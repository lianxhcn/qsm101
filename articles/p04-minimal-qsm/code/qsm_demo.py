#!/usr/bin/env python3
"""P04: 两地区 QSM 的参数估计、校准、均衡和住房政策演示。

数据均为教学构造。估计样本是随机生成的假想选址任务，未读取真实调查。
运行: python qsm_demo.py
自定义输出目录: python qsm_demo.py --output my-run
依赖: numpy, scipy, pandas, matplotlib (不调用大模型 API)。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize
from scipy.special import expit, logsumexp

STAMP = "20261004-2330"
SEED = 20261004
ALPHA = 0.25                    # 住房支出占工资收入的比例: 教学设定
BETA = 0.90                     # 生产函数劳动弹性: 教学设定
N0 = np.array([60000.0, 40000.0])
W0 = np.array([10000.0, 8000.0])  # 元 / 工人 / 月
R0 = np.array([100.0, 80.0])      # 元 / 平方米 / 月, 同质住房服务


def simulate_choice_data(n=8000, seed=SEED):
    """生成假想的二选一任务; 随机属性使估计程序可以恢复已知参数。"""
    rng = np.random.default_rng(seed)
    dw = rng.uniform(-0.35, 0.35, n)   # log(w_B / w_A)
    dr = rng.uniform(-0.40, 0.40, n)   # log(r_B / r_A)
    # 0.12 为任务中的 B 选项截距, 与两地区基准便利度的反演分开处理。
    prob = expit(0.12 + 4.0 * (dw - ALPHA * dr))
    return pd.DataFrame({
        "ln_wage_ratio": dw,
        "ln_rent_ratio": dr,
        "choose_B": rng.binomial(1, prob),
    })


def estimate_theta(data, alpha=ALPHA):
    """在 alpha 已知时, 用二元 Logit 极大似然估计截距和 theta。"""
    x = data["ln_wage_ratio"].to_numpy() - alpha * data["ln_rent_ratio"].to_numpy()
    X = np.column_stack([np.ones(len(x)), x])
    y = data["choose_B"].to_numpy()

    # logaddexp 避免 exp 溢出; 平均负对数似然改善数值尺度。
    def objective(coef):
        linear = X @ coef
        return np.mean(np.logaddexp(0.0, linear) - y * linear)

    def gradient(coef):
        return X.T @ (expit(X @ coef) - y) / len(y)

    fit = minimize(objective, [0.0, 3.0], jac=gradient, method="L-BFGS-B",
                   bounds=[(None, None), (0.01, 20.0)],
                   options={"ftol": 1e-14, "gtol": 1e-10, "maxiter": 1000})
    score = np.max(np.abs(gradient(fit.x)))
    if not fit.success or score > 1e-7 or not 0.011 < fit.x[1] < 19.99:
        raise RuntimeError(f"MLE 未通过检查: {fit.message}; score={score}")
    p = expit(X @ fit.x)
    information = X.T @ ((p * (1.0 - p))[:, None] * X)
    se = np.sqrt(np.diag(np.linalg.inv(information)))
    estimates = pd.DataFrame({
        "parameter": ["task_intercept", "theta"],
        "true_simulation_value": [0.12, 4.0],
        "estimate": fit.x,
        "iid_standard_error": se,
        "ci95_low": fit.x - 1.96 * se,
        "ci95_high": fit.x + 1.96 * se,
        "data_origin": "synthetic_choice_tasks",
    })
    return float(fit.x[1]), estimates, float(score)


def calibrate(theta, alpha=ALPHA, beta=BETA):
    """固定行为参数后, 从基准人口、工资、租金反演 H、Z 和相对便利度 B。"""
    if not (theta > 0 and 0 < alpha < 1 and 0 < beta <= 1):
        raise ValueError("参数范围不符合本模型")
    # H 为有效住房服务存量; 并非独立观测到的真实建筑面积。
    H = alpha * W0 * N0 / R0
    Z = W0 * N0 ** (1.0 - beta) / beta
    log_B = np.log(N0 / N0.sum()) / theta - np.log(W0) + alpha * np.log(R0)
    log_B -= log_B[0]              # 只识别相对便利度: B_A = 1
    return {"alpha": alpha, "beta": beta, "theta": theta,
            "H": H, "Z": Z, "B": np.exp(log_B)}


def prices_and_choices(log_odds, params, H_hat, Z_hat):
    """给定 log(N_B/N_A), 计算工资、租金以及居民希望选择的份额。"""
    s_B = expit(log_odds)
    N = N0.sum() * np.array([1.0 - s_B, s_B])
    w = W0 * Z_hat * (N / N0) ** (params["beta"] - 1.0)
    H = params["H"] * H_hat
    r = params["alpha"] * w * N / H
    log_v = np.log(params["B"]) + np.log(w) - params["alpha"] * np.log(r)
    scores = params["theta"] * log_v
    desired_shares = np.exp(scores - logsumexp(scores))
    log_welfare_index = logsumexp(scores) / params["theta"]
    return N, w, r, H, desired_shares, log_welfare_index


def solve(params, H_hat=(1.0, 1.0), Z_hat=(1.0, 1.0)):
    """用一维有界求根获得均衡; 不把程序的收敛消息当作经济验证。"""
    H_hat, Z_hat = np.asarray(H_hat, float), np.asarray(Z_hat, float)
    if np.any(H_hat <= 0) or np.any(Z_hat <= 0):
        raise ValueError("政策倍率必须为正")

    def residual(log_odds):
        N, w, r, H, shares, log_V = prices_and_choices(log_odds, params, H_hat, Z_hat)
        # 实际人口比的对数 = 居民选择概率比的对数。
        log_v = np.log(params["B"]) + np.log(w) - params["alpha"] * np.log(r)
        return log_odds - params["theta"] * (log_v[1] - log_v[0])

    root = brentq(residual, -30.0, 30.0, xtol=1e-12)
    N, w, r, H, shares, log_V = prices_and_choices(root, params, H_hat, Z_hat)
    theta, alpha, beta = params["theta"], params["alpha"], params["beta"]
    denominator = 1.0 + theta * (alpha + (1.0 - alpha) * (1.0 - beta))
    # 本特例有解析解, 可独立核验数值求根; 无集聚外部性时残差严格递增。
    analytical_root = np.log(N0[1] / N0[0]) + theta / denominator * (
        alpha * np.log(H_hat[1] / H_hat[0])
        + (1.0 - alpha) * np.log(Z_hat[1] / Z_hat[0]))
    Y = params["Z"] * Z_hat * N ** beta
    checks = {
        "population_total_error": float(abs(N.sum() - N0.sum())),
        "location_choice_error": float(np.max(np.abs(N / N.sum() - shares))),
        "housing_market_relative_error": float(np.max(np.abs(alpha * w * N / r / H - 1.0))),
        "wage_marginal_product_relative_error": float(np.max(np.abs(w / (beta * Y / N) - 1.0))),
        "analytical_log_odds_error": float(abs(root - analytical_root)),
        "root_residual": float(abs(residual(root))),
    }
    if max(checks.values()) > 1e-8:
        raise RuntimeError(f"均衡核验失败: {checks}")
    return {"N": N, "w": w, "r": r, "H": H, "Y": Y,
            "log_welfare_index": float(log_V), "checks": checks}


def report_rows(scenario, state, baseline):
    rows = []
    for i, region in enumerate(["A", "B"]):
        row = {"scenario": scenario, "region": region}
        for key, name in [("N", "workers"), ("w", "monthly_wage"),
                          ("r", "monthly_rent_per_m2"), ("H", "effective_housing_m2")]:
            row[name] = float(state[key][i])
            row[name + "_change_pct"] = float((state[key][i] / baseline[key][i] - 1.0) * 100)
        row["worker_ex_ante_welfare_change_pct"] = float(
            np.expm1(state["log_welfare_index"] - baseline["log_welfare_index"]) * 100)
        rows.append(row)
    return rows


def configure_fonts():
    # 在 Linux 和 Windows 上选择可用中文字体; SVG 与 PDF 保留实际矢量图形。
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((f for f in ["Noto Sans CJK SC", "Microsoft YaHei", "SimHei"] if f in available), None)
    if chosen is None:
        raise RuntimeError("未找到中文字体; 请安装 Noto Sans CJK SC 或微软雅黑后重试")
    plt.rcParams.update({"font.family": chosen, "font.size": 14,
                         "axes.unicode_minus": False, "svg.fonttype": "path"})


def export_figures(out, results, sensitivity, theta):
    configure_fonts()
    fig_dir = out / "fig"
    fig_dir.mkdir(exist_ok=True)
    colors = {"A": "#2C7A89", "B": "#C56B3E"}
    chosen = results[results.scenario == "B_housing_plus20_GE"].set_index("region")
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=100)
    labels = ["劳动人口", "月工资", "每平方米月租金"]
    y = np.arange(3)
    for j, region in enumerate(["A", "B"]):
        values = chosen.loc[region, ["workers_change_pct", "monthly_wage_change_pct",
                                     "monthly_rent_per_m2_change_pct"]].to_numpy(float)
        ax.barh(y + (j - 0.5) * 0.32, values, height=0.29,
                label=f"{region} 地区", color=colors[region])
        for yi, val in zip(y + (j - 0.5) * 0.32, values):
            ax.text(val + (0.25 if val >= 0 else -0.25), yi, f"{val:+.2f}%",
                    va="center", ha="left" if val >= 0 else "right", fontsize=13)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.axvline(0, color="#4A4A4A", linewidth=1)
    ax.set_xlim(-17, 8)
    ax.set_xlabel("相对于基准均衡的变化 (%)")
    fig.text(0.04, 0.945, "B 地区住房增加 20% 后的空间均衡", fontsize=18, va="top")
    ax.legend(loc="lower left", ncol=2, frameon=False, bbox_to_anchor=(0, 1.025))
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ax.grid(axis="x", color="#E5E5E5", linewidth=0.7)
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.23, right=0.97, top=0.79, bottom=0.19)
    fig.text(0.04, 0.035, "教学构造数据 | 总劳动人口固定为 10 万 | 工资与租金同时调整", fontsize=12, color="#525252")
    for ext in ["png", "svg", "pdf"]:
        fig.savefig(fig_dir / f"qsm-housing-equilibrium-{STAMP}.{ext}", dpi=100)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=100)
    for beta, style in [(0.8, "--"), (0.9, "-"), (1.0, ":")]:
        df = sensitivity[np.isclose(sensitivity.beta, beta)].sort_values("theta")
        ax.plot(df.theta, df.B_workers_change_pct, color="#2C7A89",
                linestyle=style, linewidth=2.5, label=f"劳动产出弹性 β = {beta:.1f}")
    main = sensitivity[(np.isclose(sensitivity.beta, BETA)) & (np.isclose(sensitivity.theta, theta))].iloc[0]
    ax.scatter([theta], [main.B_workers_change_pct], color="#C56B3E", zorder=4, s=65)
    ax.annotate(f"本次估计 θ = {theta:.3f}", (theta, main.B_workers_change_pct),
                xytext=(theta + 0.8, main.B_workers_change_pct + 0.4), fontsize=13)
    ax.set(xlabel="区位选择敏感度 θ", ylabel="B 地区劳动人口增幅 (%)", xlim=(0, 9), ylim=(0, 9))
    ax.set_title("同一住房政策在不同参数下的预测", loc="left", pad=16)
    ax.legend(frameon=False, fontsize=12, loc="upper left")
    ax.grid(color="#E5E5E5", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(left=0.12, right=0.96, top=0.84, bottom=0.2)
    fig.text(0.04, 0.035, "B 地区住房增加 20% | α = 0.25 | 各组参数均重新校准到同一基准", fontsize=12, color="#525252")
    for ext in ["png", "svg", "pdf"]:
        fig.savefig(fig_dir / f"qsm-housing-sensitivity-{STAMP}.{ext}", dpi=100)
    plt.close(fig)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "demo-output")
    parser.add_argument("--no-figures", action="store_true", help="只计算表格, 可在缺少中文字体时运行")
    args = parser.parse_args()
    out = args.output.resolve()
    # 整个入口专用于教学样本。真实数据应走独立入口, 不会被此处静默替换。
    out.mkdir(parents=True, exist_ok=True)
    input_dir = out / "input"
    input_dir.mkdir(exist_ok=True)
    data = simulate_choice_data()
    data.to_csv(input_dir / "synthetic-choice-tasks.csv", index=False)
    pd.DataFrame({"region": ["A", "B"], "workers": N0,
                  "monthly_wage": W0, "monthly_rent_per_m2": R0,
                  "origin": "teaching_assumption"}).to_csv(input_dir / "teaching-baseline.csv", index=False)
    theta, estimates, score = estimate_theta(data)
    estimates.to_csv(out / "synthetic-estimates.csv", index=False)
    params = calibrate(theta)
    baseline = solve(params)
    housing = solve(params, H_hat=(1.0, 1.2))
    zero = solve(params, H_hat=(1.0, 1.0))
    rows = report_rows("baseline", baseline, baseline) + report_rows("B_housing_plus20_GE", housing, baseline)
    # 只把工资固定, 先按原人口计算新房租, 再预测选址; 此计算未满足全部市场出清。
    r_fixed = R0 / np.array([1.0, 1.2])
    scores = theta * (np.log(params["B"]) + np.log(W0) - ALPHA * np.log(r_fixed))
    fixed_shares = np.exp(scores - logsumexp(scores))
    partial = {"N": N0.sum() * fixed_shares, "w": W0, "r": r_fixed,
               "H": params["H"] * [1.0, 1.2], "log_welfare_index": float(logsumexp(scores) / theta)}
    rows += report_rows("fixed_price_choice_prediction_NOT_GE", partial, baseline)
    results = pd.DataFrame(rows)
    results.to_csv(out / "equilibrium-results.csv", index=False)

    sensitivity_rows = []
    grid = np.unique(np.append(np.linspace(0.5, 8.0, 31), theta))
    for beta in [0.8, 0.9, 1.0]:
        for t in grid:
            p = calibrate(float(t), beta=beta)
            b = solve(p)
            cf = solve(p, H_hat=(1.0, 1.2))
            sensitivity_rows.append({"theta": float(t), "alpha": ALPHA, "beta": beta,
                                     "B_workers_change_pct": float((cf["N"][1] / N0[1] - 1) * 100),
                                     "B_rent_change_pct": float((cf["r"][1] / R0[1] - 1) * 100),
                                     "worker_ex_ante_welfare_change_pct": float(np.expm1(
                                         cf["log_welfare_index"] - b["log_welfare_index"]) * 100)})
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(out / "sensitivity-results.csv", index=False)

    baseline_error = max(float(np.max(np.abs(baseline[k] / v - 1)))
                         for k, v in [("N", N0), ("w", W0), ("r", R0)])
    zero_error = max(float(np.max(np.abs(zero[k] - baseline[k]))) for k in ["N", "w", "r"])
    if baseline_error > 1e-8 or zero_error > 1e-8:
        raise RuntimeError("基准复原或零冲击检查失败")
    properties = {}
    # 用共同冲击的经济性质核验, 避免检查仅仅重复求解器内部计算。
    for name, H_hat, Z_hat, wage_scale, rent_scale, welfare_scale in [
        ("common_housing", (1.2, 1.2), (1.0, 1.0), 1.0, 1 / 1.2, 1.2 ** ALPHA),
        ("common_productivity", (1.0, 1.0), (1.1, 1.1), 1.1, 1.1, 1.1 ** (1 - ALPHA)),
    ]:
        new = solve(params, H_hat=H_hat, Z_hat=Z_hat)
        np.testing.assert_allclose(new["N"], baseline["N"], rtol=1e-10)
        np.testing.assert_allclose(new["w"], baseline["w"] * wage_scale, rtol=1e-10)
        np.testing.assert_allclose(new["r"], baseline["r"] * rent_scale, rtol=1e-10)
        ratio = float(np.exp(new["log_welfare_index"] - baseline["log_welfare_index"]))
        np.testing.assert_allclose(ratio, welfare_scale, rtol=1e-10)
        properties[name] = {"checks_passed": True, "expected_welfare_ratio": welfare_scale,
                            "observed_welfare_ratio": ratio}
    calibrated = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in params.items()}
    write_json(out / "calibrated-parameters.json", calibrated)
    checks = {"seed": SEED, "data_origin": "teaching_and_synthetic_only",
              "baseline_relative_error": baseline_error, "zero_shock_error": zero_error,
              "mle_mean_score_max_abs": score, "baseline": baseline["checks"],
              "counterfactual": housing["checks"],
              "estimation_sample_size": len(data),
              "independent_properties": properties,
              "versions": {p: importlib.metadata.version(p) for p in ["numpy", "scipy", "pandas", "matplotlib"]},
              "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(input_dir.glob("*.csv"))}}
    write_json(out / "verification.json", checks)
    if not args.no_figures:
        export_figures(out, results, sensitivity, theta)
    print(estimates.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    print(results[["scenario", "region", "workers", "monthly_wage", "monthly_rent_per_m2",
                   "worker_ex_ante_welfare_change_pct"]].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"均衡检查通过; 基准相对误差 = {baseline_error:.3e}")
    print(f"输出目录: {out}")


if __name__ == "__main__":
    main()
