"""Create map overrides for the initial Peterhof province transfer."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')
MOVED = {6174, 79, 11068}

if __name__ == '__main__':
    target = ROOT / 'map'
    target.mkdir(exist_ok=True)
    definition_path = target / 'definition.csv'
    buildings_path = target / 'buildings.txt'
    if definition_path.exists() or buildings_path.exists():
        raise SystemExit('Existing map overrides found; merge changes rather than overwrite.')
    definition = (GAME / 'map/definition.csv').read_text(encoding='utf-8-sig')
    lines = definition.splitlines(keepends=True)
    color_to_id = {}
    for index, line in enumerate(lines):
        fields = line.strip().split(';')
        if len(fields) < 8 or not fields[0].isdigit():
            continue
        province = int(fields[0])
        color_to_id[tuple(map(int, fields[1:4]))] = province
        if province == 6174:
            assert fields[6] == 'forest', fields
            fields[6] = 'urban'
            lines[index] = ';'.join(fields) + '\n'
    definition_path.write_text(''.join(lines), encoding='utf-8')
    # Building coordinates use a bottom-left origin; bitmap rows start at top-left.
    with Image.open(GAME / 'map/provinces.bmp') as image:
        image = image.convert('RGB')
        height = image.height
        pixels = image.load()
        building_lines = (GAME / 'map/buildings.txt').read_text(encoding='utf-8-sig').splitlines(keepends=True)
        changes = []
        for index, line in enumerate(building_lines):
            fields = line.strip().split(';')
            if len(fields) < 7 or fields[0] != '195':
                continue
            x, z = int(float(fields[2])), int(float(fields[4]))
            province = color_to_id.get(pixels[x, height - 1 - z])
            if province in MOVED:
                fields[0] = '208'
                building_lines[index] = ';'.join(fields) + '\n'
                changes.append((fields[1], province))
        if changes:
            buildings_path.write_text(''.join(building_lines), encoding='utf-8')
        print(f'Province 6174 terrain: urban; moved building positions: {changes}')
