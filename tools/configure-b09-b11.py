"""Configure B09 (Круглое государство, state 95) and create B11 (Подиковая республика, state 66)."""
from pathlib import Path
import re
import shutil
import sys
from PIL import Image

root = Path(__file__).resolve().parents[1]
img_dir = Path(sys.argv[1])  # directory with 1.png (Mark P) and 2.png (Artur Kruglyy)

RU = {
    'B09': 'Круглое государство',
    'B11': 'Подиковая республика',
}
EN = {
    'B09': 'Round State',
    'B11': 'Podik Republic',
}
SUFFIXES = ['', '_DEF', '_ADJ'] + [f'_{i}{e}' for i in ('neutrality', 'democratic', 'fascism', 'communism') for e in ('', '_DEF', '_ADJ')]


def write(path, text, bom=False):
    (root / path).write_text(text, encoding='utf-8-sig' if bom else 'utf-8')


def history(capital, char):
    return f'''capital = {capital}
set_politics = {{
    ruling_party = democratic
    elections_allowed = yes
}}
set_popularities = {{
    democratic = 65
    fascism = 5
    communism = 5
    neutrality = 25
}}
recruit_character = {char}
'''


def character(char, tag, slug):
    return f'''characters = {{
    {char} = {{
        name = {char}
        portraits = {{
            civilian = {{
                large = GFX_portrait_KOCH_{tag}_{slug}
            }}
        }}
        country_leader = {{
            ideology = liberalism
            expire = "2100.1.1.1"
            id = -1
        }}
    }}
}}
'''


people = {
    'B09': ('KOCH_B09_artur_kruglyy', 'artur_kruglyy', 95, '2.png', (110, 0, 550, 592), 'Артур Круглый', 'Artur Kruglyy', 'Гродно', 'Grodno'),
    'B11': ('KOCH_B11_mark_p', 'mark_p', 66, '1.png', (149, 60, 449, 464), 'Марк П', 'Mark P', 'Вроцлав', 'Wroclaw'),
}

for tag, (char, slug, state, img, box, leader_ru, leader_en, cap_ru, cap_en) in people.items():
    write(f'history/countries/{tag} - koch.txt', history(state, char))
    write(f'common/characters/koch_{tag}.txt', character(char, tag, slug))
    d = root / f'gfx/leaders/{tag}'
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(img_dir / img, d / f'koch_{slug}_source.png')
    im = Image.open(img_dir / img).convert('RGB').crop(box).resize((156, 210), Image.Resampling.LANCZOS)
    im.save(d / f'koch_{slug}.dds')
    im.save(d / f'koch_{slug}_preview.png')

    p = root / 'interface/koch_portraits.gfx'
    s = p.read_text(encoding='utf-8')
    if f'GFX_portrait_KOCH_{tag}_{slug}' not in s:
        s = s.replace('spriteTypes = {', f'''spriteTypes = {{
    spriteType = {{
        name = "GFX_portrait_KOCH_{tag}_{slug}"
        texturefile = "gfx/leaders/{tag}/koch_{slug}.dds"
    }}''', 1)
        p.write_text(s, encoding='utf-8')

    p = root / next(Path(root / 'history/states').glob(f'{state}-*.txt')).relative_to(root)
    s = p.read_text(encoding='utf-8')
    if 'owner' not in s:
        s = re.sub(r'(\bhistory\s*=\s*\{)', rf'\1\n\t\towner = {tag}\n\t\tcontroller = {tag}\n\t\tadd_core_of = {tag}', s, count=1)
        p.write_text(s, encoding='utf-8')

colors = {'B09': (161, 117, 185), 'B11': (214, 138, 62)}
p = root / 'common/countries/colors.txt'
s = p.read_text(encoding='utf-8')
for tag, c in colors.items():
    if not re.search(rf'\b{tag}\s*=', s):
        s += f'\n{tag} = {{\n    color = rgb {{ {c[0]} {c[1]} {c[2]} }}\n    color_ui = rgb {{ {c[0]} {c[1]} {c[2]} }}\n}}\n'
    p2 = root / f'common/countries/koch_{tag}.txt'
    p2.write_text(
        'graphical_culture = eastern_european_gfx\ngraphical_culture_2d = eastern_european_2d\n'
        f'color = {{ {c[0]} {c[1]} {c[2]} }}\n', encoding='utf-8')
p.write_text(s, encoding='utf-8')

p = root / 'common/country_tags/koch_countries.txt'
s = p.read_text(encoding='utf-8')
if 'B11' not in s:
    s = s.rstrip('\n') + '\nB11 = "countries/koch_B11.txt"\n'
    p.write_text(s, encoding='utf-8')

desc = {
    'ru': {
        'B09': 'Круглое государство контролирует регион 95. Столица — Гродно. Страну возглавляет Артур Круглый. Поддержка партий: демократия — 65%, фашизм — 5%, коммунизм — 5%, нейтралитет — 25%.',
        'B11': 'Подиковая республика контролирует регион 66. Столица — Вроцлав. Страну возглавляет Марк П. Поддержка партий: демократия — 65%, фашизм — 5%, коммунизм — 5%, нейтралитет — 25%.',
    },
    'en': {
        'B09': 'The Round State controls state 95. Its capital is Grodno and its leader is Artur Kruglyy. Party support: democracy 65%, fascism 5%, communism 5%, neutrality 25%.',
        'B11': 'The Podik Republic controls state 66. Its capital is Wroclaw and its leader is Mark P. Party support: democracy 65%, fascism 5%, communism 5%, neutrality 25%.',
    },
}
for lang, names, code in (('russian', RU, 'ru'), ('english', EN, 'en')):
    p = root / f'localisation/{lang}/koch_countries_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig')
    s = re.sub(r'^ B09(_\w+)?:0 .*\n', '', s, flags=re.M)
    s = re.sub(r'^ KOCH_B09_DESC:0 .*\n', '', s, flags=re.M)
    for tag in ('B09', 'B11'):
        if tag == 'B11':
            s = re.sub(rf'^ {tag}(_\w+)?:0 .*\n', '', s, flags=re.M)
            s = re.sub(rf'^ KOCH_{tag}_DESC:0 .*\n', '', s, flags=re.M)
        for suf in SUFFIXES:
            s += f' {tag}{suf}:0 "{names[tag]}"\n'
        s += f' KOCH_{tag}_DESC:0 "{desc[code][tag]}"\n'
    for tag, (char, _, _, _, _, lru, len_, _, _) in people.items():
        s = re.sub(rf'^ {char}:0 .*\n', '', s, flags=re.M)
        s += f' {char}:0 "{lru if code == "ru" else len_}"\n'
    p.write_text(s, encoding='utf-8-sig')

    p = root / f'localisation/replace/koch_map_names_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig')
    cap = {9570: people['B11'][7 if code == 'ru' else 8], 3393: people['B09'][7 if code == 'ru' else 8]}
    for vp, name in cap.items():
        s = re.sub(rf'^ VICTORY_POINTS_{vp}:0 .*\n', '', s, flags=re.M)
        s += f' VICTORY_POINTS_{vp}:0 "{name}"\n'
    p.write_text(s, encoding='utf-8-sig')

p = root / 'common/bookmarks/koch_empty_world.txt'
s = p.read_text(encoding='utf-8')
s = s.replace('''            minor = yes
            history = "KOCH_B09_DESC"
            ideology = neutrality''', '''            minor = yes
            history = "KOCH_B09_DESC"
            ideology = democratic''')
if 'B11' not in s:
    s = s.replace('''        "B08" = {''', '''        "B11" = {
            history = "KOCH_B11_DESC"
            ideology = democratic
            version = base_game
        }
        "B08" = {''')
p.write_text(s, encoding='utf-8')
print('Configured B09 (state 95) and B11 (state 66).')
