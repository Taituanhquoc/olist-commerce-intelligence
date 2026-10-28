"""Export source-grounded portfolio figures without requiring the full warehouse."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from src.promise_lab import load_state_data
from src.config import ROOT

model=load_state_data()
rows=model['rows']
out=ROOT/'reports'/'figures';out.mkdir(parents=True,exist_ok=True)
C={'bg':'#071726','panel':'#0e2636','white':'#e9f5f8','sub':'#a1b4c7','teal':'#48e1c5','gold':'#f4c477','grid':'#304c5c'}
plt.rcParams.update({'figure.facecolor':C['bg'],'axes.facecolor':C['panel'],'axes.labelcolor':C['sub'],'text.color':C['white'],'xtick.color':C['sub'],'ytick.color':C['sub'],'font.size':11,'font.family':'DejaVu Sans'})
fig, ax=plt.subplots(figsize=(13.6,6.8));fig.subplots_adjust(left=.085,right=.96,bottom=.24,top=.78)
fig.text(.085,.925,'PROMISE LAB    /    DELIVERY INTELLIGENCE',color=C['teal'],fontweight='bold',fontsize=11)
fig.text(.085,.85,'Regional delivery risk, without denominator bias',color=C['white'],fontweight='bold',fontsize=23)
fig.text(.085,.805,'Bubble area = historical late orders  |  X = shipped volume (log)  |  Y = percent late',color=C['sub'],fontsize=11)
ax.set_xscale('log')
for r in rows:
 high=r['observed_late_rate']>model['national_late_rate']
 ax.scatter(r['delivered_orders'],100*r['observed_late_rate'],s=25+r['late_orders']*.55,
            c=C['teal'] if high else C['gold'],alpha=.80,edgecolor=C['bg'],linewidth=1,zorder=3)
 if r['state'] in ['AL','MA','RJ','SP','BA','CE','MG']:
  ax.annotate(r['state'],(r['delivered_orders'],100*r['observed_late_rate']),xytext=(8,5),textcoords='offset points',fontsize=10,color=C['white'])
ax.axhline(100*model['national_late_rate'],color=C['gold'],ls='--',lw=1.5)
ax.text(350,100*model['national_late_rate']+.85,'National late rate 6.79%',color=C['gold'],fontsize=10)
ax.set_xlabel('Number of delivered orders per state (log scale)',labelpad=14)
ax.set_ylabel('Observed late-delivery rate (%)',labelpad=14)
ax.grid(axis='y',alpha=.16,color=C['sub']);ax.set_axisbelow(True)
for spine in ax.spines.values():spine.set_color(C['grid'])
ax.set_ylim(0,26);ax.set_xlim(250,80000)
fig.text(.085,.055,'HISTORICAL OLIST 2017–18   •   21 states in export (95,354 of 96,203 delivered orders nationwide)   •   Not causal',color=C['sub'],fontsize=9)
fig.savefig(out/'promise_lab_risk_priority.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)

fig,ax=plt.subplots(figsize=(11.2,6.1));fig.subplots_adjust(left=.11,right=.93,bottom=.11,top=.76)
fig.text(.11,.925,'PROMISE LAB    /    FINANCIAL DECISION SENSITIVITY',color=C['teal'],fontweight='bold',fontsize=11)
fig.text(.11,.84,'Break-even is a hypothesis, not a result',color=C['white'],fontweight='bold',fontsize=21)
from src.promise_lab import scenarios,Assumptions
sc=scenarios(model,Assumptions())
labels=[r['scenario'] for r in sc];values=[r['modeled_net_brl'] for r in sc]
ax.bar(labels,values,color=[C['gold'],C['teal'], '#6f9ece'],width=.6)
ax.axhline(0,color=C['white'],lw=.9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'R${v/1000:.0f}k'))
for i,v in enumerate(values):ax.annotate(f'{"−" if v<0 else "+"}R${abs(v):,.0f}',(i,v),xytext=(0,-17 if v<0 else 9),textcoords='offset points',ha='center',color=C['white'],fontweight='bold')
ax.set_ylabel('Modeled net value, BRL (not observed)');ax.grid(axis='y',alpha=.16,color=C['sub']);ax.set_axisbelow(True)
for spine in ax.spines.values():spine.set_color(C['grid'])
fig.text(.11,.06,'Historical risk × hypothetical efficacy × assumed avoided-late value − treatment costs. Experiment required.',color=C['sub'],fontsize=9)
fig.savefig(out/'promise_lab_sensitivity.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
print('Exported 2 portfolio figures')
