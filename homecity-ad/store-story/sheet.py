import glob
from PIL import Image
fs=sorted(glob.glob('pr_*.jpg'));n=len(fs);cols=6
s=Image.new('RGB',(270*cols,480*((n+cols-1)//cols)))
for i,f in enumerate(fs): s.paste(Image.open(f).resize((270,480)),((i%cols)*270,(i//cols)*480))
s.save('sheet.jpg',quality=82)
