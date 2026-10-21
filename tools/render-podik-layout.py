"""Render the actual focus IDs, coordinates and prerequisites for layout review."""
from pathlib import Path
import runpy
import textwrap
from PIL import Image, ImageDraw, ImageFont

data=runpy.run_path('tools/validate-podik.py')
focus,first,loc=data['focus'],data['first'],data['loc']
req,exc=data['requirements'],data['exclusions']
sx,sy,margin=46,76,115
minx=min(int(first(f,'x')) for f in focus.values())
maxx=max(int(first(f,'x')) for f in focus.values())
maxy=max(int(first(f,'y')) for f in focus.values())
im=Image.new('RGB',((maxx-minx)*sx+2*margin,(maxy+2)*sy+margin),'#172027')
d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',10)
big=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',24)
def pos(fid):
    f=focus[fid]
    return (int(first(f,'x'))-minx)*sx+margin,int(first(f,'y'))*sy+margin
for fid,groups in req.items():
    x,y=pos(fid)
    for parent in set().union(*groups):
        px,py=pos(parent);mid=py+sy*.5
        d.line([(px,py+23),(px,mid),(x,mid),(x,y-23)],fill='#758997',width=2)
        d.polygon([(x,y-23),(x-4,y-30),(x+4,y-30)],fill='#758997')
for fid,f in focus.items():
    x,y=pos(fid)
    if x<0:raise ValueError('Invalid diagram coordinate')
    fx=int(first(f,'x'))
    color=('#66534b' if fx<=-28 else '#496259' if fx<=-14 else '#63603e' if fx<0 else '#525d74' if fx<=8 else '#79504f' if fx<=16 else '#555071' if fx<=27 else '#3f6772' if fx<=40 else '#4b6450')
    d.rounded_rectangle((x-58,y-23,x+58,y+23),radius=7,fill=color,outline='#bfbaa0',width=1)
    lines=textwrap.wrap(loc[fid],width=18)
    for i,line in enumerate(lines[:3]):
        d.text((x,y-16+i*14),line,font=font,fill='#ffffff',anchor='mt')
    d.text((x,y+27),f"{int(first(f,'cost'))*7} дн.",font=small,fill='#adbdc6',anchor='mt')
d.text((margin,30),'Подиковая республика — 101 фокус: схема из файлов мода',font=big,fill='#f1e6bf')
d.text((margin,65),'Принтер и мама · Балконный вопрос · Культ · Совет · Футболка · Макафон · Гродно · Экономика',font=font,fill='#bdcbd3')
out=Path('tools/diagnostics/podik-expansion/focus-layout.png');out.parent.mkdir(parents=True,exist_ok=True);im.save(out)
print(out.resolve())
