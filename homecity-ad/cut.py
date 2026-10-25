import sys,glob,os,numpy as np
from PIL import Image,ImageDraw,ImageFilter
src=sys.argv[1];out=sys.argv[2]
for f in sorted(glob.glob(src+'/*.jpg'))+[src+'/app-icon-512.png']:
    im=Image.open(f).convert('RGB');a=np.asarray(im).astype(int)
    if 'sign' in f or 'app-icon' in f:
        im.save(out+'/'+os.path.basename(f).rsplit('.',1)[0]+'.png');continue
    wh=(a.min(axis=2)>232)&((a.max(axis=2)-a.min(axis=2))<18)
    bg=np.zeros_like(wh);bg[0,:]=wh[0,:];bg[-1,:]=wh[-1,:];bg[:,0]=wh[:,0];bg[:,-1]=wh[:,-1]
    while True:
        n=bg.copy();n[1:]|=bg[:-1];n[:-1]|=bg[1:];n[:,1:]|=bg[:,:-1];n[:,:-1]|=bg[:,1:];n&=wh
        if (n==bg).all():break
        bg=n
    al=Image.fromarray(((~bg)*255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    rgba=im.copy();rgba.putalpha(al)
    bb=al.point(lambda v:255 if v>20 else 0).getbbox()
    rgba=rgba.crop(bb)
    w,h=rgba.size;s=max(w,h);pad=int(s*.04);c=Image.new('RGBA',(s+2*pad,s+2*pad),(0,0,0,0));c.paste(rgba,((s-w)//2+pad,(s-h)//2+pad))
    c=c.resize((512,512),Image.LANCZOS);c.save(out+'/'+os.path.basename(f).rsplit('.',1)[0]+'.png')
    print(os.path.basename(f),round(1-bg.mean(),2),w/h if h else 0)
