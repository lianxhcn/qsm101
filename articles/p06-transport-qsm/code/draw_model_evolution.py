"""确定性绘制 P04—P06 机制图。全部设定为教学构造，图中不含政策结果。"""
from pathlib import Path
from datetime import datetime
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager

BLUE='#23649a'; ORANGE='#b96924'; GRAY='#303840'

def build(out,stamp):
    candidates=['Microsoft YaHei','SimHei','Noto Sans CJK SC']
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((f for f in candidates if f in available),None)
    if not font: raise RuntimeError('缺少中文字体，请安装后再制图')
    plt.rcParams.update({'font.family':font,'font.size':11,'svg.fonttype':'path','pdf.fonttype':42,'axes.unicode_minus':False})
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    def panel(ax,n):
        ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
        def text(x,y,s,size=11,color=GRAY,weight='normal'):
            ax.text(x,y,s,ha='center',va='center',fontsize=size,color=color,weight=weight,linespacing=1.5)
        def box(x,y,w,h,s,color=GRAY,face='#f7f9fb',size=11):
            ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.018',ec=color,fc=face,lw=1.2))
            text(x+w/2,y+h/2,s,size,color)
        def arrow(start,end,color=GRAY,width=1.4,rad=0):
            ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color=color,lw=width,connectionstyle=f'arc3,rad={rad}'))
        titles=['P04：居住地等于工作地','P05：居住与工作分开','P06：非对称城市的交通改善']
        text(.5,.95,titles[n],12,weight='bold')
        if n==0:
            box(.04,.68,.40,.17,'A 地区\n居民 / 岗位',BLUE)
            box(.56,.68,.40,.17,'B 地区\n居民 / 岗位',ORANGE)
            text(.5,.60,r'$N_{i}=R_{i}=E_{i}$',14)
            box(.18,.44,.64,.10,r'住房供给 $H_{B}\uparrow$',ORANGE)
            arrow((.5,.435),(.5,.375))
            box(.18,.28,.64,.09,'房租 → 人口 / 就业')
            arrow((.5,.27),(.5,.22))
            box(.18,.12,.64,.09,'工资与房租反馈')
            arrow((.17,.16),(.17,.33),rad=-.25)
            text(.5,.04,'只允许本地工作',11)
        elif n==1:
            text(.5,.85,'四种联合选择 (行：居住；列：工作)',10)
            box(.12,.59,.76,.19,'         工作 A     工作 B\n居住 A    AA          AB\n居住 B    BA          BB',size=11)
            text(.20,.52,'A',12,BLUE); text(.80,.52,'B',12,ORANGE)
            arrow((.27,.535),(.73,.535),BLUE,1.2)
            arrow((.73,.50),(.27,.50),ORANGE,1.2)
            text(.5,.43,'对称基准：双向通勤同样多',10)
            text(.5,.34,r'$R_{i}=\sum_{j}M_{ij}$',14)
            text(.5,.25,r'$E_{j}=\sum_{i}M_{ij}$',14)
            box(.18,.10,.64,.09,r'主政策：$H_{B}\uparrow$',ORANGE)
            text(.5,.04,'居民决定住房需求，就业决定劳动投入',10)
        else:
            box(.03,.71,.43,.15,'A：就业中心\n较高 Z、工资',BLUE)
            box(.54,.71,.43,.15,'B：居住区\n较多住房、较低租金',ORANGE,size=10.5)
            arrow((.22,.66),(.78,.66),BLUE,1.2)
            arrow((.78,.60),(.22,.60),ORANGE,3.5)
            text(.5,.545,'基准 B → A 多于 A → B',10)
            box(.12,.40,.76,.10,r'政策：$\tau_{AB}=\tau_{BA}\downarrow$')
            arrow((.5,.395),(.5,.345))
            box(.22,.255,.56,.085,r'联合选择 $M_{ij}$')
            arrow((.35,.25),(.23,.19)); arrow((.65,.25),(.77,.19))
            box(.015,.095,.435,.09,r'就业 $E_{j}\to w_{j}$',BLUE,size=11)
            box(.55,.095,.435,.09,r'居住 $R_{i}\to r_{i}$',ORANGE,size=11)
            arrow((.02,.19),(.21,.30),BLUE,rad=-.25)
            arrow((.98,.19),(.79,.30),ORANGE,rad=.25)
            text(.5,.035,'居民与就业可向不同方向调整',10.5)
    outputs=[]
    for mobile in [False,True]:
        fig,axes=plt.subplots(3 if mobile else 1,1 if mobile else 3,figsize=(4.2,15) if mobile else (11,5.7),dpi=100)
        for n,ax in enumerate(axes): panel(ax,n)
        fig.subplots_adjust(left=.02,right=.98,top=.99,bottom=.05 if not mobile else .025,wspace=.10,hspace=.08)
        fig.text(.5,.018 if not mobile else .008,'教学构造；蓝色：A，橙色：B，灰色：共同市场与反馈',ha='center',fontsize=10 if not mobile else 8.5,color=GRAY)
        name=f'qsm-p06-fig01-model-evolution'+('-mobile' if mobile else '')+f'-{stamp}'
        for ext in ['png','svg','pdf']:
            path=out/f'{name}.{ext}'
            fig.savefig(path,dpi=100,facecolor='white')
            outputs.append(str(path))
        plt.close(fig)
    print('\n'.join(outputs))
    return outputs

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--stamp',default=datetime.now().strftime('%Y%m%d-%H%M%S'))
    a=p.parse_args(); build(a.output,a.stamp)

