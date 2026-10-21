from pathlib import Path
import re
import shutil
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1]
def write(path, text):
    (root / path).write_text(text, encoding='utf-8')

write('history/countries/B08 - koch.txt', '''capital = 195
set_politics = {
    ruling_party = neutrality
    elections_allowed = no
}
set_popularities = {
    democratic = 0
    fascism = 0
    communism = 0
    neutrality = 100
}
recruit_character = KOCH_B08_artem_verdi
''')
write('common/characters/koch_B08.txt', '''characters = {
    KOCH_B08_artem_verdi = {
        name = KOCH_B08_artem_verdi
        portraits = {
            civilian = {
                large = GFX_portrait_KOCH_B08_artem_verdi
            }
        }
        country_leader = {
            ideology = despotism
            expire = "2100.1.1.1"
            id = -1
        }
    }
}
''')
p = root / 'common/countries/koch_B08.txt'
p.write_text(re.sub(r'color\s*=\s*\{[^}]*\}', 'color = { 255 255 255 }', p.read_text(encoding='utf-8')), encoding='utf-8')
p = root / 'common/countries/colors.txt'
s = p.read_text(encoding='utf-8')
if not re.search(r'\bB08\s*=', s):
    p.write_text(s + '\nB08 = {\n    color = rgb { 255 255 255 }\n    color_ui = rgb { 255 255 255 }\n}\n', encoding='utf-8')
for sid in (195,146,216,928):
    p = next(p for p in (root / 'history/states').glob(f'{sid}*.txt') if re.search(r'\bid\s*=\s*'+str(sid)+r'\b', p.read_text(encoding='utf-8')))
    s = p.read_text(encoding='utf-8')
    owners = re.findall(r'\b(?:owner|controller|add_core_of)\s*=\s*(\w+)', s)
    assert all(tag == 'B08' for tag in owners), (p,owners)
    if not owners:
        s = re.sub(r'(\bhistory\s*=\s*\{)', r'\1\n        owner = B08\n        controller = B08\n        add_core_of = B08', s, count=1)
    p.write_text(s, encoding='utf-8')

for lang, name, desc in [
    ('russian', 'Артем Верди', 'ИТМО контролирует регионы 195, 146, 216 и 928. Столица — Санкт-Петербург. Страну возглавляет Артем Верди. Поддержка партий: демократия — 0%, фашизм — 0%, коммунизм — 0%, авторитаризм — 100%.'),
    ('english', 'Artem Verdi', 'ITMO controls states 195, 146, 216 and 928. Its capital is Saint Petersburg. Artem Verdi leads the country. Party support: democracy — 0%, fascism — 0%, communism — 0%, non-aligned — 100%.'),
]:
    p = root / f'localisation/{lang}/koch_countries_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig')
    s = re.sub(r' KOCH_B08_DESC:0 .*', f' KOCH_B08_DESC:0 "{desc}"', s)
    key = 'KOCH_B08_artem_verdi'
    if not re.search(r'^\s*'+key+r':', s, re.M):
        s += f'\n {key}:0 "{name}"\n'
    p.write_text(s, encoding='utf-8-sig')

p = root / 'interface/koch_portraits.gfx'
s = p.read_text(encoding='utf-8')
if 'GFX_portrait_KOCH_B08_artem_verdi' not in s:
    s = s.replace('spriteTypes = {', '''spriteTypes = {
    spriteType = {
        name = "GFX_portrait_KOCH_B08_artem_verdi"
        texturefile = "gfx/leaders/B08/koch_artem_verdi.dds"
    }''', 1)
p.write_text(s, encoding='utf-8')

portrait_src = Path('C:/Users/qacdf/AppData/Local/Temp/codex-clipboard-42181391-f69b-425a-9281-875aba80306d.png')
flag_src = Path('C:/Users/qacdf/AppData/Local/Temp/codex-clipboard-f9717b69-eed1-495c-b144-2f5f59bd45b7.png')
d = root / 'gfx/leaders/B08'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2(portrait_src, d / 'koch_artem_verdi_source.png')
im = Image.open(portrait_src).convert('RGB')
w,h = im.size
im = im.crop((round(w*0.10), round(h*0.22), round(w*0.88), h))
im = ImageOps.fit(im, (156,210), method=Image.Resampling.LANCZOS)
im.save(d / 'koch_artem_verdi.dds')
im.save(d / 'koch_artem_verdi_preview.png')
d = root / 'gfx/flags/source'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2(flag_src, d / 'koch_B08.png')
im = Image.open(flag_src).convert('RGB')
for folder, size in [('',(82,52)), ('medium',(41,26)), ('small',(10,7))]:
    d = root / 'gfx/flags' / folder
    d.mkdir(parents=True, exist_ok=True)
    flag = im.resize(size, Image.Resampling.LANCZOS)
    flag.save(d / 'B08.tga')
    flag.save(d / 'B08_neutrality.tga')
print('Configured B08: states 195, 146, 216, 928; capital 195; portrait, flags, white color.')
