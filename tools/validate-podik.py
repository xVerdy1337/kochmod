"""Structural and reference checks for Podik content; not an engine substitute.

Usage: python tools/validate-podik.py [--game PATH]
"""
from pathlib import Path
import argparse
import collections
import itertools
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
args = argparse.ArgumentParser()
args.add_argument('--game', type=Path, default=Path('D:/SteamLibrary/steamapps/common/Hearts of Iron IV'))
game = args.parse_args().game
root = Path(__file__).resolve().parents[1]
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


def parse(path):
    """Preserve repeated keys (prerequisites, focus refs, options) and operators."""
    text = path.read_text(encoding='utf-8-sig')
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}]|[<>!=]=?|[^\s{}=<>!#"]+', text)
    tokens = [t for t in tokens if not t.startswith('#')]
    index = 0

    def block(nested=False):
        nonlocal index
        result = []
        while index < len(tokens):
            key = tokens[index]
            index += 1
            if key == '}':
                if not nested:
                    raise ValueError(f'{path}: unexpected closing brace')
                return result
            if key == '{':
                raise ValueError(f'{path}: unexpected opening brace')
            if index == len(tokens) or tokens[index] not in ('=', '>', '<', '>=', '<=', '!='):
                result.append((None, None, key.strip('"')))
                continue
            op = tokens[index]
            index += 1
            value = tokens[index]
            index += 1
            value = block(True) if value == '{' else value.strip('"')
            result.append((key, op, value))
        if nested:
            raise ValueError(f'{path}: missing closing brace')
        return result

    return block()


def values(block, key):
    return [v for k, _, v in block if k == key]


def first(block, key, default=None):
    return next(iter(values(block, key)), default)


def walk(block):
    for k, op, v in block:
        yield k, op, v
        if isinstance(v, list):
            yield from walk(v)


paths = [p for folder in ('common', 'events', 'history') for p in (root/folder).rglob('*.txt')
         if 'podik' in p.name.lower() or p.name in ('koch_B11.txt', 'B11 - koch.txt', 'KOCH_B11_militia.txt')]
parsed = {}
for p in paths:
    try:
        parsed[p.relative_to(root).as_posix()] = parse(p)
    except (ValueError, IndexError) as error:
        errors.append(str(error))

tree = first(parsed['common/national_focus/koch_podik.txt'], 'focus_tree')
focus_blocks = values(tree, 'focus')
focus = {first(f, 'id'): f for f in focus_blocks}
require(len(focus) == len(focus_blocks) == 101, 'Expected 101 unique focus IDs')
requirements = {fid: [set(values(b, 'focus')) for b in values(f, 'prerequisite')] for fid, f in focus.items()}
exclusions = {fid: set(itertools.chain.from_iterable(values(b, 'focus') for b in values(f, 'mutually_exclusive'))) for fid, f in focus.items()}
positions = {}
for fid, f in focus.items():
    pos = (int(first(f, 'x')), int(first(f, 'y')))
    require(pos not in positions, f'Overlapping nodes: {fid} and {positions.get(pos)}')
    positions[pos] = fid
    require(first(f, 'cost') in ('1', '2', '3', '5', '10'), f'Wrong duration: {fid}')
    require(bool(first(f, 'completion_reward')), f'Empty reward: {fid}')
    for dep in set().union(*requirements[fid], exclusions[fid]):
        require(dep in focus, f'Unknown dependency: {fid} -> {dep}')
    for other in exclusions[fid]:
        require(fid in exclusions.get(other, set()), f'Asymmetric exclusivity: {fid} -> {other}')
    for dep in set().union(*requirements[fid]):
        if dep in focus:
            require(int(first(focus[dep], 'y')) < pos[1], f'Non-descending link/cycle: {dep} -> {fid}')
panel = first(tree, 'continuous_focus_position')
require(int(first(panel, 'y')) >= 2500, 'Continuous focus panel intrudes into tree')
# Conservatively keep each long incoming vertical segment clear of other icons.
for fid, groups in requirements.items():
    x, y = int(first(focus[fid], 'x')), int(first(focus[fid], 'y'))
    for dep in set().union(*groups):
        py = int(first(focus[dep], 'y'))
        for (nx, ny), node in positions.items():
            require(not (nx == x and py < ny < y), f'Incoming line to {fid} passes through {node}')

# Enumerate all 10 combinations of political sub-branches and final governments.
prefix = 'KOCH_B11_'
def full(name):
    return prefix+name

routes = []
for sub, ending in itertools.product(('BAN_DOUBT', 'SACRED_MANUAL'), ('ETERNAL_EMPIRE', 'PODIK_ABOVE_STATE')):
    routes.append(('cult', [full('PODIK_PATH'), full(sub), full(ending)]))
for sub, ending in itertools.product(('VAMOS_BLAMES', 'GAMOS_BLAMES'), ('GREAT_COMPROMISE', 'SINGLE_CHAIR', 'TWO_PRESIDENTS')):
    routes.append(('council', [full('COUNCIL_PATH'), full(sub), full(ending)]))
for name, choices in routes:
    blocked = set().union(*(exclusions[c] for c in choices))
    done = set()
    while True:
        more = {fid for fid in focus if fid not in done|blocked
                and not exclusions[fid]&done
                and all(group&done for group in requirements[fid])}
        # Keep the independent friendship/confrontation branch deterministic.
        more.discard(full('ACE_NOT_OUR_BUSINESS'))
        if not more:
            break
        done |= more
    require(set(choices) <= done, f'Unreachable route: {choices}')
    require(full('FINAL_MEMO') in done, f'Economy unreachable: {choices}')
require(requirements[full('EMERGENCY_LOGISTICS')] == [{full('NEW_EPOCH')}], 'Economy depends on Grodno')

event_blocks = values(parsed['events/koch_podik.txt'], 'country_event')
events = {first(e, 'id'): e for e in event_blocks}
require(len(events) == len(event_blocks) == 101, 'Expected 101 unique events')
# Hidden timeout callbacks for the Prophet superevent live in a manual file
# (not part of the 101 story events); they are valid country_event targets.
superevent_ids = {first(e, 'id') for e in values(parsed['events/koch_podik_superevent.txt'], 'country_event')}
require(len(superevent_ids) == 2, 'Expected 2 superevent timeout events')
ideas = first(first(parsed['common/ideas/koch_podik.txt'], 'ideas'), 'country')
idea_ids = {k for k, _, _ in ideas}
require(len(idea_ids) == 53, 'Expected 53 spirits')
decisions = parsed['common/decisions/koch_podik.txt']
categories = parsed['common/decisions/categories/koch_podik.txt']
decision_ids = {key for _, _, cat in decisions for key, _, _ in cat}
require(len(categories) == 6 and len(decision_ids) == 33, 'Expected 6 categories and 33 decisions')
require({k for k, _, _ in decisions} == {k for k, _, _ in categories}, 'Decision category not defined')
opinions = {k for k, _, _ in first(parsed['common/opinion_modifiers/koch_podik.txt'], 'opinion_modifiers')}

loc = {}
for p in (root/'localisation/russian').glob('*.yml'):
    text = p.read_text(encoding='utf-8-sig')
    for key, val in re.findall(r'^\s*([^\s:#]+):\d*\s+"(.*)"\s*$', text, re.M):
        loc[key] = val
own_loc = root/'localisation/russian/koch_podik_l_russian.yml'
require(own_loc.read_bytes().startswith(b'\xef\xbb\xbf'), 'Localisation must use UTF-8 BOM')
own_keys = re.findall(r'^\s*([^\s:#]+):\d*\s+', own_loc.read_text(encoding='utf-8-sig'), re.M)
require(len(own_keys) == len(set(own_keys)), 'Duplicate Podik localisation keys')
for line in own_loc.read_text(encoding='utf-8-sig').splitlines():
    if line.strip() and not line.lstrip().startswith('#') and line.strip() != 'l_russian:':
        require(bool(re.fullmatch(r'\s+[^\s:#]+:\d+\s+"(?:\\.|[^"\\])*"\s*', line)), f'Malformed localisation line: {line[:100]}')
needed = set()


def check_visible_conditions(block):
    for key, _, value in block:
        if key in ('has_country_flag', 'check_variable'):
            require(False, f'Unlabelled player-facing condition: {key} = {value}')
        elif isinstance(value, list) and key not in ('custom_override_tooltip', 'custom_trigger_tooltip'):
            check_visible_conditions(value)


for block in (tree, decisions):
    for key, _, value in walk(block):
        if key == 'available':
            check_visible_conditions(value)
for fid in focus:
    needed |= {fid, fid+'_desc'}
for key in idea_ids|decision_ids:
    needed |= {key, key+'_desc'}
for key, _, _ in categories:
    needed |= {key, key+'_desc'}
for ev in events.values():
    needed |= {first(ev, 'title'), first(ev, 'desc')}
    options = values(ev, 'option')
    require(len(options) > 0, f'No options: {first(ev, "id")}')
    needed |= {first(o, 'name') for o in options}
    require(any(not first(o, 'trigger') for o in options), f'No unconditional fallback: {first(ev, "id")}')

sprites = set()
for base in (game, root):
    for p in (base/'interface').rglob('*.gfx'):
        sprites.update(re.findall(r'\bname\s*=\s*"?([^\s"{}]+)', p.read_text(encoding='utf-8-sig', errors='replace')))
for filename, block in parsed.items():
    for key, op, value in walk(block):
        if key == 'country_event' and isinstance(value, list):
            require(first(value, 'id') in events or first(value, 'id') in superevent_ids, f'Unknown event in {filename}: {first(value, "id")}')
        if key in ('add_ideas', 'remove_ideas') and isinstance(value, str) and value.startswith('KOCH_'):
            require(value in idea_ids, f'Unknown spirit: {value}')
        if key == 'add_timed_idea':
            require(first(value, 'idea') in idea_ids, f'Unknown timed spirit: {value}')
        if key == 'add_opinion_modifier':
            require(first(value, 'modifier') in opinions, f'Unknown opinion modifier: {value}')
        if key in ('custom_effect_tooltip', 'tooltip', 'not_tooltip', 'localization_key', 'name', 'long_name') and isinstance(value, str) and value.startswith('KOCH_') and not (key == 'name' and '/scripted_localisation/' in filename):
            needed.add(value)
        if key == 'set_cosmetic_tag':
            needed |= {value+'_neutrality', value+'_neutrality_DEF', value+'_neutrality_ADJ'}
        if key == 'icon':
            sprite = value if value.startswith('GFX_') else ('GFX_decision_category_' if '/categories/' in filename else 'GFX_decision_')+value
            require(sprite in sprites, f'Missing icon sprite: {value}')
        if key == 'picture':
            sprite = value if value.startswith('GFX_') else 'GFX_idea_'+value
            require(sprite in sprites, f'Missing picture sprite: {value}')
        if key == 'large' and value.startswith('gfx/'):
            require((game/value).is_file() or (root/value).is_file(), f'Missing portrait: {value}')
        if key == 'large' and value.startswith('GFX_'):
            require(value in sprites, f'Missing portrait sprite: {value}')
        if key == 'add_state_claim':
            require(value != '3393', 'Province ID used for state claim')
for key in sorted(needed):
    require(key in loc and bool(loc.get(key)), f'Missing Russian localisation: {key}')
require(loc.get(full('PROTECT_ACE')) == 'Охранять туз Артура', 'Required exact focus name changed')
require(loc.get(full('mark_recognized')) == 'Откровение Марка признано', 'Raw prophet flag lacks a readable fallback')
dynamic_texts = {first(b, 'name') for b in values(parsed['common/scripted_localisation/koch_podik.txt'], 'defined_text')}
for name in re.findall(r'\[(KOCH_B11_\w+)\]', loc['koch_podik_cult_desc']):
    require(name in dynamic_texts, f'Undefined dynamic charge text: {name}')

# Execute the actual variable effects and limits in the game's DSL for charge
# hysteresis and complementary council influence, including broken-device guards.
effects = dict((k, v) for k, _, v in parsed['common/scripted_effects/koch_podik.txt'])
class State:
    def __init__(self):
        self.vars = collections.defaultdict(float)
        self.flags = set()
        self.ideas = set()
        self.events = []
        self.focuses = set()
        self.war = False
        self.leader = full('council')
        self.metrics = collections.defaultdict(float)
        self.flag_days = {}
        self.scheduled = []
        self.countries = {}
        self.opinions = collections.defaultdict(float)
        self.enemies = set()

    def check(self, block):
        checks = []
        for k, op, v in block:
            if k == 'check_variable':
                if first(v, 'var') is not None:
                    var, val = first(v, 'var'), float(first(v, 'value'))
                    cmp = first(v, 'compare', 'equals')
                else:
                    var, cmp, val = v[0]
                    val = float(val)
                a = self.vars[var]
                checks.append({'<': a < val, '>': a > val, '=': a == val,
                    'less_than': a < val, 'less_than_or_equals': a <= val,
                    'greater_than': a > val, 'greater_than_or_equals': a >= val,
                    'equals': a == val, 'not_equals': a != val}[cmp])
            elif k == 'has_country_flag': checks.append(v in self.flags)
            elif k == 'has_idea': checks.append(v in self.ideas)
            elif k == 'has_completed_focus': checks.append(v in self.focuses)
            elif k == 'has_war': checks.append(self.war == (v == 'yes'))
            elif k == 'country_exists': checks.append(v in self.countries)
            elif k == 'has_war_with': checks.append(v in self.enemies)
            elif k == 'has_opinion':
                _, cmp, val = next(item for item in v if item[0] == 'value')
                a = self.opinions[first(v, 'target')]
                checks.append(a > float(val) if cmp == '>' else a < float(val))
            elif k == 'tag': checks.append(v == ('B09' if self is self.countries.get('B09') else 'B11'))
            elif k == 'always': checks.append(v == 'yes')
            elif k in ('B09', 'B11'):
                checks.append(k in self.countries and self.countries[k].check(v))
            elif k in ('custom_override_tooltip', 'custom_trigger_tooltip'):
                checks.append(self.check([item for item in v if item[0] not in ('tooltip', 'not_tooltip')]))
            elif k == 'NOT': checks.append(not self.check(v))
            elif k == 'OR': checks.append(any(self.check([item]) for item in v))
            else: raise ValueError(f'Unsupported model trigger {k}')
        return all(checks)

    def run(self, block):
        branch = False
        for k, op, v in block:
            if k == 'if':
                branch = self.check(first(v, 'limit'))
                if branch: self.run([item for item in v if item[0] != 'limit'])
            elif k == 'else':
                if not branch: self.run(v)
            elif k == 'else_if':
                if not branch and self.check(first(v, 'limit')):
                    branch = True
                    self.run([item for item in v if item[0] != 'limit'])
            elif k in effects: self.run(effects[k])
            elif k == 'hidden_effect': self.run(v)
            elif k == 'custom_effect_tooltip': pass
            elif k in ('set_variable', 'add_to_variable', 'subtract_from_variable', 'divide_variable'):
                var, _, val = v[0]
                val = self.vars[val[4:]] if val.startswith('var:') else float(val)
                if k == 'set_variable': self.vars[var] = val
                elif k == 'divide_variable': self.vars[var] /= val
                else: self.vars[var] += val * (-1 if k == 'subtract_from_variable' else 1)
                self.vars[var] = round(self.vars[var], 3)
            elif k == 'clamp_variable':
                var = first(v, 'var')
                self.vars[var] = max(float(first(v, 'min')), min(float(first(v, 'max')), self.vars[var]))
            elif k == 'add_ideas': self.ideas.add(v)
            elif k == 'remove_ideas': self.ideas.discard(v)
            elif k == 'set_country_flag':
                name = first(v, 'flag') if isinstance(v, list) else v
                self.flags.add(name)
                if isinstance(v, list): self.flag_days[name] = int(first(v, 'days'))
            elif k == 'clr_country_flag':
                self.flags.discard(v)
                self.flag_days.pop(v, None)
            elif k == 'country_event':
                self.events.append(first(v, 'id'))
                self.scheduled.append((first(v, 'id'), int(first(v, 'days', '0'))))
            elif k in ('add_political_power','add_stability','add_war_support','army_experience'):
                self.metrics[k] += float(v)
            elif k == 'promote_character': self.leader = v if isinstance(v, str) else first(v, 'character')
            elif k == 'add_timed_idea': self.ideas.add(first(v, 'idea'))
            elif k == 'add_opinion_modifier':
                self.opinions[first(v, 'target')] += (25 if first(v, 'modifier') == 'KOCH_friendship' else -25)
            elif k in ('B09','B11'):
                if k in self.countries: self.countries[k].run(v)
            else: raise ValueError(f'Unsupported model effect {k}')

    def tick(self, block):
        for name in list(self.flag_days):
            self.flag_days[name] -= 1
            if self.flag_days[name] <= 0:
                self.flags.discard(name)
                del self.flag_days[name]
        self.run(block)

s = State()
s.flags.add(full('podik_path'))
for charge, brownout, golden in ((100, False, True), (89, False, False), (19, True, False), (30, True, False), (40, False, False)):
    s.vars['KOCH_podik_charge'] = charge
    s.run(effects[full('update_charge')])
    require((full('brownout') in s.ideas) == brownout and (full('golden_charge') in s.ideas) == golden, f'Charge threshold incorrect: {charge}')
s.flags.add(full('device_broken'))
s.vars['KOCH_podik_charge'] = 100
s.run(effects[full('update_charge')])
require(s.vars['KOCH_podik_charge'] == 0 and full('golden_charge') not in s.ideas, 'Broken device can be charged')
s.vars['KOCH_vamos_influence'] = 50
for _ in range(3): s.run(effects[full('shift_vamos')])
require(s.vars['KOCH_vamos_influence'] == 80 and s.vars['KOCH_gamos_influence'] == 20, 'Influence does not accumulate')
for _ in range(20): s.run(effects[full('shift_gamos')])
require(s.vars['KOCH_vamos_influence'] == 0 and s.vars['KOCH_gamos_influence'] == 100, 'Council bounds incorrect')

# Regression for the cartridge-replacement tooltip: the real effect restores
# the golden-age spirit; internal removals must not leak into its preview.
replacement = first(first(decisions, 'koch_podik_cult'), full('replace_cartridge'))
for charge, broken, missing, expected in ((24, False, False, True), (25, False, False, False), (10, True, False, False), (10, False, True, False)):
    s = State()
    s.vars['KOCH_podik_charge'] = charge
    if broken: s.flags.add(full('device_broken'))
    if missing: s.flags.add(full('device_missing'))
    require(s.check(first(replacement, 'available')) == expected, 'Cartridge replacement availability changed')
s = State()
s.flags.add(full('podik_path'))
s.vars['KOCH_podik_charge'] = 10
s.run(effects[full('update_charge')])
s.run(first(replacement, 'complete_effect'))
require(s.vars['KOCH_podik_charge'] == 100 and full('golden_charge') in s.ideas and full('brownout') not in s.ideas, 'Replacement must restore charge and golden age')
require(first(effects[full('update_charge')], 'hidden_effect') is not None, 'Charge recalculation leaks misleading idea changes into tooltips')

on_actions = first(parsed['common/on_actions/koch_podik.txt'], 'on_actions')
require(first(on_actions, 'on_weekly_B11') is None, 'Legacy weekly drain still enabled')
daily = first(first(on_actions, 'on_daily_B11'), 'effect')

def cult(charge=100, manual=False):
    state = State()
    state.run(effects[full('initialize')])
    state.flags.add(full('podik_path'))
    state.vars['KOCH_podik_charge'] = charge
    if manual: state.focuses.add(full('SACRED_MANUAL'))
    return state

for manual, war, saving in itertools.product((False, True), repeat=3):
    s = cult(manual=manual)
    s.war = war
    if saving: s.flags.add(full('battery_saving'))
    drain = max(0.1, (0.3 if manual else 0.5)+(0.2 if war else 0)-(0.2 if saving else 0))
    for _ in range(7): s.run(daily)
    require(abs(s.vars['KOCH_podik_charge']-(100-7*drain)) < 0.001, f'Daily charge drain incorrect: manual={manual}, war={war}, saving={saving}')

ritual = first(first(decisions, 'koch_podik_cult'), full('charge_ritual'))
for manual, expected in ((False, 70), (True, 100)):
    s = cult(10, manual)
    s.run(first(ritual, 'complete_effect'))
    require(not s.check(first(ritual, 'available')), 'Duplicate charging can start')
    for _ in range(3): s.run(daily)
    require(s.vars['KOCH_podik_charge'] == expected and full('charging') not in s.flags, 'Three-day charging incorrect')
s = cult(85)
s.run(first(ritual, 'complete_effect'))
s.run(daily)
require(s.vars['KOCH_podik_charge'] == 100 and s.vars['KOCH_podik_charge_days'] == 0 and full('charging') not in s.flags, 'Full battery must stop charging early')
s.run(daily)
require(s.vars['KOCH_podik_charge'] == 99.5, 'Drain did not resume after charging')

for failure in ('device_broken', 'device_missing'):
    s = cult(10, manual=True)
    s.flags |= {full(failure), full('auto_charge'), full('charging')}
    s.vars['KOCH_podik_charge_days'] = 2
    s.run(daily)
    require(s.vars['KOCH_podik_charge'] == 0 and full('charging') not in s.flags and s.vars['KOCH_podik_charge_days'] == 0, f'Charging resurrects unavailable device: {failure}')

s = cult(34, manual=True)
s.flags.add(full('auto_charge'))
s.run(daily)
require(s.vars['KOCH_podik_charge'] == 64 and full('charging') in s.flags, 'Automatic service did not start below 35%')
for _ in range(400): s.run(daily)
require('KOCH_PODIK.11007' not in s.events and 'KOCH_PODIK.11050' not in s.events, 'Automatic service failed to prevent battery crisis')
s = cult()
for _ in range(250): s.run(daily)
for eid in ('KOCH_PODIK.11049', 'KOCH_PODIK.11007', 'KOCH_PODIK.11050'):
    require(s.events.count(eid) == 1, f'Warning/blackout event spam: {eid}')
require(s.ideas & {full('brownout'), full('low_battery'), full('empty_battery')} == {full('empty_battery')}, 'Battery stage penalties stack')
for charge, idea in ((90, 'golden_charge'), (89.9, None), (40, None), (39.9, 'low_battery'), (20, 'low_battery'), (19.9, 'brownout'), (0, 'empty_battery')):
    s = cult(charge)
    s.run(effects[full('update_charge')])
    stage = s.ideas & {full(k) for k in ('golden_charge', 'low_battery', 'brownout', 'empty_battery')}
    require(stage == ({full(idea)} if idea else set()), f'Fractional battery stage incorrect: {charge}')
s = cult(19)
s.run(effects[full('update_charge')])
for charge, recovering in ((20, True), (39.9, True), (40, False)):
    s.vars['KOCH_podik_charge'] = charge
    s.run(effects[full('update_charge')])
    require((full('brownout') in s.ideas) == recovering, f'Battery crisis recovery incorrect: {charge}')
s = cult(55)
s.run(daily)
require(s.vars['KOCH_podik_charge'] == 54.5, 'Existing save charge reset during daily migration')
s = State()
s.run(effects[full('initialize')])
s.flags.add(full('council_path'))
s.vars['KOCH_podik_charge'] = 75
s.run(daily)
require(s.vars['KOCH_podik_charge'] == 75, 'Council subjected to cult battery drain')

def dynamic_text(name, state):
    blocks = values(parsed['common/scripted_localisation/koch_podik.txt'], 'defined_text')
    block = next(b for b in blocks if first(b, 'name') == name)
    for text in values(block, 'text'):
        if state.check(first(text, 'trigger', [])):
            return first(text, 'localization_key')

s = cult(10)
s.run(effects[full('update_charge')])
require(dynamic_text(full('GetChargeStatus'), s) == full('status_crisis'), 'Dashboard misses crisis stage')
s.flags.add(full('charging'))
require(dynamic_text(full('GetChargeStatus'), s) == full('status_charging'), 'Dashboard misses active charging')
s.flags.add(full('device_missing'))
require(dynamic_text(full('GetChargeStatus'), s) == full('status_missing') and dynamic_text(full('GetChargeForecast'), s) == full('forecast_unavailable'), 'Dashboard shows charging for missing device')
prophet = focus[full('MARK_PROPHET')]
s = cult()
require(not s.check(first(prophet, 'available')), 'Prophet focus unlocks without recognition')
s.flags.add(full('mark_recognized'))
require(s.check(first(prophet, 'available')), 'Recognizing Mark fails to unlock prophet focus')

monthly = first(first(on_actions, 'on_monthly_B11'), 'effect')
sabotage_condition = first(first(monthly, 'if'), 'limit')
for influence, outcome in ((50, False), (74, False), (75, True), (80, True), (25, True), (26, False)):
    s = State()
    s.flags.add(full('council_path'))
    s.vars['KOCH_vamos_influence'] = influence
    s.run(effects[full('normalize_council')])
    require(s.check(sabotage_condition) == outcome, f'Sabotage threshold incorrect: {influence}')
    for flag in ('compromise', 'single_chair', 'sabotage_pending'):
        s.flags.add(full(flag))
        require(not s.check(sabotage_condition), f'Sabotage ignores protection: {flag}')
        s.flags.discard(full(flag))

# New story route coverage: all independent major endings, including hostility.
expanded_routes = 0
for route, choices in routes:
    for balcony, diplomacy in itertools.product(('BAN_BALCONIES','SAFE_RAILINGS'),('RELATIONS_GRODNO','ACE_NOT_OUR_BUSINESS')):
        extras = [(p,) for p in ('MATERNAL_CONTROL','PRINTER_REVOLUTION','MOTHER_TREATY')] if route == 'cult' else list(itertools.product(('SECOND_DEMONSTRATION','TAILOR_AMNESTY'),('SILENCE_SECRET','SILENCE_IDEOLOGY','GAMOS_COUP')))
        for extra in extras:
            chosen = choices+[full(balcony),full(diplomacy)]+[full(x) for x in extra]
            blocked = set().union(*(exclusions[c] for c in chosen))
            done = set()
            while True:
                more = {fid for fid in focus if fid not in done|blocked
                    and not exclusions[fid]&done and all(g&done for g in requirements[fid])}
                if not more: break
                done |= more
            require(set(chosen)<=done, f'Expansion ending is unreachable: {chosen}')
            require(full('BALCONY_DOCTRINE') in done and full('FINAL_MEMO') in done,'Shared branch blocked by new ending')
            if route == 'cult': require(full('HOUSEHOLD_CONSTITUTION') in done,'Printer OR merge blocks an ending')
            else: require({full('SHIRT_HISTORY'),full('VOICE_THAT_WASNT')}<=done,'Council OR merge blocks an ending')
            expanded_routes += 1

def option_effect(n, i):
    return [item for item in values(events[f'KOCH_PODIK.{11000+n}'],'option')[i] if item[0] not in ('name','ai_chance','trigger')]

for value, warned, pending in ((0,False,False),(69.9,False,False),(70,True,False),(99.9,True,False),(100,True,True),(150,True,True)):
    s = cult()
    s.flags.add(full('printer_active'))
    s.vars['KOCH_mother_suspicion'] = value
    for _ in range(5): s.run(effects[full('update_suspicion')])
    require(s.vars['KOCH_mother_suspicion']<=100,'Suspicion escapes bounds')
    require((full('mother_warned') in s.flags)==warned and (full('inspection_pending') in s.flags)==pending,'Suspicion thresholds changed')
    require(s.events.count('KOCH_PODIK.11057')==int(warned) and s.events.count('KOCH_PODIK.11058')==int(pending),'Mother warning/inspection repeats')
    if pending: require(('KOCH_PODIK.11058',14) in s.scheduled,'Critical inspection lacks preparation time')

for outcome, effect in (('mother_victory','mother_wins'),('printer_revolution','printer_wins'),('mother_treaty','mother_compromise')):
    s = cult(73)
    s.flags |= {full('printer_active'),full('inspection_pending')}
    s.run(effects[full(effect)])
    require(full(outcome) in s.flags and full('printer_resolved') in s.flags,'Printer outcome not recorded')
    require(full('inspection_pending') not in s.flags,'Inspection remains pending after ending')
    for _ in range(250): s.run(daily)
    require('KOCH_PODIK.11058' not in s.events,'Resolved printer crisis repeats')

for charge in (0,19.5,73,100):
    s = cult(charge, manual=True)
    s.flags |= {full('auto_charge'),full('charging'),full('printer_active'),full('battery_saving')}
    s.ideas |= {full('charger_service'),full('battery_saving')}
    s.run(effects[full('mother_wins')])
    for _ in range(200): s.run(daily)
    require(s.vars['KOCH_podik_charge']==charge,'Confiscation loses stored charge or permits automatic charging')
    require(not s.ideas&{full(x) for x in ('golden_charge','low_battery','brownout','empty_battery','charger_service','battery_saving')},'Confiscation leaves battery penalties or maintenance cost')
    require(not s.check(first(ritual,'available')) and not s.check(first(replacement,'available')),'Confiscated device permits charging/replacement')
    require(dynamic_text(full('GetChargeStatus'),s)==full('status_confiscated'),'Dashboard hides confiscation')
    s.run(effects[full('return_confiscated')])
    require(s.vars['KOCH_podik_charge']==charge and {full('charger_service'),full('battery_saving')}<=s.ideas,'Return changes charge or fails to resume service/saving mode')
    s.run(daily)
    require(s.vars['KOCH_podik_charge'] != charge,'Returned device never resumes battery lifecycle')
for failure in ('device_broken','device_missing'):
    s=cult(70); s.flags.add(full(failure))
    s.run(effects[full('mother_wins')]); s.run(effects[full('return_confiscated')])
    require(s.vars['KOCH_podik_charge']==0 and full(failure) in s.flags,'Confiscation/return repairs broken or missing device')

s=cult();s.flags|={full('printer_active'),full('charging')}
s.run(effects[full('expansion_daily')])
require(s.vars['KOCH_mother_suspicion']==1.15,'Charging suspicion incorrect')
s.flags.add(full('quiet_charging'));s.run(effects[full('expansion_daily')])
require(s.vars['KOCH_mother_suspicion']==1.3,'Quiet charging still raises charging suspicion')
s.flags.add(full('device_missing'))
for _ in range(5):s.run(effects[full('expansion_daily')])
require(abs(s.vars['KOCH_mother_suspicion']-12.05)<0.001,'Search denunciation repeats daily')
household=first(decisions,'koch_podik_household')
s.vars['KOCH_mother_suspicion']=5
s.run(first(first(household,full('clean_room')),'complete_effect'))
require(s.vars['KOCH_mother_suspicion']==0,'Cleaning makes suspicion negative')

# Four shirt choices and four Gamos reactions have distinct political effects.
require(len(values(events['KOCH_PODIK.11072'],'option'))==4,'Great Rip requires four choices')
signatures=[]
for i in range(4):
    s=State();s.vars['KOCH_vamos_influence']=50;s.run(option_effect(72,i))
    require(s.vars['KOCH_vamos_influence']+s.vars['KOCH_gamos_influence']==100,'Shirt scandal breaks complementary influence')
    signatures.append((s.vars['KOCH_vamos_influence'],s.metrics['add_stability'],frozenset(s.flags)))
require(len(set(signatures))==4,'Shirt choices have identical results')
for i,expected in enumerate((35,20,60,65)):
    s=State();s.vars['KOCH_vamos_influence']=50;s.run(option_effect(74,i))
    require(s.vars['KOCH_vamos_influence']==expected,'Gamos tape choice has wrong influence')
for settled in (False,True):
    s=State()
    if settled:s.flags.add(full('council_settled'))
    s.run(effects[full('gamos_takeover')])
    require((s.leader==full('gamos'))== (not settled),'Gamos coup overrides a settled government or fails to promote him')
    if not settled:
        require(s.vars['KOCH_gamos_influence']==80,'Gamos coup grants wrong influence')
        s.run(effects[full('council_settlement')])
        require(full('gamos_regency') not in s.ideas,'Council settlement leaves temporary regency')
for winner,expected in (('vamos_won',100),('gamos_won',0)):
    s=State();s.flags|={full('single_chair'),full(winner)};s.vars['KOCH_vamos_influence']=50
    s.run(option_effect(74,1))
    require(s.vars['KOCH_vamos_influence']==expected,'Delayed scandal undermines single-chair government')

# Absent B09 and war cannot issue cemetery requests; refusal has a peaceful fallback.
for exists,war in itertools.product((False,True),repeat=2):
    s=State();b=State();s.countries={'B11':s,**({'B09':b} if exists else {})};b.countries=s.countries
    if war:s.enemies.add('B09');b.enemies.add('B11')
    s.run(effects[full('request_cemetery')])
    require(bool(b.events)==(exists and not war),'Cemetery request ignores absent B09 or war')
    if exists and not war:
        b.run(option_effect(65,1))
        require(full('cemetery_refused') in s.flags and full('cemetery_pending') not in s.flags,'Refusal blocks retry')
        quiet=first(first(decisions,'koch_podik_stories'),full('cemetery_quiet_deal'))
        require(s.check(first(quiet,'available')),'Peaceful protocol unavailable after refusal')
        s.run(first(quiet,'complete_effect'));b.run(option_effect(101,0))
        require(full('cemetery_permit') in s.flags and full('cemetery_pending') not in s.flags,'Quiet protocol fails to unlock cemetery')

# Secret scheduler gates all ten events, fires at most one per call, never repeats.
secret_blocks=values(effects[full('secret_archives')],'if')+values(effects[full('secret_archives')],'else_if')
require(len(secret_blocks)==10,'Ten secret events must be scheduled')
for n in range(87,97):
    s=cult();s.vars['KOCH_mother_suspicion']=60
    # Complete both mutually exclusive prerequisites here only to test scheduler coverage.
    s.focuses=set(focus);s.flags|={full(x) for x in ('printer_active','toner_bought','wait_for_no','makafon_resolved','long_broadcast','cemetery_permit','cartridge_relic','newton_convicted','two_shrines_signed')}
    s.ideas.add(full('silence_archive'))
    for _ in range(20):
        before=len(s.events);s.run(effects[full('secret_archives')])
        require(len(s.events)-before<=1,'Secret scheduler spams multiple events per month')
    require(s.events.count(f'KOCH_PODIK.{11000+n}')==1,'Secret event is unreachable or repeats')
s=State();s.run(effects[full('secret_archives')]);require(not s.events,'Secrets trigger with no special conditions')

modifier_doc = (game/'documentation/modifiers_documentation.md').read_text(encoding='utf-8-sig')
for _, _, idea in ideas:
    for key, _, _ in first(idea, 'modifier', []):
        # Building-specific production modifiers are generated by the engine.
        require(key in modifier_doc or re.fullmatch(r'production_speed_(industrial_complex|arms_factory|infrastructure)_factor', key), f'Undocumented modifier: {key}')

if errors:
    print('\n'.join('FAIL: '+e for e in errors))
    sys.exit(1)
print(f'PASS: {len(focus)} focuses, {len(events)} events, {len(idea_ids)} spirits, {len(decision_ids)} decisions, {len(categories)} categories.')
print(f'PASS: {len(routes)} political routes, dependencies, exclusivity, durations, positions, references, Russian text and sprites.')
print('PASS: executed DSL model for daily battery modes, charging, automation, warnings, blackout/recovery, save migration, influence and sabotage.')
print(f'PASS: {expanded_routes} expanded routes, mother warning/outcomes, confiscation/return, shirt choices, Gamos regency, cemetery refusal/peaceful protocol and ten once-only secrets.')
