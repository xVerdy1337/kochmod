"""Build B09/B11 flags (padded with background colour, no cropping) and set map colours from them."""
from pathlib import Path
import re
import shutil
import sys
from PIL import Image

root = Path(__file__).resolve().parents[1]
img_dir = Path(sys.argv[1])
SRC = {'B09': '3.png', 'B11': '4.webp'}
colors = {}
for tag, name in SRC.items():
    src = img_dir / name
    src_copy = root / f'gfx/flags/source/koch_{tag}.png'
    src_copy.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert('RGB')
    im.save(src_copy)
    # background colour = median of a thin border strip
    w, h = im.size
    strip = [im.getpixel((x, 3)) for x in range(0, w, 8)] + [im.getpixel((x, h - 4)) for x in range(0, w, 8)]
    bg = tuple(sorted(c[i] for c in strip)[len(strip) // 2] for i in range(3))
    colors[tag] = bg
    for folder, (fw, fh) in [('', (82, 52)), ('medium', (41, 26)), ('small', (10, 7))]:
        scale = min(fw / w, fh / h)
        nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
        small = im.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (fw, fh), bg + (255,))
        canvas.paste(small, ((fw - nw) // 2, (fh - nh) // 2))
        d = root / 'gfx/flags' / folder
        for suffix in ('', '_democratic', '_fascism', '_communism', '_neutrality'):
            path = d / f'{tag}{suffix}.tga'
            canvas.save(path, compression=None)
            data = path.read_bytes()
            assert data[2] == 2 and data[16] == 32, path
            chk = Image.open(path); chk.load()
            assert chk.size == (fw, fh), path

cp = root / 'common/countries/colors.txt'
s = cp.read_text(encoding='utf-8')
for tag, c in colors.items():
    block = f'{tag} = {{\n    color = rgb {{ {c[0]} {c[1]} {c[2]} }}\n    color_ui = rgb {{ {c[0]} {c[1]} {c[2]} }}\n}}\n'
    s = re.sub(rf'\n?{tag} = \{{[^}}]*\}}\n', '', s) if re.search(rf'\b{tag} = ', s) else s
    s = s.rstrip('\n') + '\n\n' + block
    p = root / f'common/countries/koch_{tag}.txt'
    t = p.read_text(encoding='utf-8')
    p.write_text(re.sub(r'color\s*=\s*\{[^}]*\}', f'color = {{ {c[0]} {c[1]} {c[2]} }}', t), encoding='utf-8')
cp.write_text(s, encoding='utf-8')
print(colors)
