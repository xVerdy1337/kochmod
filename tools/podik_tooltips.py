"""Player-facing labels for scripted availability conditions."""
import re

FLAGS = {
    'device_broken': ('Подик сломан', 'Подик исправен'),
    'device_missing': ('Подик пропал', 'Подик на месте'),
    'search_pending': ('Розыск или срочный ремонт уже начат', 'Розыск или срочный ремонт ещё не начат'),
    'guard_consent': ('Артур согласился на охрану', 'Согласие Артура на охрану ещё не получено'),
    'mark_recognized': ('Откровение Марка признано', 'Откровение Марка ещё не признано'),
    'podik_path': ('Выбран священный путь Подика', 'Священный путь Подика не выбран'),
    'council_path': ('К власти пришёл Совет Вамоса и Гамоса', 'Совет Вамоса и Гамоса не у власти'),
    'charging': ('Подик заряжается', 'Подик сейчас не заряжается'),
    'battery_saving': ('Включён экономрежим', 'Экономрежим выключен'),
}
VARIABLES = {
    ('KOCH_mother_suspicion', '<', '85'): ('mother_below_85', 'Подозрение мамы ниже 85'),
    ('KOCH_podik_charge', '<', '90'): ('charge_below_90', 'Заряд Подика ниже 90%'),
    ('KOCH_podik_charge', '<', '25'): ('charge_below_25', 'Заряд Подика ниже 25%'),
    ('KOCH_podik_charge', '>', '29'): ('charge_at_least_30', 'Заряд Подика не ниже 30%'),
    ('KOCH_podik_charge', '>', '49'): ('charge_at_least_50', 'Заряд Подика не ниже 50%'),
    ('KOCH_vamos_influence', '<', '100'): ('vamos_below_100', 'Влияние Вамоса ниже 100%'),
    ('KOCH_gamos_influence', '<', '100'): ('gamos_below_100', 'Влияние Гамоса ниже 100%'),
    ('KOCH_vamos_influence', '>', '64'): ('vamos_at_least_65', 'Влияние Вамоса не ниже 65%'),
    ('KOCH_gamos_influence', '>', '64'): ('gamos_at_least_65', 'Влияние Гамоса не ниже 65%'),
}
LOC = {}
for flag, (positive, negative) in FLAGS.items():
    key = 'KOCH_B11_condition_'+flag+'_tt'
    LOC[key], LOC[key+'_NOT'] = positive, negative
    # Fallback for older saves/scripts that still display the raw flag trigger.
    LOC['KOCH_B11_'+flag] = positive
for name, label in VARIABLES.values():
    LOC['KOCH_B11_condition_'+name+'_tt'] = label


def readable_conditions(text):
    def flag(match):
        name = match[1]
        if name not in FLAGS:
            return match[0]
        key = 'KOCH_B11_condition_'+name+'_tt'
        return f'custom_override_tooltip = {{ tooltip = {key} not_tooltip = {key}_NOT {match[0]} }}'

    def variable(match):
        data = VARIABLES.get((match[1], match[2], match[3]))
        if not data:
            return match[0]
        key = 'KOCH_B11_condition_'+data[0]+'_tt'
        return f'custom_override_tooltip = {{ tooltip = {key} {match[0]} }}'

    text = re.sub(r'has_country_flag\s*=\s*KOCH_B11_(\w+)', flag, text)
    return re.sub(r'check_variable\s*=\s*\{\s*(\w+)\s*([<>])\s*(\d+)\s*\}', variable, text)
