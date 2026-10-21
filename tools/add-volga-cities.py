from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
cities = {
    11356: ('Новочебоксарск', 'Novocheboksarsk', 1),
    9373: ('Канаш', 'Kanash', 1),
    11243: ('Иннополис', 'Innopolis', 1),
    9514: ('Чистополь', 'Chistopol', 1),
    3214: ('Набережные Челны', 'Naberezhnye Chelny', 10),
    3365: ('Мамадыш', 'Mamadysh', 1),
    11344: ('Арзамас', 'Arzamas', 1),
}
found = set()
for p in (root / 'history/states').glob('*.txt'):
    s = p.read_text(encoding='utf-8-sig')
    clean = re.sub(r'#.*', '', s)
    m = re.search(r'\bprovinces\s*=\s*\{([^}]+)\}', clean)
    if not m:
        continue
    hit = set(cities).intersection(map(int, re.findall(r'\d+', m[1])))
    if not hit:
        continue
    for pid in sorted(hit):
        assert pid not in found, pid
        found.add(pid)
        points = cities[pid][2]
        pattern = r'(\bvictory_points\s*=\s*\{\s*'+str(pid)+r'\s+)\d+'
        if re.search(pattern, s):
            s = re.sub(pattern, lambda m: m[1]+str(points), s)
        else:
            s, n = re.subn(r'(\bhistory\s*=\s*\{)', lambda m: m[1]+f'\n        victory_points = {{ {pid} {points} }}', s, count=1)
            assert n == 1, p
    p.write_text(s, encoding='utf-8')
    print(p.name, sorted(hit))
assert found == set(cities)

for lang, index in [('russian', 0), ('english', 1)]:
    p = root / f'localisation/{lang}/koch_victory_points_l_{lang}.yml'
    s = p.read_text(encoding='utf-8-sig')
    for pid, entry in cities.items():
        line = f' VICTORY_POINTS_{pid}:0 "{entry[index]}"'
        pattern = r'^\s*VICTORY_POINTS_'+str(pid)+r':[^\n]*'
        if re.search(pattern, s, re.M):
            s = re.sub(pattern, line, s, flags=re.M)
        else:
            s += line+'\n'
    p.write_text(s, encoding='utf-8-sig')

p = root / 'map/definition.csv'
lines = p.read_text(encoding='utf-8-sig').splitlines()
changed = set()
for i, line in enumerate(lines):
    fields = line.split(';')
    if fields[0].isdigit() and int(fields[0]) in cities:
        assert fields[4] == 'land', fields
        fields[6] = 'urban'
        lines[i] = ';'.join(fields)
        changed.add(int(fields[0]))
assert changed == set(cities)
p.write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('Seven cities localized; province terrain set to urban.')
