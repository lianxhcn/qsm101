#!/usr/bin/env python3
"""P06 两地区通勤 QSM。所有输入、参数与结果均为教学构造。

算法：固定输入 -> 重算 OD -> 反演基本面 -> 二维对数比求解 ->
固定基本面降低 tau -> 市场核验、极端检验及逐组重校准敏感性。
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.optimize import root
from scipy.special import softmax, logsumexp

TAU0 = np.log(9.) / 4.
STARTS = [(0., 0.), (-2., -2.), (2., 2.), (-2., 2.), (2., -2.)]
REGIONS = ['A', 'B']
NATURE = '教学构造；非真实城市或交通项目评估'

def dump(path, obj):
    """用 UTF-8 保存可审计 JSON，不允许非标准 NaN。"""
    def convert(v):
        if isinstance(v, np.ndarray): return v.tolist()
        if isinstance(v, np.generic): return v.item()
        raise TypeError(str(type(v)))
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                   default=convert, allow_nan=False), encoding='utf-8')

def save_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False, encoding='utf-8-sig', float_format='%.17g')

def relative(a, b):
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b))/np.maximum(np.abs(b), 1.)))

def read_inputs(data):
    """严格检查标签与四格方向，绝不从显示表的圆整数读取。"""
    names = ['teaching-central-residential-primitives.csv', 'teaching-central-residential-od.csv']
    hashes = {name: hashlib.sha256((data/name).read_bytes()).hexdigest() for name in names}
    df = pd.read_csv(data/names[0]).set_index('region').loc[REGIONS]
    od = pd.read_csv(data/names[1])
    if len(df) != 2 or len(od) != 4 or od.duplicated(['home_region','work_region']).any():
        raise ValueError('需要两个地区和四个不重复的 OD 单元')
    M = od.pivot(index='home_region', columns='work_region', values='workers').loc[REGIONS, REGIONS].to_numpy()
    arr = df[['residents','monthly_wage','monthly_rent_per_m2']].to_numpy()
    if not np.isfinite(arr).all() or (arr <= 0).any() or not np.isfinite(M).all() or (M <= 0).any():
        raise ValueError('固定输入必须是有限正数')
    return arr[:,0], arr[:,1], arr[:,2], M, hashes

def calibrate(R, w, r, theta=4., beta=.9, tau=TAU0):
    """给定原始 R/w/r/tau。theta 改变后重建 OD，不强行匹配旧 OD。"""
    if theta <= 0 or not 0 < beta <= 1 or tau < 0:
        raise ValueError('theta>0，0<beta<=1，tau>=0')
    R, w, r = map(lambda x: np.asarray(x, dtype=float), (R,w,r))
    alpha = .25
    cost = np.array([[0.,tau],[tau,0.]])
    scores = theta*(np.log(w)[None,:]-cost)
    q = softmax(scores, axis=1)
    M = R[:,None]*q
    E = M.sum(0)
    H = alpha*(M@w)/r
    Z = w*E**(1-beta)/beta
    inclusive = logsumexp(scores, axis=1)
    logB = (np.log(R/R[0])+alpha*theta*np.log(r/r[0])-(inclusive-inclusive[0]))/theta
    p = dict(N=float(R.sum()), alpha=alpha, beta=beta, theta=theta,
             H=H, Z=Z, B=np.exp(logB), tau=cost)
    target = dict(R=R,E=E,w=w,r=r,M=M,H=H,Z=Z,B=p['B'])
    return p, target

def state(xy, p, restricted=False):
    """以候选 R/E 构造价格，再重算联合流量和对数边际比残差。"""
    R = p['N']*softmax([0.,xy[0]])
    E = p['N']*softmax([0.,xy[1]])
    w = p['beta']*p['Z']*E**(p['beta']-1)
    mask = np.eye(2,dtype=bool) if restricted else np.ones((2,2),dtype=bool)
    score = np.where(mask,p['theta']*(np.log(w)[None,:]-p['tau']),-np.inf)
    q = softmax(score,axis=1)
    r = p['alpha']*R*(q@w)/p['H']
    v = np.log(p['B'])[:,None]+np.log(w)[None,:]-p['alpha']*np.log(r)[:,None]-p['tau']
    joint_score = np.where(mask,p['theta']*v,-np.inf)
    prob = np.exp(joint_score-logsumexp(joint_score))
    M = p['N']*prob
    rows, cols = M.sum(1), M.sum(0)
    residual = np.log([rows[1]/rows[0],cols[1]/cols[0]])-xy
    return dict(R=R,E=E,w=w,r=r,M=M,prob=prob,logW=logsumexp(joint_score)/p['theta'],
                residual=residual,xy=np.asarray(xy),Y=p['Z']*E**p['beta'])

def solve(p, start=(0.,0.), diagnostics=None, name='', restricted=False):
    """记录所有算法状态；最终验收还须检查经济方程。"""
    for method in ['hybr','lm']:
        sol = root(lambda xy: state(xy,p,restricted)['residual'],start,method=method,tol=1e-11)
        s = state(sol.x,p,restricted)
        err = float(np.max(np.abs(s['residual'])))
        if diagnostics is not None:
            diagnostics.append(dict(scenario=name,method=method,start=list(start),success=bool(sol.success),
                                    message=str(sol.message),nfev=int(sol.nfev),max_residual=err,solution=sol.x.tolist()))
        if err <= 1e-10: return s
    raise RuntimeError(f'{name}: 二维残差 {err} 未通过；不生成政策结论')

def changed(p, fraction):
    """只改变 tau，深拷贝以避免污染基准基本面。"""
    out = copy.deepcopy(p)
    out['tau'] *= 1-fraction
    return out

def summary(s, baseline):
    M=s['M']
    return dict(cross_workers=float(M[0,1]+M[1,0]), cross_share=float((M[0,1]+M[1,0])/M.sum()),
                net_B_to_A=float(M[1,0]-M[0,1]), welfare_pct=float(100*np.expm1(s['logW']-baseline['logW'])))

def checks_for(s,p,name,checks):
    """用最终联合流量检查市场，不以候选租金公式自证出清。"""
    M=s['M']; rows=M.sum(1); cols=M.sum(0)
    def check(key,error,tol=1e-8):
        checks.append(dict(scenario=name,test=key,error=float(error),threshold=tol,passed=bool(error<=tol)))
    check('total_population',abs(M.sum()/p['N']-1))
    check('row_residents',relative(rows,s['R']))
    check('column_employment',relative(cols,s['E']))
    check('wage_marginal_product',relative(s['w'],p['beta']*p['Z']*cols**(p['beta']-1)))
    check('housing_clearing',relative(s['r']*p['H'],p['alpha']*(M@s['w'])))
    v=np.log(p['B'])[:,None]+np.log(s['w'])[None,:]-p['alpha']*np.log(s['r'])[:,None]-p['tau']
    check('joint_choice',relative(M,p['N']*softmax(p['theta']*v)))
    income=float((M@s['w']).sum())
    consumption=(1-p['alpha'])*income+float((s['r']*p['H']).sum())+(1-p['beta'])*s['Y'].sum()
    check('goods_resource',abs(consumption/s['Y'].sum()-1))
    check('log_ratio_residual',np.max(np.abs(s['residual'])))

def run(data,output):
    """完整运行：输入审计、主政策、控制情景和敏感性，不覆盖既有输出。"""
    data,output=Path(data),Path(output)
    if output.exists() and any(output.iterdir()): raise FileExistsError(f'输出非空：{output}')
    output.mkdir(parents=True,exist_ok=True)
    R,w,r,M_input,hashes=read_inputs(data)
    p,target=calibrate(R,w,r)
    diagnostics=[]; checks=[]
    def check(name,error,tol=1e-8):
        checks.append(dict(scenario='special',test=name,error=float(error),threshold=tol,passed=bool(error<=tol)))
    check('fixed_od_recomputed',relative(target['M'],M_input))
    b=solve(p,diagnostics=diagnostics,name='baseline')
    p1=changed(p,.25); s=solve(p1,diagnostics=diagnostics,name='policy25')
    for key in ['M','R','E','w','r']: check('baseline_'+key,relative(b[key],target[key]))
    expected={'H':[885169.7232957717,1497141.2594953028],
              'Z':[33464.6835987020,27311.6609829235], 'B':[1.,1.16855646176227]}
    for key,val in expected.items(): check('calibration_'+key,relative(p[key],val))
    for key in ['N','alpha','theta','beta','H','Z','B']: check('policy_fixed_'+key,relative(p[key],p1[key]))
    zero=solve(changed(p,0),diagnostics=diagnostics,name='zero_shock')
    for key in ['R','E','w','r','M']: check('zero_'+key,relative(zero[key],b[key]))
    # 固定工资、租金，仅重新分配联合概率；这是局部选择预测。
    v=np.log(p['B'])[:,None]+np.log(w)[None,:]-p['alpha']*np.log(r)[:,None]-p1['tau']
    fixed_M=p['N']*softmax(p['theta']*v)
    fixed=dict(M=fixed_M,R=fixed_M.sum(1),E=fixed_M.sum(0),w=w,r=r,
               logW=logsumexp(p['theta']*v)/p['theta'])
    # 对称情形下，双向通勤增加但地区总量及价格不变。
    sym,st=calibrate([60000,60000],[9600,9600],[120,120])
    sb=solve(sym,diagnostics=diagnostics,name='symmetric_baseline')
    sp=changed(sym,.25); ss=solve(sp,diagnostics=diagnostics,name='symmetric_policy')
    for key in ['R','E','w','r']: check('symmetric_'+key,relative(ss[key],st[key]))
    check('symmetric_cross_increase',0. if ss['M'][0,1]>sb['M'][0,1] and ss['M'][1,0]>sb['M'][1,0] else 1.)
    high=copy.deepcopy(p); high['tau']=np.array([[0.,20.],[20.,0.]])
    hs=solve(high,diagnostics=diagnostics,name='tau20')
    local=solve(p,diagnostics=diagnostics,name='local_only',restricted=True)
    check('tau20_cross_share',summary(hs,b)['cross_share'],1e-12)
    for key in ['R','E','w','r','M']: check('tau20_local_'+key,relative(hs[key],local[key]))
    free=copy.deepcopy(p); free['tau']=np.zeros((2,2))
    fs=solve(free,diagnostics=diagnostics,name='tau0')
    check('tau0_separability',np.max(np.abs(fs['prob']-np.outer(fs['prob'].sum(1),fs['prob'].sum(0)))))
    mirror=copy.deepcopy(p1)
    for key in ['H','Z','B']: mirror[key]=mirror[key][::-1]
    mirror['tau']=mirror['tau'][::-1,::-1]
    ms=solve(mirror,diagnostics=diagnostics,name='labels_swapped')
    for key in ['R','E','w','r']: check('mirror_'+key,relative(ms[key],s[key][::-1]))
    check('mirror_M',relative(ms['M'],s['M'][::-1,::-1]))
    for scenario,pars,base in [('baseline',p,b),('policy25',p1,s)]:
        for n,start in enumerate(STARTS):
            got=solve(pars,start,diagnostics,f'{scenario}_start{n}')
            check(f'{scenario}_start{n}',relative(got['M'],base['M']))
    cases=[('baseline',p,b),('policy25',p1,s),('zero_shock',p,zero),
           ('symmetric_baseline',sym,sb),('symmetric_policy',sp,ss),('tau20',high,hs),('tau0',free,fs),('mirror',mirror,ms)]
    for name,pars,result in cases: checks_for(result,pars,name,checks)
    sensitivity=[]
    for axis,grid in [('reduction',[0.,.1,.25,.5]),('theta',[2.,4.,6.]),('beta',[.8,.9,1.])]:
        for value in grid:
            theta=value if axis=='theta' else 4.
            beta=value if axis=='beta' else .9
            reduction=value if axis=='reduction' else .25
            cp,ct=calibrate(R,w,r,theta,beta,TAU0)
            cb=solve(cp,diagnostics=diagnostics,name=f'{axis}{value}_base')
            pp=changed(cp,reduction); cs=solve(pp,diagnostics=diagnostics,name=f'{axis}{value}_policy')
            for key in ['R','E','w','r','M']: check(f'{axis}{value}_baseline_{key}',relative(cb[key],ct[key]))
            checks_for(cb,cp,f'{axis}{value}_base',checks); checks_for(cs,pp,f'{axis}{value}_policy',checks)
            row=dict(axis=axis,value=value,theta=theta,beta=beta,reduction=reduction,tau0=TAU0,
                     baseline_cross_share=summary(cb,cb)['cross_share'],**summary(cs,cb),data_nature=NATURE)
            for key in ['R','E','w','r']:
                for j,region in enumerate(REGIONS): row[f'{key}_{region}_pct']=100*(cs[key][j]/cb[key][j]-1)
            sensitivity.append(row)
    equilibrium=[]; flows=[]; summaries=[]
    for name,pars,result in cases[:7]:
        for i,reg in enumerate(REGIONS):
            equilibrium.append(dict(scenario=name,region=reg,**{k:result[k][i] for k in ['R','E','w','r']},data_nature=NATURE))
            for j,job in enumerate(REGIONS): flows.append(dict(scenario=name,home_region=reg,work_region=job,workers=result['M'][i,j],data_nature=NATURE))
        comparison_base=sb if name.startswith('symmetric') else b
        summaries.append(dict(scenario=name,**summary(result,comparison_base),data_nature=NATURE))
    fixed_rows=[]
    for name,result in [('fixed_prices_prediction',fixed),('general_equilibrium',s)]:
        for i,reg in enumerate(REGIONS):
            fixed_rows.append(dict(scenario=name,region=reg,**{k:result[k][i] for k in ['R','E','w','r']},**summary(result,b),data_nature=NATURE))
    save_csv(output/'equilibrium-results.csv',equilibrium)
    save_csv(output/'commuting-matrix-results.csv',flows)
    save_csv(output/'commuting-summary.csv',summaries)
    save_csv(output/'fixed-price-comparison.csv',fixed_rows)
    save_csv(output/'sensitivity-results.csv',sensitivity)
    save_csv(output/'verification.csv',checks)
    save_csv(output/'teaching-central-residential-baseline.csv',[dict(region=reg,**{k:target[k][i] for k in ['R','E','w','r','H','Z','B']},data_nature=NATURE) for i,reg in enumerate(REGIONS)])
    dump(output/'calibrated-parameters.json',dict(data_nature=NATURE,**p))
    dump(output/'input-sha256.json',hashes)
    dump(output/'solver-diagnostics.json',diagnostics)
    dump(output/'main-results.json',dict(data_nature=NATURE,baseline=b,policy=s,fixed_prices=fixed,summary=summary(s,b)))
    env=dict(python=sys.version,platform=platform.platform(),executable=sys.executable,
             packages={x:importlib.metadata.version(x) for x in ['numpy','scipy','pandas','matplotlib']},
             command=sys.argv,cwd=str(Path.cwd()),utc=datetime.now(timezone.utc).isoformat())
    dump(output/'environment.json',env)
    failures=[x for x in checks if not x['passed']]
    dump(output/'verification.json',dict(passed=not failures,count=len(checks),failed=failures,
                                        max_error=max(x['error'] for x in checks),data_nature=NATURE))
    if failures: raise RuntimeError(f'{len(failures)} 项核验失败，见 verification.csv')
    print(json.dumps(dict(output=str(output),checks=len(checks),passed=True,**summary(s,b)),ensure_ascii=False))
    return b,s,checks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.data,args.output)

if __name__=='__main__': main()
