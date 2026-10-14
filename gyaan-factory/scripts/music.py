import numpy as np, wave
import json,sys
EVJ=json.load(open(sys.argv[1]));RT=EVJ['starts'];OUT=sys.argv[2];SEED=int(sys.argv[3]) if len(sys.argv)>3 else 1
SR=44100; DUR=RT[-1]; N=int(SR*DUR); t=np.arange(N)/SR
BPM=[116,120,124,128][SEED%4]; beat=60/BPM; bar=beat*4
out=np.zeros((N,2))
def note(f): return 440*2**((f-69)/12)
def env_ad(n,a,d):
    e=np.ones(n); ai=int(a*SR); e[:ai]=np.linspace(0,1,ai); e[ai:]=np.exp(-np.arange(n-ai)/(d*SR)); return e
PROGS=[[[57,60,64],[53,57,60],[48,52,55],[55,59,62]],[[50,53,57],[46,50,53],[48,52,55],[45,48,52]],[[52,55,59],[48,52,55],[55,59,62],[50,54,57]],[[45,48,52],[41,45,48],[43,47,50],[40,44,47]]]
prog=PROGS[SEED%len(PROGS)]
rng=np.random.default_rng(SEED)
# intensity curve: soft intro, full from 7s, drop at 63, fade out
inten=np.clip((t-RT[1]+0.2)/0.3,0,1)*1.0+np.clip((t-1)/2,0,1)*0.55*(t<RT[1])*np.clip((DUR-t)/4,0,1)
# pads
nbars=int(DUR/bar)+1
for b in range(nbars):
    s=int(b*bar*SR); n=min(int(bar*SR*1.1),N-s)
    if n<=0: break
    tt=np.arange(n)/SR; e=np.minimum(1,tt/0.4)*np.minimum(1,(bar*1.1-tt)/0.4).clip(0)
    for i,m in enumerate(prog[b%4]):
        for det in (-0.08,0.08):
            ph=2*np.pi*note(m+(-12 if i==0 else 0))*(1+det/100)*tt
            w=(2*((ph/(2*np.pi))%1)-1)  # saw
            out[s:s+n,0 if det<0 else 1]+=0.035*w*e
    # bass
    ph=note(prog[b%4][0]-24)*tt
    out[s:s+n]+=(0.16*np.sin(2*np.pi*ph)*e)[:,None]
# simple lowpass on pads
from numpy import convolve
k=np.ones(18)/18
for c in range(2): out[:,c]=convolve(out[:,c],k,'same')
# arp (16ths)
step=beat/4; i=0
while i*step<DUR:
    s=int(i*step*SR); n=min(int(step*SR),N-s); b=int(i*step/bar)
    ch=prog[b%4]; m=ch[[0,1,2,1][i%4]]+12+(12 if (i//8)%2 else 0)
    tt=np.arange(n)/SR; w=np.sign(np.sin(2*np.pi*note(m)*tt))*0.5+np.sin(2*np.pi*note(m)*tt)*.5
    g=0.05*inten[s]*env_ad(n,0.003,0.06)
    out[s:s+n,0]+=w*g*(0.7 if i%2 else 1); out[s:s+n,1]+=w*g*(1 if i%2 else 0.7)
    i+=1
# drums
for k in range(int(DUR/beat)+1):
    s=int(k*beat*SR); 
    if s>=N: break
    if inten[s]<0.05: continue
    n=min(int(0.35*SR),N-s); tt=np.arange(n)/SR
    f=50+120*np.exp(-tt*30); kick=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*9)
    out[s:s+n]+=(0.5*kick*inten[s])[:,None]
    if k%2==1:
        n2=min(int(0.2*SR),N-s); sn=rng.standard_normal(n2)*np.exp(-np.arange(n2)/SR*18)
        out[s:s+n2]+=(0.13*sn*inten[s])[:,None]
    for h in (0.5,):
        s2=int((k+h)*beat*SR); n3=min(int(0.05*SR),N-s2)
        if n3>0:
            hh=np.diff(rng.standard_normal(n3+1))*np.exp(-np.arange(n3)/SR*80)
            out[s2:s2+n3]+=(0.05*hh*inten[s])[:,None]
# whooshes at cuts
for c in [e['t'] for e in EVJ['events'] if e['type']=='whoosh']:
    s=int((c-0.35)*SR); n=int(0.6*SR); tt=np.arange(n)/SR
    if s<0 or s+n>N: continue
    nz=rng.standard_normal(n); nz=convolve(nz,np.ones(6)/6,'same')
    e=np.sin(np.pi*tt/0.6)**2
    out[s:s+n,0]+=0.12*nz*e*np.linspace(1,.3,n); out[s:s+n,1]+=0.12*nz*e*np.linspace(.3,1,n)
# title hit
s=int(RT[1]*SR); n=int(2*SR); tt=np.arange(n)/SR
out[s:s+n]+=(0.6*np.sin(2*np.pi*(45+80*np.exp(-tt*8))*tt)*np.exp(-tt*2.5))[:,None]

EV=EVJ['events']
for e in EV:
    s=int(e['t']*SR)
    if s>=N: continue
    if e['type']=='pop':
        n=min(int(.12*SR),N-s); tt=np.arange(n)/SR
        out[s:s+n]+=(0.18*np.sin(2*np.pi*(900+1400*np.exp(-tt*40))*tt)*np.exp(-tt*35))[:,None]
    elif e['type']=='stamp':
        n=min(int(.9*SR),N-s); tt=np.arange(n)/SR
        boom=np.sin(2*np.pi*(40+90*np.exp(-tt*12))*tt)*np.exp(-tt*4.5)
        nz=rng.standard_normal(n)*np.exp(-tt*14)
        out[s:s+n]+=(0.75*boom+0.25*nz)[:,None]
        # riser before stamp
        r0=max(0,s-int(1.5*SR)); rn=s-r0; rt=np.arange(rn)/SR
        out[r0:s]+=(0.06*rng.standard_normal(rn)*(rt/1.5)**2)[:,None]
out*=np.clip(t/1.5,0,1)[:,None]
out=out/np.max(np.abs(out))*0.85
with wave.open(OUT,'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((out*32767).astype('<i2').tobytes())
print('ok')
