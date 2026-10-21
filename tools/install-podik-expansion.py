"""Install generated expansion blocks without changing existing focus IDs."""
from pathlib import Path
import re
from podik_expansion import FOCUSES, OLD_EVENTS, LOC, SECRET_GATES, cond, flag
import runpy
runpy.run_path('tools/build-podik-events.py')

MARK = '# PODIK EXPANSION\n'
def read(path): return Path(path).read_text(encoding='utf-8-sig')
def save(path,text): Path(path).write_text(text,encoding='utf-8')
def generated(path, script):
    text = read(path).split(MARK)[0].rstrip()+'\n\n'+MARK+script.strip()+'\n'
    save(path,text)

def span(text,start):
    depth=0
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}]',text[start:]):
        if m[0]=='{': depth+=1
        elif m[0]=='}':
            depth-=1
            if depth==0: return start+m.end()
    raise ValueError('Unclosed block')

focus_path='common/national_focus/koch_podik.txt'
t=read(focus_path)
if MARK in t: t=t.split(MARK)[0].rstrip()+'\n}\n'
# Move diplomacy right of the new Council branches; economy is independent.
for m in reversed(list(re.finditer(r'    focus = \{',t))):
    end=span(t,m.start()); b=t[m.start():end]
    name=re.search(r'id = KOCH_B11_(\w+)',b)[1]
    pos=re.search(r'x = (-?\d+) y = (\d+)',b)
    x,y=map(int,pos.groups())
    if name in ('DIPLOMATIC_ARGUMENT','RELATIONS_GRODNO','PROTECT_ACE','PACT_ACES','BROTHERHOOD','ARTHUR_SUMMIT','ONE_ALLIANCE_TWO_STATES','ACE_NOT_OUR_BUSINESS','DEEP_CONCERN','CONDEMN_ACE','GRODNO_ULTIMATUM','NOT_OUR_WAY'):
        # Already moved positions remain unchanged on repeated installation.
        if x<30: b=b[:pos.start()]+f'x = {x+18} y = {y}'+b[pos.end():]
    elif name in ('EMERGENCY_LOGISTICS','CARTRIDGE_FACTORY','NATIONAL_MILITIA','PROPAGANDA_CIRCUS','SCIENCE_OF_STUPIDITY','BORDER_COMMITTEE','FINAL_MEMO'):
        if x==25: b=b[:pos.start()]+f'x = 46 y = {y-8}'+b[pos.end():]
    if name in OLD_EVENTS and f'KOCH_PODIK.{11000+OLD_EVENTS[name]}' not in b:
        b=b.rstrip()[:-1].rstrip() # final focus brace
        # Insert inside completion_reward, before its matching closing brace.
        cr=b.index('completion_reward = {'); ce=span(b,cr)
        b=b[:ce-1]+f' country_event = {{ id = KOCH_PODIK.{11000+OLD_EVENTS[name]} days = 1 }} '+b[ce-1:]+'\n    }'
    t=t[:m.start()]+b+t[end:]
save(focus_path,t.rstrip()[:-1].rstrip()+'\n\n'+MARK+''.join(FOCUSES)+'}\n')

effects_path='common/scripted_effects/koch_podik.txt'
t=read(effects_path).split(MARK)[0]
# Confiscation preserves actual charge and existing broken/missing flags.
if 'KOCH_B11_device_confiscated' not in t:
    t=t.replace('limit = { has_country_flag = KOCH_B11_podik_path }\n        KOCH_B11_calculate_drain', 'limit = { has_country_flag = KOCH_B11_podik_path NOT = { has_country_flag = KOCH_B11_device_confiscated } }\n        KOCH_B11_calculate_drain')
    start=t.index('KOCH_B11_update_charge = {'); pos=t.index('            remove_ideas = KOCH_B11_low_battery',start)
    end=t.index('\n        KOCH_B11_calculate_drain = yes',pos)
    # The original closing brace at end closes the path limit; add a nested else.
    t=t[:pos]+'''            if = {
                limit = { has_country_flag = KOCH_B11_device_confiscated }
                set_variable = { KOCH_podik_charge = var:KOCH_confiscated_charge }
                clr_country_flag = KOCH_B11_charging
                set_variable = { KOCH_podik_charge_days = 0 }
                remove_ideas = KOCH_B11_golden_charge
                remove_ideas = KOCH_B11_low_battery
                remove_ideas = KOCH_B11_brownout
                remove_ideas = KOCH_B11_empty_battery
            }
            else = {
'''+t[pos:end].rstrip()+'\n            }\n'+t[end:]
    # Final single-chair leadership cannot be undermined by a queued story choice.
    pos=t.index('    clamp_variable = { var = KOCH_vamos_influence')
    t=t[:pos]+'''    if = { limit = { has_country_flag = KOCH_B11_single_chair has_country_flag = KOCH_B11_vamos_won } set_variable = { KOCH_vamos_influence = 100 } }
    if = { limit = { has_country_flag = KOCH_B11_single_chair has_country_flag = KOCH_B11_gamos_won } set_variable = { KOCH_vamos_influence = 0 } }
'''+t[pos:]
save(effects_path,t)
secret_script = '\nKOCH_B11_secret_archives = {\n'
for index,(n,gate) in enumerate(SECRET_GATES.items()):
    op = 'if' if index == 0 else 'else_if'
    secret_script += f'''    {op} = {{
        limit = {{ {gate} NOT = {{ has_country_flag = KOCH_B11_secret_{n} }} }}
        set_country_flag = KOCH_B11_secret_{n}
        country_event = {{ id = KOCH_PODIK.{11000+n} days = 1 }}
    }}\n'''
secret_script += '}\n'
generated(effects_path,r'''
KOCH_B11_update_suspicion = {
    clamp_variable = { var = KOCH_mother_suspicion min = 0 max = 100 }
    if = {
        limit = { has_country_flag = KOCH_B11_printer_active NOT = { has_country_flag = KOCH_B11_printer_resolved } }
        if = {
            limit = { check_variable = { var = KOCH_mother_suspicion value = 70 compare = greater_than_or_equals } NOT = { has_country_flag = KOCH_B11_mother_warned } }
            set_country_flag = KOCH_B11_mother_warned
            country_event = { id = KOCH_PODIK.11057 days = 1 }
        }
        if = {
            limit = { check_variable = { var = KOCH_mother_suspicion value = 100 compare = greater_than_or_equals } NOT = { has_country_flag = KOCH_B11_inspection_pending } }
            set_country_flag = KOCH_B11_inspection_pending
            country_event = { id = KOCH_PODIK.11058 days = 14 }
        }
    }
}
KOCH_B11_suspicion_10 = {
    if = {
        limit = { has_country_flag = KOCH_B11_printer_active NOT = { has_country_flag = KOCH_B11_printer_resolved } }
        add_to_variable = { KOCH_mother_suspicion = 10 }
        KOCH_B11_update_suspicion = yes
    }
}
KOCH_B11_resolve_printer = {
    set_country_flag = KOCH_B11_printer_resolved
    clr_country_flag = KOCH_B11_inspection_pending
    remove_ideas = KOCH_B11_printer_cache
    remove_ideas = KOCH_B11_printer_guard
    set_variable = { KOCH_mother_suspicion = 0 }
}
KOCH_B11_mother_wins = {
    KOCH_B11_resolve_printer = yes
    set_country_flag = KOCH_B11_mother_victory
    set_country_flag = KOCH_B11_device_confiscated
    set_variable = { KOCH_confiscated_charge = var:KOCH_podik_charge }
    remove_ideas = KOCH_B11_charger_service
    remove_ideas = KOCH_B11_battery_saving
    add_ideas = KOCH_B11_underground_cult
    add_stability = -0.04
    KOCH_B11_update_charge = yes
    custom_effect_tooltip = KOCH_B11_confiscation_tt
}
KOCH_B11_printer_wins = {
    KOCH_B11_resolve_printer = yes
    set_country_flag = KOCH_B11_printer_revolution
    add_ideas = KOCH_B11_holy_printer
    add_ideas = KOCH_B11_mother_enemy
    add_stability = -0.08
    add_war_support = 0.06
}
KOCH_B11_mother_compromise = {
    KOCH_B11_resolve_printer = yes
    set_country_flag = KOCH_B11_mother_treaty
    add_political_power = -40
    add_ideas = KOCH_B11_household_treaty
    add_stability = 0.04
}
KOCH_B11_return_confiscated = {
    clr_country_flag = KOCH_B11_device_confiscated
    set_variable = { KOCH_podik_charge = var:KOCH_confiscated_charge }
    if = { limit = { has_country_flag = KOCH_B11_auto_charge } add_ideas = KOCH_B11_charger_service }
    if = { limit = { has_country_flag = KOCH_B11_battery_saving } add_ideas = KOCH_B11_battery_saving }
    KOCH_B11_update_charge = yes
    custom_effect_tooltip = KOCH_B11_return_device_tt
}
KOCH_B11_request_cemetery = {
    if = {
        limit = { country_exists = B09 NOT = { has_war_with = B09 } }
        set_country_flag = { flag = KOCH_B11_cemetery_pending days = 30 }
        B09 = { country_event = { id = KOCH_PODIK.11065 days = 2 } }
    }
}
KOCH_B11_cemetery_apology = {
    if = { limit = { country_exists = B09 NOT = { has_war_with = B09 } }
        add_opinion_modifier = { target = B09 modifier = KOCH_friendship }
        B09 = { add_opinion_modifier = { target = B11 modifier = KOCH_friendship } }
    }
}
KOCH_B11_cemetery_scandal = {
    if = { limit = { country_exists = B09 }
        add_opinion_modifier = { target = B09 modifier = KOCH_cold_shoulders }
        B09 = { add_opinion_modifier = { target = B11 modifier = KOCH_cold_shoulders } }
    }
}
KOCH_B11_two_shrines = {
    if = { limit = { country_exists = B09 NOT = { has_war_with = B09 } has_country_flag = KOCH_B11_guard_consent has_country_flag = KOCH_B11_cemetery_permit }
        set_country_flag = KOCH_B11_two_shrines_signed
        add_ideas = KOCH_B11_two_shrines
        B09 = { add_ideas = KOCH_B11_two_shrines }
        KOCH_B11_cemetery_apology = yes
    }
}
KOCH_B11_gamos_takeover = {
    if = { limit = { NOT = { has_country_flag = KOCH_B11_council_settled } }
        set_country_flag = KOCH_B11_gamos_regent
        set_variable = { KOCH_vamos_influence = 20 }
        KOCH_B11_normalize_council = yes
        promote_character = KOCH_B11_gamos
        add_ideas = KOCH_B11_gamos_regency
        add_stability = -0.05
    }
    else = { add_political_power = 25 }
}
KOCH_B11_expansion_daily = {
    if = { limit = { has_country_flag = KOCH_B11_printer_active NOT = { has_country_flag = KOCH_B11_printer_resolved } }
        add_to_variable = { KOCH_mother_suspicion = 0.15 }
        if = { limit = { has_country_flag = KOCH_B11_charging NOT = { has_country_flag = KOCH_B11_quiet_charging } } add_to_variable = { KOCH_mother_suspicion = 1 } }
        if = { limit = { has_country_flag = KOCH_B11_device_missing NOT = { has_country_flag = KOCH_B11_search_denounced } } set_country_flag = KOCH_B11_search_denounced KOCH_B11_suspicion_10 = yes }
        KOCH_B11_update_suspicion = yes
    }
}
'''+secret_script)

# Unique spirits use verified vanilla idea pictures and documented modifiers.
spirits = [
 ('printer_cache','Государство внутри принтера','Тайник помогает хранить секреты, но ежедневное подозрение матери растёт.','political_power_factor = 0.03 stability_factor = -0.02','generic_oppression'),
 ('printer_guard','Караул у сломанной крышки','Охрана тайника требует содержания.','political_power_gain = -0.1 war_support_factor = 0.03','generic_oppression'),
 ('underground_cult','Культ под кроватью','Мама победила. Подик можно вернуть переговорами, но утраченная публичность культа остаётся политической ценой.','political_power_factor = -0.05 stability_factor = 0.02','generic_oppression'),
 ('holy_printer','Священная территория принтера','Открытие крышки без допуска запрещено законом.','war_support_factor = 0.06 stability_factor = 0.02','generic_constitutional_guarantees'),
 ('mother_enemy','Мама — Враг народа №1','Мать Наминала оспаривает культ, а государство содержит аппарат домашней холодной войны. Неприкосновенность матери гарантирована соглашением.','political_power_gain = -0.15 stability_factor = -0.03','generic_oppression'),
 ('household_treaty','Мирный договор с мамой','Выносить мусор и соблюдать расписание дешевле чрезвычайного положения.','stability_factor = 0.05 political_power_gain = -0.05','generic_constitutional_guarantees'),
 ('mourning','Государственный траур','Память требует уважения. Временный траур замедляет политическую суету.','political_power_factor = -0.05 war_support_factor = -0.02','generic_oppression'),
 ('falling_ministry','Министерство недопущения падений','Профилактика превратилась в отдельное ведомство.','political_power_gain = -0.1 army_defence_factor = 0.02','generic_build_infrastructure'),
 ('balcony_ban','Балконы вне закона','Радикальная архитектурная кампания расходует строительные ресурсы.','production_speed_buildings_factor = -0.03 war_support_factor = 0.05','generic_oppression'),
 ('safe_railings','Государственная программа перил','Инженеры получили работу, граждане — исправные ограждения.','stability_factor = 0.04 production_speed_infrastructure_factor = 0.05','generic_build_infrastructure'),
 ('balcony_doctrine','Балконная доктрина','Надёжная опора и оборонная подготовка пережили расследование комиссии.','army_defence_factor = 0.05 dig_in_speed_factor = 0.1','generic_oppression'),
 ('two_shrines','Две святыни под защитой','Согласованные церемонии и охрана укрепляют доверие.','stability_factor = 0.03 political_power_factor = 0.03','generic_constitutional_guarantees'),
 ('brown_crisis','Коричневый кризис','Вамос обосрался, футболка осталась целой, а правительство пытается отстирать легитимность.','stability_factor = -0.06 political_power_factor = -0.04','generic_oppression'),
 ('trouser_reserve','Стратегический резерв штанов','Снабжение впервые подготовлено к последствиям демонстрации силы.','supply_consumption_factor = -0.03','generic_build_infrastructure'),
 ('silence_archive','Архив несуществующей информации','Секретность передана Гамосу вместе с бюджетом на хранение пустоты.','political_power_factor = 0.04 research_speed_factor = -0.02','generic_oppression'),
 ('silence_ideology','Молчализм','Тишина сокращает совещания и оставляет рабочим время на производство.','industrial_capacity_factory = 0.04 war_support_factor = -0.02','generic_neutrality_drift_bonus'),
 ('gamos_regency','Временное руководство Гамоса','Гамос занял кресло до конституционного финала.','political_power_factor = 0.05 stability_factor = -0.03','generic_oppression'),
]
path='common/ideas/koch_podik.txt';t=read(path)
if MARK in t: t=t.split(MARK)[0].rstrip()+'\n    }\n}\n'
closing=t.rfind('    }')
blocks=[]
for name,title,desc,mod,pic in spirits:
    LOC['KOCH_B11_'+name],LOC['KOCH_B11_'+name+'_desc']=title,desc
    blocks.append(f'        KOCH_B11_{name} = {{ picture = {pic} allowed = {{ always = yes }} removal_cost = -1 modifier = {{ {mod} }} }}\n')
save(path,t[:closing]+MARK+''.join(blocks)+'    }\n}\n')

categories='common/decisions/categories/koch_podik.txt'
generated(categories, '''koch_podik_household = {
    icon = generic_political_actions
    visible = { tag = B11 has_country_flag = KOCH_B11_printer_active }
    allowed = { original_tag = B11 }
}
koch_podik_stories = {
    icon = generic_political_actions
    visible = { tag = B11 has_completed_focus = KOCH_B11_NEW_EPOCH }
    allowed = { original_tag = B11 }
}
''')
LOC.update({
 'KOCH_mother_suspicion':'Подозрение мамы',
 'KOCH_confiscated_charge':'Сохранённый заряд конфискованного подика',
 'koch_podik_household':'Мама, принтер и государственная тайна',
 'koch_podik_household_desc':'Подозрение мамы: §Y[?KOCH_mother_suspicion|1]/100§!. До развязки растёт на 0,15 в день. Зарядка без тихого режима добавляет 1 в день, литания и розыск — 10. На 70 придёт предупреждение, на 100 назначается проверка через 14 дней. Проверка предлагает три исхода. Понижение подозрения ниже 85 открывает бесплатный компромисс.',
 'koch_podik_stories':'Дела, которые не помещаются в протокол',
 'koch_podik_stories_desc':'Переговоры о кладбище, политика Совета и секретные архивы. Повторные обращения требуют времени и политической власти. Отказ Артура не требует войны.',
 'KOCH_B11_confiscation_tt':'Подик конфискован. Заряд сохранён; зарядка, автоматическая плата и штрафы за разряд приостановлены. Возврат доступен решением. Поломка и пропажа от этого не устраняются.',
 'KOCH_B11_return_device_tt':'Сохранённый заряд и автоматическое обслуживание возобновятся. Поломку и пропажу при необходимости устраняют отдельные решения.',
 'KOCH_B11_suspicion_down_tt':'Подозрение мамы снизится на §G20§! (минимум 0).',
 'KOCH_B11_quiet_charge_tt':'На §Y30 дней§! подозрение не растёт от зарядки. Обычный расход батареи сохраняется.',
 'KOCH_B11_mother':'Мать Наминала',
 'KOCH_B11_mother_desc':'Мать Наминала, противница подика и единственный человек, перед которым Министерство безопасности убирает комнату без напоминания.',
})
decisions=[]
def decision(cat,name,title,desc,visible,available,reward,cost=20,cooldown=30,once='no'):
    LOC['KOCH_B11_'+name],LOC['KOCH_B11_'+name+'_desc']=title,desc
    decisions.append((cat,f'''    KOCH_B11_{name} = {{
        icon = generic_decision
        visible = {{ {visible} }}
        available = {{ {cond(available,desc)} }}
        cost = {cost}
        fire_only_once = {once}
        days_re_enable = {cooldown}
        complete_effect = {{ {reward} }}
        ai_will_do = {{ factor = 1 }}
    }}\n'''))
active='NOT = { '+flag('printer_resolved')+' }'
decision('household','clean_room','Убрать комнату по мобилизационному плану','До развязки; подозрение ниже на 20. Повтор через 30 дней.',active,active+' check_variable = { KOCH_mother_suspicion > 0 }','add_to_variable = { KOCH_mother_suspicion = -20 } KOCH_B11_update_suspicion = yes custom_effect_tooltip = KOCH_B11_suspicion_down_tt')
decision('household','decoy_print','Заказать отвлекающую распечатку','До развязки; подозрение ниже на 20. Повтор через 45 дней.',active,active+' check_variable = { KOCH_mother_suspicion > 0 }','add_to_variable = { KOCH_mother_suspicion = -20 } KOCH_B11_update_suspicion = yes custom_effect_tooltip = KOCH_B11_suspicion_down_tt',cost=25,cooldown=45)
decision('household','quiet_charge','Заряжать без торжественного караула','До развязки; тихая зарядка действует 30 дней.',active,active+' NOT = { '+flag('quiet_charging')+' }','set_country_flag = { flag = KOCH_B11_quiet_charging days = 30 } custom_effect_tooltip = KOCH_B11_quiet_charge_tt',cost=15)
decision('household','return_device','Попросить вернуть подик','Подик конфискован матерью. Возврат сохраняет исход победы матери и не чинит устройство.',flag('device_confiscated'),flag('device_confiscated'),'KOCH_B11_return_confiscated = yes',cost=50,once='yes')
decision('stories','cemetery_retry','Повторить запрос Артуру','Гродненская республика существует; нет войны, разрешения или ожидающего запроса.','has_completed_focus = KOCH_B11_GROBNO_EXPEDITION','country_exists = B09 NOT = { has_war_with = B09 } NOT = { '+flag('cemetery_permit')+' } NOT = { '+flag('cemetery_pending')+' }','KOCH_B11_request_cemetery = yes',cost=20)
decision('stories','cemetery_quiet_deal','Согласовать делегацию без оркестра','После отказа Артура; нет войны или ожидающего запроса. Доступ обеспечит ограниченный протокол посещения.',flag('cemetery_refused'),'country_exists = B09 NOT = { has_war_with = B09 } NOT = { '+flag('cemetery_pending')+' } NOT = { '+flag('cemetery_permit')+' }','set_country_flag = { flag = KOCH_B11_cemetery_pending days = 30 } set_country_flag = KOCH_B11_quiet_deal B09 = { country_event = { id = KOCH_PODIK.11101 days = 2 } }',cost=35,cooldown=30)
decision('stories','denounce_cache','Донести на тайник Наминала','Совет пришёл к власти, и принтерная история начата; однократный донос даёт Гамосу 10 влияния.','has_completed_focus = KOCH_B11_COUNCIL_PATH',flag('printer_active')+' NOT = { '+flag('printer_resolved')+' }','KOCH_B11_suspicion_10 = yes KOCH_B11_shift_gamos = yes',cost=15,once='yes')
# On exclusive Council route, the private printer story can be opened without cult focuses.
decision('stories','council_printer_dossier','Досье Совета: тайник Наминала','Совет у власти; принтерная история ещё не начата. Открывает бытовой кризис без религиозной ветки.',flag('council_path'),flag('council_path')+' NOT = { '+flag('printer_active')+' }','set_country_flag = KOCH_B11_printer_active set_variable = { KOCH_mother_suspicion = 30 } country_event = { id = KOCH_PODIK.11051 days = 1 }',cost=25,once='yes')
path='common/decisions/koch_podik.txt';t=read(path).split(MARK)[0]
# All existing manual battery/revelation decisions respect confiscation.
if 'KOCH_B11_exp_device_access_tt' not in t:
    cut=t.index('\nkoch_podik_council')
    cult=t[:cut]
    cult=cult.replace('available = {','available = { custom_override_tooltip = { tooltip = KOCH_B11_exp_device_access_tt NOT = { has_country_flag = KOCH_B11_device_confiscated } }',)
    t=cult+t[cut:]
    t=t.replace('complete_effect = { add_to_variable = { KOCH_podik_charge = -10 }','complete_effect = { KOCH_B11_suspicion_10 = yes add_to_variable = { KOCH_podik_charge = -10 }')
save(path,t)

# Schedule at most one eligible secret per month, each once per playthrough.
path='common/on_actions/koch_podik.txt';t=read(path).split(MARK)[0]
if 'KOCH_B11_secret_archives = yes' not in t:
    pos=t.index('    on_monthly_B11 = {')
    end=span(t,pos)
    close=t.rfind('        }',pos,end)
    t=t[:close]+'            KOCH_B11_secret_archives = yes\n'+t[close:]
save(path,t)
LOC['KOCH_B11_exp_device_access_tt']='Подик не конфискован матерью'
generated('common/decisions/koch_podik.txt','\n'.join('koch_podik_'+cat+' = {\n'+''.join(b for c,b in decisions if c==cat)+'}\n' for cat in ('household','stories')))

path='common/on_actions/koch_podik.txt';t=read(path)
if 'KOCH_B11_expansion_daily' not in t:
    t=t.replace('            KOCH_B11_daily_charge = yes','            KOCH_B11_expansion_daily = yes\n            KOCH_B11_daily_charge = yes')
    t=t.replace('has_country_flag = KOCH_B11_podik_path NOT', 'has_country_flag = KOCH_B11_podik_path NOT = { has_country_flag = KOCH_B11_device_confiscated } NOT')
save(path,t)

path='common/scripted_localisation/koch_podik.txt';t=read(path)
if 'status_confiscated' not in t:
    t=t.replace('name = KOCH_B11_GetChargeStatus','name = KOCH_B11_GetChargeStatus\n    text = { trigger = { has_country_flag = KOCH_B11_device_confiscated } localization_key = KOCH_B11_status_confiscated }')
    t=t.replace('name = KOCH_B11_GetChargeForecast','name = KOCH_B11_GetChargeForecast\n    text = { trigger = { has_country_flag = KOCH_B11_device_confiscated } localization_key = KOCH_B11_forecast_unavailable }')
save(path,t)
path='common/characters/koch_B11.txt';t=read(path)
if '    KOCH_B11_mother = {' not in t:
    t=t.rstrip()[:-1]+'''    KOCH_B11_mother = {
        name = KOCH_B11_mother
        portraits = { civilian = { large = "gfx/leaders/scientists/generic_scientists/portrait_generic_europe_female_01.dds" } }
        advisor = { slot = political_advisor idea_token = KOCH_B11_mother allowed = { original_tag = B11 } available = { has_country_flag = KOCH_B11_mother_treaty } traits = { compassionate_gentleman } cost = 100 }
    }
}
'''
save(path,t)
path='history/countries/B11 - koch.txt';t=read(path)
if 'recruit_character = KOCH_B11_mother' not in t: save(path,t+'\nrecruit_character = KOCH_B11_mother\n')
# Regencies are removed by every existing Council settlement.
path='common/scripted_effects/koch_podik.txt';t=read(path)
if 'KOCH_B11_council_settlement = {\n    remove_ideas = KOCH_B11_gamos_regency' not in t:
    t=t.replace('KOCH_B11_council_settlement = {','KOCH_B11_council_settlement = {\n    remove_ideas = KOCH_B11_gamos_regency\n    clr_country_flag = KOCH_B11_gamos_regent')
save(path,t)

# Store generated supporting localisation for the normal builder to reuse.
import json
Path('tools/podik-expansion-loc.json').write_text(json.dumps(LOC,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Installed {len(FOCUSES)} new focuses, {len(spirits)} spirits and {len(decisions)} decisions.')
