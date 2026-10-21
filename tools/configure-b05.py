from pathlib import Path
import re
from PIL import Image

root = Path(__file__).resolve().parents[1]
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')
def write(path, text):
    (root / path).write_text(text, encoding='utf-8')

write('history/countries/B05 - koch.txt', '''capital = 251
set_politics = {
    ruling_party = communism
    elections_allowed = no
}
set_popularities = {
    democratic = 0
    fascism = 10
    communism = 90
    neutrality = 0
}
recruit_character = KOCH_B05_danil_kozlov
''')
write('common/characters/koch_B05.txt', '''characters = {
    KOCH_B05_danil_kozlov = {
        name = KOCH_B05_danil_kozlov
        country_leader = {
            ideology = marxism
            expire = "2100.1.1.1"
            id = -1
        }
    }
}
''')
p = root / 'common/countries/koch_B05.txt'
s = re.sub(r'color\s*=\s*\{[^}]*\}', 'color = { 205 92 92 }', p.read_text(encoding='utf-8'))
p.write_text(s, encoding='utf-8')
p = root / 'common/countries/colors.txt'
s = p.read_text(encoding='utf-8')
block = 'B05 = {\n    color = rgb { 205 92 92 }\n    color_ui = rgb { 205 92 92 }\n}\n'
if not re.search(r'\bB05\s*=', s):
    p.write_text(s + '\n' + block, encoding='utf-8')
for sid in (250,251,401,829,239):
    p = next(p for p in (root / 'history/states').glob(f'{sid}*.txt') if re.search(r'\bid\s*=\s*'+str(sid)+r'\b', p.read_text(encoding='utf-8')))
    s = p.read_text(encoding='utf-8')
    owners = re.findall(r'\b(?:owner|controller|add_core_of)\s*=\s*(\w+)', s)
    assert all(tag == 'B05' for tag in owners), (p,owners)
    if not owners:
        s = re.sub(r'(\bhistory\s*=\s*\{)', r'\1\n        owner = B05\n        controller = B05\n        add_core_of = B05', s, count=1)
    p.write_text(s, encoding='utf-8')
p = root / 'common/bookmarks/koch_empty_world.txt'
s = p.read_text(encoding='utf-8')
s = re.sub(r'("B05"\s*=\s*\{[^}]*?ideology\s*=\s*)\w+', r'\1communism', s)
p.write_text(s, encoding='utf-8')

for lang, name, desc in [
    ('russian', 'Данил Напопник Козлов', 'Самарская Народная Республика контролирует регионы 250, 251, 401, 829 и 239. Столица — Самара. Страну возглавляет Данил Напопник Козлов. Поддержка партий: демократия — 0%, фашизм — 10%, коммунизм — 90%, авторитаризм — 0%.'),
    ('english', 'Danil Napopnik Kozlov', 'Samara People’s Republic controls states 250, 251, 401, 829 and 239. Its capital is Samara. Danil Napopnik Kozlov leads the country. Party support: democracy — 0%, fascism — 10%, communism — 90%, non-aligned — 0%.'),
]:
    p = root / f'localisation/{lang}/koch_countries_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig')
    s = re.sub(r' KOCH_B05_DESC:0 .*', f' KOCH_B05_DESC:0 "{desc}"', s)
    key = 'KOCH_B05_danil_kozlov'
    if not re.search(r'^\s*'+key+r':', s, re.M):
        s += f'\n {key}:0 "{name}"\n'
    p.write_text(s, encoding='utf-8-sig')

im = Image.open(game / 'gfx/flags/KOR_communism.tga').convert('RGB')
d = root / 'gfx/flags/source'
d.mkdir(parents=True, exist_ok=True)
im.save(d / 'koch_B05.png')
for folder, size in [('',(82,52)), ('medium',(41,26)), ('small',(10,7))]:
    d = root / 'gfx/flags' / folder
    d.mkdir(parents=True, exist_ok=True)
    flag = im.resize(size, Image.Resampling.LANCZOS)
    flag.save(d / 'B05.tga')
    flag.save(d / 'B05_communism.tga')
print('Configured B05: states 250, 251, 401, 829, 239; capital 251; DPRK flags; IndianRed.')
