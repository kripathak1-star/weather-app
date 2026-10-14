import glob,sys
from PIL import Image
fs=sorted(glob.glob('pr_*.jpg'))
s=Image.new('RGB',(1920,360*((len(fs)+2)//3)))
for i,f in enumerate(fs): s.paste(Image.open(f).resize((640,360)),((i%3)*640,(i//3)*360))
s.save('sheet.jpg',quality=80)
