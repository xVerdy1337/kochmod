from pathlib import Path
import re
import shutil
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1]
def write(path, text):
    (root / path).write_text(text, encoding='utf-8')

write('history/countries/B01 - koch.txt', '''capital = 256
set_politics = {
    ruling_party = neutrality
    elections_allowed = no
}
set_popularities = {
    democratic = 20
    fascism = 25
    communism = 20
    neutrality = 35
}
recruit_character = KOCH_B01_alexey_kalkin
''')
write('common/characters/koch_B01.txt', '''characters = {
    KOCH_B01_alexey_kalkin = {
        name = KOCH_B01_alexey_kalkin
        portraits = {
            civilian = {
                large = GFX_portrait_KOCH_B01_alexey_kalkin
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
p = root / 'common/countries/koch_B01.txt'
p.write_text(re.sub(r'color\s*=\s*\{[^}]*\}', 'color = { 245 170 35 }', p.read_text(encoding='utf-8')), encoding='utf-8')
p = root / 'common/countries/colors.txt'
s = p.read_text(encoding='utf-8')
if not re.search(r'\bB01\s*=', s):
    p.write_text(s + '\nB01 = {\n    color = rgb { 245 170 35 }\n    color_ui = rgb { 245 170 35 }\n}\n', encoding='utf-8')
for sid in (256,252,255):
    p = next((root / 'history/states').glob(f'{sid}-*.txt'))
    s = p.read_text(encoding='utf-8')
    assert not re.search(r'\b(owner|controller|add_core_of)\s*=', s), p
    s = re.sub(r'(\bhistory\s*=\s*\{)', r'\1\n        owner = B01\n        controller = B01\n        add_core_of = B01', s, count=1)
    p.write_text(s, encoding='utf-8')

for lang, old, new, name, desc in [
    ('russian', 'Чувашский Бурмалдат', 'Чебоксарский Бурмалдат', 'Алексей Калькин', 'Чебоксарский Бурмалдат контролирует регионы 256, 252 и 255. Столица — Чебоксары. Страну возглавляет Алексей Калькин. Поддержка партий: демократия — 20%, фашизм — 25%, коммунизм — 20%, авторитаризм — 35%.'),
    ('english', 'Chuvash Burmaldat', 'Cheboksary Burmaldat', 'Alexey Kalkin', 'Cheboksary Burmaldat controls states 256, 252 and 255. Its capital is Cheboksary. Alexey Kalkin leads the country. Party support: democracy — 20%, fascism — 25%, communism — 20%, non-aligned — 35%.'),
]:
    p = root / f'localisation/{lang}/koch_countries_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig').replace(old, new)
    s = re.sub(r' KOCH_B01_DESC:0 .*', f' KOCH_B01_DESC:0 "{desc}"', s)
    s += f'\n KOCH_B01_alexey_kalkin:0 "{name}"\n'
    p.write_text(s, encoding='utf-8-sig')

p = root / 'interface/koch_portraits.gfx'
s = p.read_text(encoding='utf-8')
s = s.replace('spriteTypes = {', '''spriteTypes = {
    spriteType = {
        name = "GFX_portrait_KOCH_B01_alexey_kalkin"
        texturefile = "gfx/leaders/B01/koch_alexey_kalkin.dds"
    }''', 1)
p.write_text(s, encoding='utf-8')

portrait_src = Path('C:/Users/qacdf/AppData/Local/Temp/codex-clipboard-85af5f96-250e-46dd-b36b-da81df2e72a1.png')
flag_src = Path('C:/Users/qacdf/AppData/Local/Temp/codex-clipboard-dcbcff2f-52b4-4466-86f7-b3c4e48d0c45.png')
d = root / 'gfx/leaders/B01'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2(portrait_src, d / 'koch_alexey_kalkin_source.png')
im = ImageOps.fit(Image.open(portrait_src).convert('RGB'), (156,210), method=Image.Resampling.LANCZOS)
im.save(d / 'koch_alexey_kalkin.dds')
im.save(d / 'koch_alexey_kalkin_preview.png')
d = root / 'gfx/flags/source'
d.mkdir(parents=True, exist_ok=True)
shutil.copy2(flag_src, d / 'koch_B01.png')
im = Image.open(flag_src).convert('RGB')
for folder, size in [('',(82,52)), ('medium',(41,26)), ('small',(10,7))]:
    d = root / 'gfx/flags' / folder
    d.mkdir(parents=True, exist_ok=True)
    im.resize(size, Image.Resampling.LANCZOS).save(d / 'B01.tga')
print('Configured B01: states 256, 252, 255; capital 256; portrait and three flags.')
