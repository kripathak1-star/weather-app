import numpy as np, wave
SR=44100;DUR=50.0;N=int(SR*DUR);t=np.arange(N)/SR;out=np.zeros((N,2));rng=np.random.default_rng(7)
note=lambda m:440*2**((m-69)/12)
def lp(x,k):return np.convolve(x,np.ones(k)/k,'same')
BPM=100;beat=60/BPM;bar=beat*4
prog=[[50,54,57,62],[47,50,54,59],[43,47,50,55],[45,49,52,57]]   # D Bm G A
# intensity: intro soft, build from 7s, full 16-44, drop at 44, finale chord
inten=np.interp(t,[0,1.2,6.8,7.2,15,15.2,29.8,30.2,40,40.2,44.8,45.2,48,50],[0,.3,.4,.7,.75,.9,.9,.85,.85,.7,.8,1,1,0])
# pads (detuned saws, filtered)
for b in range(int(DUR/bar)+1):
    s=int(b*bar*SR);n=min(int(bar*SR*1.05),N-s)
    if n<=0:break
    tt=np.arange(n)/SR;e=np.minimum(1,tt/.3)*np.clip((bar*1.05-tt)/.3,0,1)
    for m in prog[b%4]:
        for d in(-.12,.12):
            ph=note(m)*(1+d/100)*tt;w=2*(ph%1)-1;out[s:s+n,0 if d<0 else 1]+=.022*w*e
    out[s:s+n]+=(.14*np.sin(2*np.pi*note(prog[b%4][0]-12)*tt)*e)[:,None]
for c in range(2):out[:,c]=lp(out[:,c],14)
out*=np.clip(inten*1.1,.25,1)[:,None]*(t<45.2)[:,None]
# arp plucks (16ths) from 7s
step=beat/4;i=0
while i*step<45.2:
    st=i*step
    if st>=7:
        s=int(st*SR);n=int(step*SR);b=int(st/bar);ch=prog[b%4];m=ch[[0,1,2,3,2,1,2,3][i%8]]+12
        tt=np.arange(n)/SR;w=np.sin(2*np.pi*note(m)*tt)+.4*np.sin(4*np.pi*note(m)*tt);g=.05*inten[s]*np.exp(-tt*18)
        out[s:s+n,0]+=w*g*(.7 if i%2 else 1);out[s:s+n,1]+=w*g*(1 if i%2 else .7)
    i+=1
# drums from 8s to 44s
for k in range(int(45.2/beat)):
    st=k*beat
    if st<7.2:continue
    s=int(st*SR);n=int(.4*SR);tt=np.arange(n)/SR
    f=48+110*np.exp(-tt*28);kick=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*8);out[s:s+n]+=(.42*kick*inten[s])[:,None]
    if k%2==1:
        n2=int(.25*SR);sn=rng.standard_normal(n2)*np.exp(-np.arange(n2)/SR*16);clap=lp(sn,3);out[s:s+n2]+=(.10*clap*inten[s])[:,None]
    s2=int((st+beat/2)*SR);n3=int(.05*SR);hh=np.diff(rng.standard_normal(n3+1))*np.exp(-np.arange(n3)/SR*90);out[s2:s2+n3]+=(.035*hh*inten[s])[:,None]
def impact(at,amp=1.0,dec=2.5):
    s=int(at*SR);n=min(int(3*SR),N-s);tt=np.arange(n)/SR
    boom=np.sin(2*np.pi*(32+70*np.exp(-tt*10))*tt)*np.exp(-tt*dec);nz=lp(rng.standard_normal(n),4)*np.exp(-tt*9)
    out[s:s+n]+=(amp*(.8*boom+.25*nz))[:,None]
def whoosh(at,l=.9,amp=.18):
    s=int((at-l*.6)*SR);n=int(l*SR);tt=np.arange(n)/SR;nz=lp(rng.standard_normal(n),5);e=np.sin(np.pi*tt/l)**2
    out[s:s+n,0]+=amp*nz*e*np.linspace(1,.3,n);out[s:s+n,1]+=amp*nz*e*np.linspace(.3,1,n)
def riser(a,b,amp=.12):
    s=int(a*SR);n=int((b-a)*SR);tt=np.arange(n)/SR;k=tt/(b-a);nz=lp(rng.standard_normal(n),3)
    tone=np.sin(2*np.pi*np.cumsum(200+1800*k**2)/SR)*.3;out[s:s+n]+=(amp*(nz*.7+tone)*k**2)[:,None]
def sparkle(at,amp=.06):
    s=int(at*SR);n=int(.5*SR);tt=np.arange(n)/SR
    for f in (2093,3136,4186):out[s:s+n]+=(amp*np.sin(2*np.pi*f*tt)*np.exp(-tt*9))[:,None]
def click(at,amp=.1):
    s=int(at*SR);n=int(.04*SR);tt=np.arange(n)/SR;out[s:s+n]+=(amp*np.sin(2*np.pi*1800*tt)*np.exp(-tt*120))[:,None]
# --- timeline sync (store story) ---
sparkle(.6,.06);click(.62,.12);click(.7,.1);impact(.75,.6,2.5)
for i in range(6):click(1.2+i*.5,.05)
whoosh(5.1,1.0,.18);riser(5.6,7.2,.1);impact(7.2,.9,2.2);whoosh(7.0,1.0,.25)
whoosh(15.1,.8,.22);impact(15.25,1.0,2.0);sparkle(15.6,.08)
for i in range(6):cs=15.2+2.4+i*1.8;whoosh(cs+.35,.6,.16);impact(cs+.5,.35,4);sparkle(cs+.55,.07);whoosh(cs+1.6,.5,.08)
for i in range(5):sparkle(28.4+i*.25,.04)
riser(28.6,30.2,.1);whoosh(30.1,.9,.22);impact(30.25,.8,2.5)
for i in range(17):click(30.4+i*.06,.05)
for f in range(14):whoosh(30.2+2.0+f*.5+.5,.4,.05);sparkle(30.2+2.0+f*.5+.85,.035)
whoosh(40.1,1.0,.25);impact(40.25,.6,2.5);sparkle(40.9,.06);sparkle(41.3,.06)
riser(43.4,45.2,.12);whoosh(45.0,1.0,.3);impact(45.25,1.2,1.6);sparkle(46.0,.08);sparkle(48.2,.05)
# finale chord swell 45.3-50
s=int(45.2*SR);n=N-s;tt=np.arange(n)/SR;e=np.minimum(1,tt/.4)*np.clip((DUR-45.2-tt)/1.5,0,1)
for m in [50,57,62,66,69]:
    for d in(-.1,.1):out[s:s+n,0 if d<0 else 1]+=.03*(2*((note(m)*(1+d/100)*tt)%1)-1)*e
out[s:,0]=lp(out[s:,0],10);out[s:,1]=lp(out[s:,1],10)
out*=np.clip(t/.3,0,1)[:,None];out/=np.max(np.abs(out));out*=.9
with wave.open('music.wav','wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((out*32767).astype('<i2').tobytes())
print('ok')
