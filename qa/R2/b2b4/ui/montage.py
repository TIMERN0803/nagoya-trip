import sys
from PIL import Image
out=sys.argv[1]; files=sys.argv[2:]
ims=[Image.open(f) for f in files]
w=sum(i.width for i in ims)+10*(len(ims)-1); h=max(i.height for i in ims)
m=Image.new("RGB",(w,h),"white");x=0
for i in ims: m.paste(i,(x,0)); x+=i.width+10
m.save(out)
