"""Create the initial country skeletons. Refuses to overwrite existing country files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = [
    ('B01', 'Чебоксарский Бурмалдат', 'Cheboksary Burmaldat', (245, 170, 35)),
    ('B02', 'Петергофское Княжество', 'Principality of Peterhof', (83, 125, 184)),
    ('B03', 'Волжская коммуна', 'Volga Commune', (82, 82, 92)),
    ('B04', 'Казанская Республика', 'Kazan Republic', (53, 145, 99)),
    ('B05', 'Самарская Народная Республика', "Samara People's Republic", (174, 60, 90)),
    ('B06', 'Гомельские Болота', 'Gomel Marshes', (102, 120, 59)),
    ('B07', 'Московская Администрация', 'Moscow Administration', (168, 0, 44)),
    ('B08', 'ИТМО', 'ITMO', (73, 170, 194)),
    ('B09', 'Наминальное Гродно', 'Naminal Grodno', (161, 117, 185)),
    ('B10', 'Анархия', 'Anarchy', (52, 48, 43)),
]

def build_files():
    output = {}
    tags = ['# Country skeletons: no territory or capital assigned.']
    ru = ['l_russian:']
    en = ['l_english:']
    entries = []
    for tag, name, english, color in COUNTRIES:
        tags.append(f'{tag} = "countries/koch_{tag}.txt"')
        output[f'common/countries/koch_{tag}.txt'] = (
            'graphical_culture = eastern_european_gfx\n'
            'graphical_culture_2d = eastern_european_2d\n'
            f'color = {{ {color[0]} {color[1]} {color[2]} }}\n'
        )
        output[f'history/countries/{tag} - koch.txt'] = (
            '# Skeleton only. Capital, territory, leaders and content are intentionally unset.\n'
            '# Neutrality is a technical placeholder, not the final political design.\n'
            'set_politics = {\n    ruling_party = neutrality\n    elections_allowed = no\n}\n'
            'set_popularities = { neutrality = 100 }\n'
        )
        for suffix in ['', '_DEF', '_ADJ'] + [
            f'_{ideology}{ending}'
            for ideology in ('neutrality', 'democratic', 'fascism', 'communism')
            for ending in ('', '_DEF', '_ADJ')
        ]:
            ru.append(f' {tag}{suffix}:0 "{name}"')
            en.append(f' {tag}{suffix}:0 "{english}"')
        ru.append(f' KOCH_{tag}_DESC:0 "{name}. Заготовка страны: территория, столица и игровой контент пока не заданы."')
        en.append(f' KOCH_{tag}_DESC:0 "{english}. Country skeleton: territory, capital and gameplay content are not yet configured."')
        if tag == 'B10':
            continue  # Country exists, but is not offered by this scenario.
        minor_line = '            minor = yes\n' if tag in ('B06', 'B08', 'B09') else ''
        entries.append(
            f'        "{tag}" = {{\n'
            + minor_line +
            f'            history = "KOCH_{tag}_DESC"\n'
            '            ideology = neutrality\n'
            '            version = base_game\n'
            '        }'
        )
    output['common/country_tags/koch_countries.txt'] = '\n'.join(tags) + '\n'
    output['localisation/russian/koch_countries_l_russian.yml'] = '\n'.join(ru) + '\n'
    output['localisation/english/koch_countries_l_english.yml'] = '\n'.join(en) + '\n'
    order = ('B01', 'B02', 'B03', 'B04', 'B05', 'B07', 'B06', 'B08', 'B09')
    entries.sort(key=lambda entry: order.index(entry.split('"')[1]))
    return output, '\n'.join(entries)

if __name__ == '__main__':
    output, entries = build_files()
    existing = [name for name in output if (ROOT / name).exists()]
    if existing:
        raise SystemExit(f'Refusing to overwrite country files: {existing}')
    bookmark_path = ROOT / 'common/bookmarks/koch_empty_world.txt'
    bookmark = bookmark_path.read_text(encoding='utf-8')
    for default in ('yes', 'no'):
        needle = f'        default = {default}\n'
        if bookmark.count(needle) != 1:
            raise SystemExit(f'Unexpected bookmark layout: {default}')
        bookmark = bookmark.replace(needle, needle + '        scrollable_country_list = yes\n        sort_unplayed_first = no\n' + entries + '\n')
    for name, content in output.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8-sig' if name.endswith('.yml') else 'utf-8')
    bookmark_path.write_text(bookmark, encoding='utf-8')
    print(f'Created {len(COUNTRIES)} country skeletons; added 6 primary and 3 minor entries to both bookmarks.')
