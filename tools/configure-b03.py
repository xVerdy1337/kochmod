from pathlib import Path
import re
import shutil
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1]
def write(path, text):
    (root / path).write_text(text, encoding='utf-8')

write('history/countries/B03 - koch.txt', '''capital = 833
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
recruit_character = KOCH_B03_chetkiye_patsanchiki
''')
write('common/characters/koch_B03.txt', '''characters = {
    KOCH_B03_chetkiye_patsanchiki = {
        name = KOCH_B03_chetkiye_patsanchiki
        portraits = {
            civilian = {
                large = GFX_portrait_KOCH_B03_chetkiye_patsanchiki
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
p = root / 'common/countries/koch_B03.txt'
p.write_text(re.sub(r'color\s*=\s*\{[^}]*\}', 'color = { 127 255 212 }', p.read_text(encoding='utf-8')), encoding='utf-8')
p = root / 'common/countries/colors.txt'
s = p.read_text(encoding='utf-8')
if not re.search(r'\bB03\s*=', s):
    p.write_text(s + '\nB03 = {\n    color = rgb { 127 255 212 }\n    color_ui = rgb { 127 255 212 }\n}\n', encoding='utf-8')
for sid in (833,400):
    p = next(p for p in (root / 'history/states').glob(f'{sid}*.txt') if re.search(r'\bid\s*=\s*'+str(sid)+r'\b', p.read_text(encoding='utf-8')))
    s = p.read_text(encoding='utf-8')
    owners = re.findall(r'\b(?:owner|controller|add_core_of)\s*=\s*(\w+)', s)
    assert all(tag == 'B03' for tag in owners), (p,owners)
    if not owners:
        s = re.sub(r'(\bhistory\s*=\s*\{)', r'\1\n        owner = B03\n        controller = B03\n        add_core_of = B03', s, count=1)
    p.write_text(s, encoding='utf-8')

for lang, name, desc in [
    ('russian', 'Четкие Пацанчики', 'Волжская Коммуна контролирует регионы 833 и 400. Столица — Волжск. Страной управляют Четкие Пацанчики. Поддержка партий: демократия — 0%, фашизм — 0%, коммунизм — 0%, авторитаризм — 100%.'),
    ('english', 'Chetkiye Patsanchiki', 'Volga Commune controls states 833 and 400. Its capital is Volzhsk. Chetkiye Patsanchiki govern the country. Party support: democracy — 0%, fascism — 0%, communism — 0%, non-aligned — 100%.'),
]:
    p = root / f'localisation/{lang}/koch_countries_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig').replace('Волжская коммуна', 'Волжская Коммуна')
    s = re.sub(r' KOCH_B03_DESC:0 .*', f' KOCH_B03_DESC:0 "{desc}"', s)
    key = 'KOCH_B03_chetkiye_patsanchiki'
    if not re.search(r'^\s*'+key+r':', s, re.M):
        s += f'\n {key}:0 "{name}"\n'
    p.write_text(s, encoding='utf-8-sig')

p = root / 'interface/koch_portraits.gfx'
s = p.read_text(encoding='utf-8')
if 'GFX_portrait_KOCH_B03_chetkiye_patsanchiki' not in s:
    s = s.replace('spriteTypes = {', '''spriteTypes = {
    spriteType = {
        name = "GFX_portrait_KOCH_B03_chetkiye_patsanchiki"
        texturefile = "gfx/leaders/B03/koch_chetkiye_patsanchiki.dds"
    }''', 1)
p.write_text(s, encoding='utf-8')

portrait_src = Path('C:/Users/qacdf/AppData/Local/Temp/codex-clipboard-97934244-d484-4541-95af-118e99fc548c.png')
flag_src = Path('C:/Users/qacdf/AppData/Local/Temp/codex-clipboard-12d9573d-66a5-4ae8-bd00-323a7b49e75a.png')
d = root / 'gfx/leaders/B03'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2(portrait_src, d / 'koch_chetkiye_patsanchiki_source.png')
# Pad instead of cropping, preserving both faces in this group portrait.
im = ImageOps.pad(Image.open(portrait_src).convert('RGB'), (156,210), method=Image.Resampling.LANCZOS, color=(25,30,30))
im.save(d / 'koch_chetkiye_patsanchiki.dds')
im.save(d / 'koch_chetkiye_patsanchiki_preview.png')
d = root / 'gfx/flags/source'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2(flag_src, d / 'koch_B03.png')
im = Image.open(flag_src).convert('RGB')
for folder, size in [('',(82,52)), ('medium',(41,26)), ('small',(10,7))]:
    d = root / 'gfx/flags' / folder
    d.mkdir(parents=True, exist_ok=True)
    flag = im.resize(size, Image.Resampling.LANCZOS)
    flag.save(d / 'B03.tga')
    flag.save(d / 'B03_neutrality.tga')
print('Configured B03: states 833 and 400; capital 833; leader, portrait, flags and Aquamarine.')
