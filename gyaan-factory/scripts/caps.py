"""Build caption timings. Usage: python caps.py plan.json workdir engine_dir
Spoken text = scene.voice (Hindi). Shown text = scene.caption (Hinglish) mapped proportionally onto the spoken word timings."""
import json, re, sys, numpy as np, soundfile as sf
plan=json.load(open(sys.argv[1])); W=sys.argv[2]; E=sys.argv[3]
durs=json.load(open(f'{W}/durs.json')); words=json.load(open(f'{W}/words.json'))
KEY=set(w.lower() for w in plan.get('caption_keywords',[]))
P=r'[,.!?:;।]$'
def silence_words(i,text):
    a,sr=sf.read(f'{W}/l{i}.wav'); fr=int(.02*sr); n=len(a)//fr
    rms=np.array([np.sqrt(np.mean(a[j*fr:(j+1)*fr]**2)) for j in range(n)]); th=max(rms.max()*.04,1e-4); sp=rms>th
    segs=[];j=0
    while j<n:
        if sp[j]:
            k=j
            while k<n and sp[k]:k+=1
            segs.append([j*.02,k*.02]);j=k
        else:j+=1
    m=[]
    for s in segs:
        if m and s[0]-m[-1][1]<.15:m[-1][1]=s[1]
        else:m.append(s)
    ws=text.split();wts=[len(w)+1.5+(2.5 if re.search(P,w) else 0) for w in ws];S=sum(e-s for s,e in m);tot=sum(wts)
    def s2r(x):
        acc=0
        for s,e in m:
            if acc+(e-s)>=x: return s+(x-acc)
            acc+=e-s
        return m[-1][1]
    cum=0;out=[]
    for w,wt in zip(ws,wts):
        pz=(2.5 if re.search(P,w) else 0)*.6;t0=s2r(cum/tot*S);cum+=wt-pz;t1=s2r(min(cum,tot)/tot*S);cum+=pz;out.append({'w':w,'t':t0,'e':t1})
    return out
caps=[]
for i,sc in enumerate(plan['scenes']):
    hw=words[i] or silence_words(i,sc['voice'])
    shown=(sc.get('caption') or sc['voice']).split()
    N=len(hw);hb=[w['t'] for w in hw]+[hw[-1]['e']]
    def at(f):
        x=f*N;k=min(int(x),N-1);fr=x-k;return hb[k]+(hb[k+1]-hb[k])*fr
    lens=[len(w)+1 for w in shown];tot=sum(lens);cum=0;res=[];chunk=0;cnt=0
    for w,l in zip(shown,lens):
        t0=at(cum/tot);cum+=l;t1=at(cum/tot)
        clean=re.sub(r'[,.!?:;।"]+$','',w)
        res.append({'w':clean,'t':round(t0,3),'e':round(t1,3),'c':chunk,'k':clean.lower() in KEY or bool(re.search(r'\d',clean))})
        cnt+=1
        if re.search(P,w) or cnt>=4: chunk+=1;cnt=0
    caps.append(res)
open(f'{E}/caps.js','w').write('window.CAPS='+json.dumps(caps,ensure_ascii=False)+';')
open(f'{E}/timeline.js','w').write('window.TL7={vdurs:%s};'%json.dumps(durs))
open(f'{E}/plan.js','w').write('window.PLAN='+json.dumps(plan,ensure_ascii=False)+';')
print('captions ok')
