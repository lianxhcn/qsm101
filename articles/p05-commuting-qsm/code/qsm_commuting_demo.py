#!/usr/bin/env python3
"""P05 两地区通勤 QSM；全部数据为教学构造。

方程映射：M[i,j] 为居住 i、工作 j 的人数；R=M.sum(1)，E=M.sum(0)。
U=ln(B)+(1-alpha)ln(c)+alpha*ln(h)-tau+epsilon，c+r*h=w。
p=softmax(theta*(ln(B_i)+ln(w_j)-alpha*ln(r_i)-tau_ij))。
Y=Z*E**beta；w=beta*Z*E**(beta-1)；r*H=alpha*(M@w)。
ln(W)=logsumexp(theta*V)/theta，tau 只影响效用，不扣货币预算。
N=120000，M0=[[54000,6000],[6000,54000]]，alpha=.25，beta=.90，theta=4。
跨区 tau=ln(9)/4，本地 tau=0；H 和 Z 从基准反演。
政策只令 H_B*=1.20，其余基本面固定。受限模型使用对角掩码独立校准。
算法：给定二维居民/就业对数比，先算工资，再算条件工作地概率，
用候选居民数及条件平均工资算租金，最后让联合选择边际等于候选边际。
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import numpy as np
import pandas as pd
from scipy.optimize import root, minimize
from scipy.special import softmax, logsumexp

SEED = 20261005
SAMPLE_SIZE = 20000
N = 120000.0
ALPHA = .25
THETA = 4.0
BETA = .90
TAU = np.log(9.) / 4.
M0 = np.array([[54000., 6000.], [6000., 54000.]])
W0 = np.array([9600., 9600.])
RENT0 = np.array([120., 120.])
REGIONS = np.array(['A', 'B'])
STARTS = [(0., 0.), (-2., -2.), (2., 2.), (-2., 2.), (2., -2.)]


def dump(path, obj):
    """保存数组、标量与版本记录，拒绝非标准 JSON 的 NaN。"""
    def convert(x):
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, np.generic):
            return x.item()
        raise TypeError(type(x).__name__)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                              default=convert, allow_nan=False), encoding='utf-8')


def csv(path, df):
    df.to_csv(path, index=False, encoding='utf-8-sig', float_format='%.16g')


def calibrate(theta=THETA, beta=BETA, tau=None, restricted=False):
    """theta 网格保持 OD 基准，tau 网格仅保持总量基准，不能同时强配 OD。"""
    if not (theta > 0 and 0 < beta <= 1):
        raise ValueError('参数越界')
    tau = np.log(9.) / theta if tau is None else float(tau)
    if tau < 0:
        raise ValueError('通勤成本必须非负')
    target = np.diag(M0.sum(1)) if restricted else M0.copy()
    R, E = target.sum(1), target.sum(0)
    H = ALPHA * (target @ W0) / RENT0
    Z = W0 * E ** (1-beta) / beta
    # 对称工资、租金、行和以及对称通勤成本意味着相对便利度为 1。
    return dict(N=N, alpha=ALPHA, beta=beta, theta=theta,
                tau=np.array([[0., tau], [tau, 0.]]), H=H, Z=Z,
                B=np.ones(2), mask=np.eye(2, dtype=bool) if restricted
                else np.ones((2, 2), dtype=bool), restricted=restricted)


def state(xy, p, H_hat=(1., 1.), Z_hat=(1., 1.)):
    """候选 R/E 下住房条件的代入，不把候选通勤矩阵当成最终均衡。"""
    R = p['N'] * softmax([0., xy[0]])
    E = p['N'] * softmax([0., xy[1]])
    H, Z = p['H'] * np.asarray(H_hat), p['Z'] * np.asarray(Z_hat)
    Y = Z * E ** p['beta']
    w = p['beta'] * Z * E ** (p['beta']-1)
    conditional_score = np.where(p['mask'], p['theta'] *
                                (np.log(w)[None, :] - p['tau']), -np.inf)
    q = softmax(conditional_score, axis=1)
    r = p['alpha'] * R * (q @ w) / H
    v = (np.log(p['B'])[:, None] + np.log(w)[None, :]
         - p['alpha'] * np.log(r)[:, None] - p['tau'])
    score = np.where(p['mask'], p['theta'] * v, -np.inf)
    prob = np.exp(score-logsumexp(score))
    M = p['N'] * prob
    residual = np.array([(M.sum(1)[1]-R[1])/p['N'],
                         (M.sum(0)[1]-E[1])/p['N']])
    return dict(R=R, E=E, w=w, r=r, M=M, p=prob, H=H, Z=Z, Y=Y,
                logW=logsumexp(score)/p['theta'], residual=residual,
                xy=np.asarray(xy))


def solve(p, H_hat=(1., 1.), Z_hat=(1., 1.)):
    """多初值二维求根；失败或残差超标就报错，禁止按预期结果调参。"""
    if np.any(np.asarray(H_hat) <= 0) or np.any(np.asarray(Z_hat) <= 0):
        raise ValueError('冲击倍率必须为正')
    solutions, attempts = [], []
    for initial in STARTS:
        fun = lambda xy: state(xy, p, H_hat, Z_hat)['residual']
        fit = root(fun, initial, method='hybr', options={'xtol': 1e-10})
        primary = dict(success=bool(fit.success), status=int(fit.status),
                       message=str(fit.message), residual=float(np.max(np.abs(fun(fit.x)))))
        if not fit.success:
            # 对称解附近 hybr 可能因舍入误差停止；备用算法仍求相同方程。
            fit = root(fun, fit.x, method='lm',
                       options={'ftol':1e-12,'xtol':1e-12,'gtol':1e-12})
        s = state(fit.x, p, H_hat, Z_hat)
        err = float(np.max(np.abs(s['residual'])))
        attempts.append(dict(initial=initial, success=bool(fit.success),
                             status=int(fit.status), message=str(fit.message),
                             nfev=int(fit.nfev), residual=err, xy=fit.x, primary_hybr=primary))
        if err > 1e-10 or not fit.success:
            raise RuntimeError(f'求根失败: {attempts[-1]}')
        solutions.append(s)
    s = solutions[0]
    s['initial_spread'] = max(float(np.max(np.abs(v['xy']-s['xy'])))
                              for v in solutions)
    if s['initial_spread'] > 1e-8:
        raise RuntimeError('初值对应不同解，需要检查')
    s['attempts'] = attempts
    return s


def teaching_table(p):
    rows = []
    for i in range(2):
        for j in range(2):
            rows.append(dict(home_region=REGIONS[i], work_region=REGIONS[j],
                commuters=M0[i,j], residents=M0.sum(1)[i],
                employment=M0.sum(0)[j], monthly_wage=W0[j],
                monthly_rent_per_m2=RENT0[i], alpha=ALPHA, beta=BETA,
                theta=THETA, tau=p['tau'][i,j], total_workers=N,
                data_origin='constructed_teaching_baseline'))
    return pd.DataFrame(rows)


def simulate(n=SAMPLE_SIZE, seed=SEED):
    """每个任务独立抽工作地工资、居住地租金、双向通勤强度，再抽选择。"""
    rng = np.random.default_rng(seed)
    log_w = np.log(9600.) + rng.uniform(-.35, .35, (n, 2))
    log_r = np.log(120.) + rng.uniform(-.4, .4, (n, 2))
    cross_time = rng.uniform(.5, 1.5, (n, 2))
    home = np.array([0, 0, 1, 1])
    work = np.array([0, 1, 0, 1])
    cost = np.zeros((n, 4))
    cost[:, [1, 2]] = cross_time
    x = log_w[:, work] - ALPHA * log_r[:, home]
    prob = softmax(THETA*x - THETA*TAU*cost, axis=1)
    u = rng.random(n)
    choice = (u[:, None] > np.cumsum(prob, axis=1)).sum(1)
    return pd.DataFrame(dict(choice_set_id=np.repeat(np.arange(n), 4),
        home_region=np.tile(REGIONS[home], n), work_region=np.tile(REGIONS[work], n),
        commute_indicator=np.tile((home != work).astype(int), n),
        commute_multiplier=cost.ravel(), log_wage=log_w[:,work].ravel(),
        log_rent=log_r[:,home].ravel(),
        chosen=(np.arange(4)[None,:] == choice[:,None]).astype(int).ravel(),
        data_origin='synthetic_choice_experiment'))


def estimate(df):
    """解析梯度与观测信息矩阵；tau 的标准误使用含协方差的 Delta 法。"""
    n = len(df)//4
    x = (df.log_wage-ALPHA*df.log_rent).to_numpy().reshape(n,4)
    d = df.commute_multiplier.to_numpy().reshape(n,4)
    X = np.stack([x, -d], axis=2)
    # 每个选择集中心化，不影响概率；有助于数值条件。
    X -= X.mean(1, keepdims=True)
    chosen = df.chosen.to_numpy().reshape(n,4)
    def fg(b):
        v = X@b
        prob = softmax(v, axis=1)
        loss = np.mean(logsumexp(v, axis=1)-(chosen*v).sum(1))
        grad = np.einsum('na,nak->k', prob-chosen, X)/n
        return loss, grad
    fit = minimize(fg, [3., 2.], jac=True, method='BFGS',
                   options={'gtol': 1e-10, 'maxiter': 1000})
    prob = softmax(X@fit.x, axis=1)
    mu = np.einsum('na,nak->nk', prob, X)
    info = (np.einsum('na,nak,nal->kl', prob, X, X)-mu.T@mu)
    cov = np.linalg.inv(info)
    theta, penalty = fit.x
    delta = np.array([-penalty/theta**2, 1/theta])
    values = np.array([theta, penalty, penalty/theta])
    se = np.r_[np.sqrt(np.diag(cov)), np.sqrt(delta@cov@delta)]
    true = np.array([THETA, THETA*TAU, TAU])
    rank = np.linalg.matrix_rank(X.reshape(-1,2))
    score = np.max(np.abs(fg(fit.x)[1]))
    if not fit.success or score > 1e-7 or theta <= 0 or penalty <= 0:
        raise RuntimeError(f'MLE 失败: {fit.message}, score={score}')
    out = pd.DataFrame(dict(parameter=['theta','theta_tau','tau'],
        true_value=true, estimate=values, iid_standard_error=se,
        ci95_low=values-1.96*se, ci95_high=values+1.96*se,
        z_from_truth=(values-true)/se, seed=SEED, choice_sets=n,
        data_origin='synthetic_choice_experiment'))
    meta = dict(success=bool(fit.success), status=int(fit.status),
                message=str(fit.message), mean_score_max=score,
                design_rank=int(rank), information_eigenvalues=np.linalg.eigvalsh(info),
                covariance=cov, seed=SEED, choice_sets=n, rows=len(df))
    return out, meta


def rel(a, b):
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b))/
                        np.maximum(np.abs(b), 1e-12)))


def checks_for(s, p):
    """用最终联合流量重新检查市场、边际和普通商品核算。"""
    M, R, E, w, r = (s[k] for k in ['M','R','E','w','r'])
    v = np.log(p['B'])[:,None]+np.log(w)[None,:]-p['alpha']*np.log(r)[:,None]-p['tau']
    prob = softmax(np.where(p['mask'],p['theta']*v,-np.inf).ravel()).reshape(2,2)
    wage_income = np.sum(M*w[None,:])
    worker_c = (1-p['alpha'])*wage_income
    landlord_c = np.sum(r*s['H'])
    factor_c = np.sum((1-p['beta'])*s['Y'])
    return dict(total_population=abs(M.sum()/p['N']-1),
        row_residents=rel(M.sum(1),R), column_employment=rel(M.sum(0),E),
        joint_choices=float(np.max(np.abs(M/p['N']-prob))),
        housing_market=rel(r*s['H'],p['alpha']*(M@w)),
        marginal_product=rel(w,p['beta']*s['Z']*E**(p['beta']-1)),
        goods_resource=abs((worker_c+landlord_c+factor_c)/s['Y'].sum()-1),
        wage_bill=rel(M.sum(0)*w,p['beta']*s['Y']),
        root_residual=float(np.max(np.abs(s['residual']))),
        initial_spread=s['initial_spread'])


def run(out, no_figures=False, sample_size=SAMPLE_SIZE):
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f'输出目录非空，请使用新的 --output：{out}')
    (out/'input').mkdir(parents=True, exist_ok=True)
    p = calibrate()
    data = simulate(sample_size)
    csv(out/'input/teaching-baseline.csv',teaching_table(p))
    csv(out/'input/synthetic-joint-choice-tasks.csv',data)
    estimates, mle = estimate(data)
    csv(out/'synthetic-estimates.csv',estimates)
    dump(out/'estimation-diagnostics.json',mle)
    states, params, baselines = {}, {}, {}
    def add(name, pa, h=(1.,1.), z=(1.,1.), base='baseline'):
        states[name], params[name], baselines[name] = solve(pa,h,z), pa, base
        return states[name]
    base = add('baseline',p)
    policy = add('B_housing_plus20',p,h=(1.,1.2))
    add('zero_shock',p)
    add('common_housing_plus20',p,h=(1.2,1.2))
    add('common_productivity_plus10',p,z=(1.1,1.1))
    restricted = calibrate(restricted=True)
    rb = add('restricted_baseline',restricted,base='restricted_baseline')
    rp = add('restricted_B_housing_plus20',restricted,h=(1.,1.2),base='restricted_baseline')
    high = calibrate(tau=20.)
    hb = add('high_tau_baseline',high,base='high_tau_baseline')
    hp = add('high_tau_B_housing_plus20',high,h=(1.,1.2),base='high_tau_baseline')
    dump(out/'calibrated-parameters.json',dict(main=p,restricted=restricted,
        main_uses='true teaching parameters, not MLE',data_origin='teaching_only'))
    sensitivity = []
    specs = [('theta',t,BETA,None) for t in [1.,2.,4.,6.,8.]]
    specs += [('beta',THETA,b,None) for b in [.8,.85,.9,.95,1.]]
    specs += [('tau',THETA,BETA,t) for t in [0.,.25,TAU,1.,2.]]
    specs += [('estimated_theta',float(estimates.iloc[0].estimate),BETA,None)]
    # 同时使用模拟估计 theta/tau 的情景只保留对称总量，不能强配四格 OD。
    specs += [('estimated_joint',float(estimates.iloc[0].estimate),BETA,float(estimates.iloc[2].estimate))]
    for k,(axis,t,b,cost) in enumerate(specs):
        pa = calibrate(t,b,cost)
        bn, sn = f'sensitivity_{k:02d}_baseline', f'sensitivity_{k:02d}_policy'
        s0 = add(bn,pa,base=bn)
        s1 = add(sn,pa,h=(1.,1.2),base=bn)
        sensitivity.append(dict(axis=axis,theta=t,beta=b,tau=pa['tau'][0,1],
            calibration_target='aggregate_only_OD_changes' if cost is not None else 'full_OD_baseline',
            baseline_OD_relative_error=rel(s0['M'],M0),
            baseline_cross_commuters=s0['M'][0,1]+s0['M'][1,0],
            residents_B_change_pct=100*(s1['R'][1]/s0['R'][1]-1),
            employment_B_change_pct=100*(s1['E'][1]/s0['E'][1]-1),
            wage_B_change_pct=100*(s1['w'][1]/s0['w'][1]-1),
            rent_B_change_pct=100*(s1['r'][1]/s0['r'][1]-1),
            welfare_change_pct=100*np.expm1(s1['logW']-s0['logW'])))
    sens = pd.DataFrame(sensitivity)
    csv(out/'sensitivity-results.csv',sens)
    rows, flows = [], []
    for name,s in states.items():
        s0=states[baselines[name]]
        for i,region in enumerate(REGIONS):
            row=dict(scenario=name,region=region,data_origin='teaching_model',
                     worker_welfare_change_pct=100*np.expm1(s['logW']-s0['logW']))
            for key,label in [('R','residents'),('E','employment'),('w','monthly_wage'),
                              ('r','monthly_rent_per_m2'),('H','housing_m2'),('Y','output')]:
                row[label]=s[key][i]
                row[label+'_change_pct']=100*(s[key][i]/s0[key][i]-1)
            rows.append(row)
            for j,work in enumerate(REGIONS):
                flows.append(dict(scenario=name,home_region=region,work_region=work,
                                  commuters=s['M'][i,j],probability=s['p'][i,j],
                                  data_origin='teaching_model'))
    results=pd.DataFrame(rows)
    csv(out/'equilibrium-results.csv',results)
    csv(out/'commuting-matrix-results.csv',pd.DataFrame(flows))
    checks={}
    def check(name,error,tol=1e-8):
        checks[name]=dict(error=float(error),threshold=tol,passed=bool(np.isfinite(error) and error<=tol))
    for name,s in states.items():
        for metric,error in checks_for(s,params[name]).items():
            check(name+'/'+metric,error)
    for key,target in [('M',M0),('R',M0.sum(1)),('E',M0.sum(0)),('w',W0),('r',RENT0)]:
        check('baseline_restore/'+key,rel(base[key],target))
        check('zero_shock/'+key,rel(states['zero_shock'][key],base[key]))
    for name,ws,rs,welf in [('common_housing_plus20',1.,1/1.2,1.2**ALPHA),
                          ('common_productivity_plus10',1.1,1.1,1.1**(1-ALPHA))]:
        s=states[name]
        for key,target in [('M',base['M']),('w',base['w']*ws),('r',base['r']*rs)]:
            check(name+'/scaling_'+key,rel(s[key],target))
        check(name+'/welfare_scaling',abs(np.exp(s['logW']-base['logW'])/welf-1))
    swapped=copy.deepcopy(p)
    for k in ['H','Z','B']: swapped[k]=p[k][::-1].copy()
    for k in ['tau','mask']: swapped[k]=p[k][::-1,::-1].copy()
    mirror=solve(swapped,(1.2,1.))
    for key in ['R','E','w','r','M']:
        target=policy[key][::-1,::-1] if key=='M' else policy[key][::-1]
        check('label_mirror/'+key,rel(mirror[key],target))
    check('label_mirror/welfare',abs(mirror['logW']-policy['logW']))
    for name in ['restricted_baseline','restricted_B_housing_plus20']:
        check(name+'/cross_exact_zero',abs(states[name]['M'][0,1])+abs(states[name]['M'][1,0]),0.)
    for key,target in [('R',M0.sum(1)),('E',M0.sum(0)),('w',W0),('r',RENT0)]:
        check('restricted_restore/'+key,rel(rb[key],target))
    for key in ['R','E','w','r']:
        check('high_tau_limit/'+key,rel(hp[key],rp[key]))
    check('high_tau_limit/cross_share',(hp['M'][0,1]+hp['M'][1,0])/N,1e-12)
    check('high_tau_limit/welfare_gain',abs((hp['logW']-hb['logW'])-(rp['logW']-rb['logW'])))
    # 受限模型的一维解析式另作检查，独立于二维数值算法。
    analytical = THETA*ALPHA*np.log(1.2)/(1+THETA*(ALPHA+(1-ALPHA)*(1-BETA)))
    check('restricted_analytical',abs(rp['xy'][0]-analytical))
    check('mle/score',mle['mean_score_max'],1e-7)
    check('mle/design_rank',abs(mle['design_rank']-2),0.)
    for _,row in estimates.iterrows():
        check('mle/recovery_'+row.parameter,abs(row.z_from_truth),4.)
    check('data/one_choice_per_set',float(np.max(np.abs(data.groupby('choice_set_id').chosen.sum()-1))),0.)
    for row in sensitivity:
        if row['calibration_target']=='full_OD_baseline':
            check('sensitivity_OD/'+row['axis']+str(row['theta'])+str(row['beta']),row['baseline_OD_relative_error'])
    verification=dict(all_passed=all(v['passed'] for v in checks.values()),checks=checks,
        seed=SEED,choice_sets=sample_size,data_origin='teaching_and_synthetic_only',
        versions={k:importlib.metadata.version(k) for k in ['numpy','scipy','pandas','matplotlib']},
        python=platform.python_version(),timestamp=datetime.now().isoformat(),
        input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'input').glob('*.csv')})
    dump(out/'verification.json',verification)
    dump(out/'solver-diagnostics.json',{name:s['attempts'] for name,s in states.items()})
    if not verification['all_passed']:
        raise RuntimeError('核验失败: '+str({k:v for k,v in checks.items() if not v['passed']}))
    if not no_figures:
        draw(out,states,sens)
    print(estimates.to_string(index=False))
    print(results[results.scenario.isin(['baseline','B_housing_plus20','restricted_B_housing_plus20'])].to_string(index=False))
    print(f'PASS: {len(checks)} checks; output={out}')


def draw(out,states,sens):
    """每图一问；所有坐标明确单位，PNG 为 1100 px，另存矢量图。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fonts={f.name for f in font_manager.fontManager.ttflist}
    font=next((f for f in ['Microsoft YaHei','Noto Sans CJK SC','SimHei'] if f in fonts),None)
    if font is None:
        raise RuntimeError('未找到中文字体，可先用 --no-figures 验证数值')
    plt.rcParams.update({'font.family':font,'font.size':12,'axes.unicode_minus':False,
                         'svg.fonttype':'path','pdf.fonttype':42})
    folder=out/'figures'; folder.mkdir()
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    manifest=[]
    def save(fig,num,name,caption):
        stem=f'p05-commuting-fig{num:02d}-{name}-{stamp}'
        fig.text(.5,.02,'教学构造数据与模型计算；不对应真实城市',ha='center',fontsize=10,color='#555555')
        for ext in ['png','svg','pdf']:
            fig.savefig(folder/f'{stem}.{ext}',dpi=100)
        plt.close(fig)
        manifest.append(dict(stem=stem,caption=caption,font=font))
    fig,ax=plt.subplots(figsize=(11,5.5))
    ax.axis('off')
    table=ax.table(cellText=[['住 A','54,000','6,000','60,000'],['住 B','6,000','54,000','60,000'],
                            ['就业合计','60,000','60,000','120,000']],
                   colLabels=['居住地 / 工作地','在 A 工作','在 B 工作','居民合计'],
                   cellLoc='center',loc='center',bbox=[.04,.18,.92,.65])
    table.auto_set_font_size(False); table.set_fontsize(16)
    for (i,j),cell in table.get_celld().items():
        cell.set_edgecolor('white')
        cell.set_facecolor('#dcebf3' if i==0 or j==0 else '#f0f4f6')
    ax.set_title('通勤矩阵的行是居民数，列是就业数',fontsize=19,pad=15)
    save(fig,1,'baseline-flow','基准通勤矩阵与居民、就业边际量')
    fig,axes=plt.subplots(1,2,figsize=(11,5.8),gridspec_kw={'width_ratios':[1.4,1]})
    base=states['baseline']; policy=states['B_housing_plus20']; rp=states['restricted_B_housing_plus20']; rb=states['restricted_baseline']
    labels=['A 居民','B 居民','A 就业','B 就业','A 工资','B 工资','A 租金','B 租金']
    ys=np.arange(8)
    for offset,s,s0,label,color in [(-.18,policy,base,'允许通勤','#276b8e'),(.18,rp,rb,'仅本地工作','#cc713d')]:
        vals=np.concatenate([100*(s[k]/s0[k]-1) for k in ['R','E','w','r']])
        axes[0].barh(ys+offset,vals,height=.33,label=label,color=color)
    axes[0].set_yticks(ys,labels);axes[0].invert_yaxis();axes[0].axvline(0,color='gray',lw=.8)
    axes[0].set_xlabel('相对各自基准的变化 (%)');axes[0].legend(fontsize=10,loc='upper left',bbox_to_anchor=(0,1.09),ncol=2,frameon=False)
    # 受限模型跨区流量为零：用文字说明，避免不可见柱形对应多余图例。
    for offset,s,label,color in [(-.12,base,'允许通勤：基准','#9ebed0'),(.12,policy,'允许通勤：政策后','#276b8e')]:
        axes[1].bar(np.arange(2)+offset,[s['M'][0,1],s['M'][1,0]],width=.24,label=label,color=color)
    axes[1].text(.5,.82,'仅本地工作：两方向均为 0 人',
                 transform=axes[1].transAxes,ha='center',fontsize=10,color='#555555')
    axes[1].set_xticks([0,1],['住 A → 工作 B','住 B → 工作 A']);axes[1].set_ylabel('跨区通勤人数 (人)')
    axes[1].legend(fontsize=9,loc='upper center',bbox_to_anchor=(.5,1.02));axes[1].set_ylim(0,8500)
    fig.suptitle('B 地区住房增加 20%：居住与就业如何分开调整',fontsize=18)
    fig.subplots_adjust(left=.10,right=.97,bottom=.16,top=.87,wspace=.36)
    save(fig,2,'policy-compare','允许通勤与受限通勤的住房政策比较')
    fig,axes=plt.subplots(1,3,figsize=(11,4.8))
    for ax,axis,label in zip(axes,['theta','beta','tau'],['选择敏感度 θ','劳动产出弹性 β','跨区效用成本 τ']):
        sub=sens[sens.axis==axis]
        ax.plot(sub[axis],sub.residents_B_change_pct,'o-',label='B 居民',color='#276b8e')
        ax.plot(sub[axis],sub.employment_B_change_pct,'s--',label='B 就业',color='#cc713d')
        ax.set_xlabel(label);ax.grid(alpha=.2);ax.set_ylim(0,7)
    axes[0].set_ylabel('住房政策带来的增长 (%)');axes[0].legend()
    fig.suptitle('行为参数改变时，B 居民与就业的政策响应',fontsize=18)
    fig.text(.5,.10,'θ、β：重新匹配完整 OD 基准；τ：匹配总量，基准通勤份额允许改变',ha='center',fontsize=10)
    fig.subplots_adjust(left=.07,right=.98,bottom=.25,top=.85,wspace=.26)
    save(fig,3,'sensitivity','参数敏感性；不是置信区间')
    dump(out/'figure-manifest.json',manifest)


if __name__=='__main__':
    if sys.stdout.encoding and sys.stdout.encoding.lower()!='utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('runs/p05-first-run'))
    parser.add_argument('--no-figures',action='store_true')
    parser.add_argument('--sample-size',type=int,default=SAMPLE_SIZE)
    args=parser.parse_args()
    if args.sample_size<1000: parser.error('模拟恢复检查要求至少 1000 个任务')
    run(args.output,args.no_figures,args.sample_size)
