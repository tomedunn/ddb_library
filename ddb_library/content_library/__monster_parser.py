"""Tools for importing monsters from DnD Beyond HTML files taken from books and spells.

Functions:

    construct_monster(BeautifulSoup) -> dict
"""

from bs4 import BeautifulSoup
import re

MONSTER_DEFAULTS = {
    'CR': ['0', '1/8', '1/4', '1/2', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
           '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
           '21', '22', '23', '24', '25', '26', '27', '28', '29', '30'],
    'XP': [0, 25, 50, 100, 200, 450, 700, 1100, 1800, 2300, 2900, 3900, 5000, 
        5900, 7200, 8400, 10000, 11500, 13000, 15000, 18000, 20000, 22000, 25000, 
        33000, 41000, 50000, 62000, 75000, 90000, 105000, 120000, 135000, 155000],
    'PB': [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 
           4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 
           7, 7, 7, 7, 8, 8, 8, 8, 9, 9],
}

def ability_score_modifier(ability_score):
    return int(ability_score/2 - 5)

def construct_monster(html, rules=None, debugging=False):
    monster = {}
    s = splitup_html(html, debugging=debugging)
    if s['header']: monster.update(parse_header(s['header'], debugging=debugging))
    if s['meta']: monster.update(parse_meta(s['meta'], debugging=debugging))
    if s['attributes']: monster.update(parse_attributes(s['attributes'], debugging=debugging))
    if s['abilities']: monster.update(parse_abilities(s['abilities'], debugging=debugging))
    if s['tidbits']: monster.update(parse_tidbits(s['tidbits'], debugging=debugging))
    if s['traits']: monster.update(parse_traits(s['traits'], debugging=debugging))
    if s['actions']: monster.update(parse_actions(s['actions'], debugging=debugging))
    if s['bonus actions']: monster.update(parse_bonus_actions(s['bonus actions'], debugging=debugging))
    if s['reactions']: monster.update(parse_reactions(s['reactions'], debugging=debugging))
    if s['legendary actions']: monster.update(parse_legendary_actions(s['legendary actions'], debugging=debugging))
    if s['mythic actions']: monster.update(parse_mythic_actions(s['mythic actions'], debugging=debugging))
    if s['roleplaying information']: monster.update(parse_roleplaying_information(s['roleplaying information'], debugging=debugging))
    if s['figure']: monster.update(parse_figure(s['figure'], debugging=debugging))

    if rules == '2014':
        monster = convert_to_2014_format(monster)
    elif rules == '2024':
        monster = convert_to_2024_format(monster)
    
    return monster

def convert_to_2014_format(monster):
    """
    Changes a monster to 2014 rules format.

    Parameters
    ----------
    monster : dict
        The monster in dictionary form.
    
    rules : str
        The rule set to convert to.
    
    Returns
    -------
    monster : dict
        The monster in dictionary form.
    """
    if 'ac' in monster:
        monster['armor class'] = monster.pop('ac')
    
    if 'hp' in monster:
        monster['hit points'] = monster.pop('hp')

    if 'vulnerabilities' in monster:
        monster['damage vulnerabilities'] = monster.pop('vulnerabilities')

    if 'resistances' in monster:
        monster['damage resistances'] = monster.pop('resistances')

    if 'immunities' in monster:
        for group in monster.pop('immunities').split('; '):
            conditions = [
                'blinded','charmed','deafened','exhaustion','frightened','grappled','incapacitated',
                'invisible','paralyzed','petrified','poisoned','prone','restrained','stunned','unconscious',
            ]
            for condition in conditions:
                if condition in group:
                    monster['condition immunities'] = group
                    break
            else:
                monster['damage immunities'] = group

    if 'cr' in monster:
        monster['challenge'] = monster.pop('cr')
    
    if 'pb' in monster:
        monster['proficiency bonus'] = monster.pop('pb')

    key_list = [
        'id',
        'name',
        'size',
        'type',
        'subtype',
        'alignment',
        'armor class',
        'initiative',
        'hit points',
        'speed',
        'ability scores',
        'saving throws',
        'skills',
        'damage vulnerabilities',
        'damage resistances',
        'damage immunities',
        'condition immunities',
        'gear',
        'senses',
        'languages',
        'challenge',
        'xp',
        'proficiency bonus',
        'traits',
        'actions',
        'bonus actions',
        'reactions',
        'legendary actions',
        'mythic actions',
        'roleplaying information',
        'figure',
    ]
    return {k: monster[k] for k in key_list if k in monster}

def convert_to_2024_format(monster):
    """
    Changes a monster to 2024 rules format.

    Parameters
    ----------
    monster : dict
        The monster in dictionary form.
    
    rules : str
        The rule set to convert to.
    
    Returns
    -------
    monster : dict
        The monster in dictionary form.
    """
    if 'armor class' in monster:
        monster['ac'] = monster.pop('armor class')

    if 'challenge' in monster:
        monster['cr'] = monster.pop('challenge')

    if 'initiative' not in monster:
        monster['initiative'] = ability_score_modifier(monster['ability scores']['Dexterity'])

    if 'hit points' in monster:
        monster['hp'] = monster.pop('hit points')

    if 'damage vulnerabilities' in monster:
        monster['vulnerabilities'] = monster.pop('damage vulnerabilities')

    if 'damage resistances' in monster:
        monster['resistances'] = monster.pop('damage resistances')

    immunities = []
    if 'damage immunities' in monster:
        immunities.append(monster.pop('damage immunities'))

    if 'condition immunities' in monster:
        immunities.append(monster.pop('condition immunities'))

    if immunities:
        monster['immunities'] = '; '.join(immunities)

    if 'proficiency bonus' in monster:
        monster['pb'] = monster.pop('proficiency bonus')

    key_list = [
        'id',
        'name',
        'size',
        'type',
        'subtype',
        'alignment',
        'ac',
        'initiative',
        'hp',
        'speed',
        'ability scores',
        'saving throws',
        'skills',
        'vulnerabilities',
        'resistances',
        'immunities',
        'gear',
        'senses',
        'languages',
        'cr',
        'xp',
        'pb',
        'traits',
        'actions',
        'bonus actions',
        'reactions',
        'legendary actions',
        'mythic actions',
        'roleplaying information',
        'figure',
    ]
    return {k: monster[k] for k in key_list if k in monster}

def parse_header(html, debugging=False):
    soup = BeautifulSoup(html, 'html.parser')
    a = soup.find('a', {'class': 'tooltip-hover monster-tooltip'})
    return {
        'id': a['href'][10:] if a else None,
        'name': soup.get_text('', strip=True),
    }

def parse_meta(html, **kwargs):
    soup = BeautifulSoup(html, 'html.parser')
    m = re.match(
        r'\b(?P<size>small or medium|medium or small|huge or smaller|tiny|small|medium|large|huge|gargantuan)\b'
        r'\s*(?P<swarm>swarm of \w+)?'
        r'\s*\b(?P<type>\w+?)s?\b'
        r'\s*(?:\((?P<subtype>[^\)]+)\))?'
        r'\s*(?:,\s*(?P<alignment>[\w\s]+))?',
        soup.get_text(' ', strip=True),
        re.IGNORECASE,
    )
    return {
        'size': m['size'],
        'type': m['type'],
        'subtype': m['subtype'],
        'alignment': m['alignment'],
    }

def parse_attributes(html, **kwargs):
    """
    Parses a monster's attributes from html

    Parameters
    ----------
    html : str
        The attributes portion of the monster's html.
    
    Returns
    -------
    attributes : dict
        The monster's attributes.
    """
    soup = BeautifulSoup(html, 'html.parser')

    attributes = {}
    for c in soup.contents:
        for m in re.finditer(
                r'(?P<key>'
                    r'ac|armor class|hit points|hp|speed|initiative'
                r')\s+(?P<value>.*?)(?=$| initiative)',
                c.get_text(''),
                re.IGNORECASE,
            ):
            attributes[m['key'].lower()] = m['value'].lower()

    if 'speed' in attributes:
        speeds = {}
        for m in re.finditer(r'\b(?P<mode>[^\d]+) (?P<speed>\d+ ft.)', 'walk ' + attributes['speed'], re.IGNORECASE):
            speeds[m['mode'].title()] = m['speed']
        attributes['speed'] = speeds

    if 'initiative' in attributes:
        attributes['initiative'] = int(attributes['initiative'].split(' ')[0])

    return attributes

def parse_abilities(html, debugging=False):
    ABILITY_SCORE_DECODER = {
        'STR': 'Strength',
        'DEX': 'Dexterity',
        'CON': 'Constitution',
        'INT': 'Intelligence',
        'WIS': 'Wisdom',
        'CHA': 'Charisma'
    }
    html = html.replace('−', '-')
    html = html.replace('–', '-')
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.contents[0]

    abilities = {}
    if 'monster--stats' in tag['class']: # 389
        #print('v1')
        abilities['ability scores'] = {}

        c = tag.find('p')
        while c:
            ability = ABILITY_SCORE_DECODER[c.get_text(' ', strip=True).upper()]
            c = c.find_next_sibling('p')

            m = re.match(
                r'^'
                r'\s*(?P<score>\d+)'
                r'\s*(?:\((?P<modifier>[^\)]+)\))?',
                c.get_text(' ', strip=True),
                re.IGNORECASE,
            )
            score = int(m['score'])
            c = c.find_next_sibling('p')
            abilities['ability scores'][ability] = score
    
    elif 'stat-block-ability-scores' in tag['class']: # 1928
        #print('v2')
        abilities['ability scores'] = {}
        for div in tag.find_all('div', class_='stat-block-ability-scores-stat'):
            ability = div.find('div', class_='stat-block-ability-scores-heading').get_text(' ', strip=True)
            ability = ABILITY_SCORE_DECODER[ability.upper()]

            score = div.find('div', class_='stat-block-ability-scores-data').get_text(' ', strip=True)
            m = re.match(
                r'^'
                r'\s*(?P<score>\d+)'
                r'\s*(?:\((?P<modifier>[^\)]+)\))?',
                score,
                re.IGNORECASE)
            score = int(m['score'])
            abilities['ability scores'][ability] = score

    elif 'stats' in tag['class']: # 502
        #print('v3')
        abilities['ability scores'] = {}
        abilities['saving throws'] = {}
        for tr in tag.find_all('tr'):
            if debugging: print(tr.get_text(' ', strip=True))
            m = re.match(
                r'^'
                r'\s*(?P<ability>\w+)'
                r'\s+(?P<score>\d+)'
                r'\s+(?P<modifier>[+-]\d+)'
                r'\s+(?P<save>[+-]\d+)'
                r'\s*$',
                tr.get_text(' ', strip=True),
                re.IGNORECASE,
            )
            if not m: 
                #print(tr.get_text(' ', strip=True))
                continue

            ability = ABILITY_SCORE_DECODER.get(m.group('ability').upper(), m.group('ability').title())
            score = int(m.group('score'))
            abilities['ability scores'][ability] = score

            modifier = int(m.group('modifier'))
            save = int(m.group('save'))
            if modifier != save:
                abilities['saving throws'][ability] = save
    
    return abilities

def parse_tidbits(html, debugging=False):
    soup = BeautifulSoup(html, 'html.parser')

    tidbits = {}
    for c in soup.contents:
        for m in re.finditer(
                r'^(?P<key>'
                    r'Saving Throws|Skills|Condition Immunities|'
                    r'Damage Immunities|Damage Resistances|Damage Vulnerabilities|'
                    r'Immunities|Resistances|Vulnerabilities|'
                    r'Gear|'
                    r'Senses|Languages|Challenge Rating|Challenge|CR|'
                    r'Proficiency Bonus'
                r')\s+(?P<value>.*)$',
                c.get_text(''),
                re.IGNORECASE,
            ):
            key = m['key'].lower()
            key = 'challenge' if key == 'challenge rating' else key
            tidbits[key] = m['value'].lower()

    if 'cr' in tidbits:
        m = re.match(
            r'(?P<cr>[^\s]+)'
            r'(?:\s+\('
                r'(?:XP )?(?P<normal_xp>[\d,]+)(?: XP)?'
                r'(?:,? or (?P<special_xp>[\d,]+) (?P<special_place>in [^;]+))?'
                r'; PB (?P<proficiency>[^\)]+)'
            r'\))?',
            tidbits['cr'],
            re.IGNORECASE,
        )
        if m:
            tidbits['cr'] = m['cr']
            tidbits['xp'] = int(m.group('normal_xp').replace(',',''))
            tidbits['pb'] = m.group('proficiency')
            if len(tidbits['pb']) <= 3: tidbits['pb'] = int(tidbits['pb'])
            
        else:
            if debugging: print('cr', tidbits['cr'])
            raise Exception('CR parsing error')
        
    elif 'challenge' in tidbits:
        m = re.match(
            r'(?P<cr>[^\s]+)'
            r'(?:\s+\('
                r'(?P<normal_xp>[\d,]+) XP'
                #r'(?:, or (?P<special_xp>[\d,]+) (?P<special_place>in lair))'
            r'\))?',
            tidbits['challenge'],
            re.IGNORECASE,
        )
        if m:
            tidbits['challenge'] = m['cr']
            tidbits['xp'] = m.group('normal_xp')
            if tidbits['xp']: tidbits['xp'] = int(tidbits['xp'].replace(',',''))
        else:
            print('challenge', tidbits['cr'])
            raise Exception('Challenge parsing error')

        if not tidbits['xp']:
            if tidbits['challenge'] in MONSTER_DEFAULTS['CR']:
                tidbits['xp'] = MONSTER_DEFAULTS['XP'][MONSTER_DEFAULTS['CR'].index(tidbits['challenge'])]
        
        if 'proficiency bonus' not in tidbits:
            if tidbits['challenge'] in MONSTER_DEFAULTS['CR']:
                tidbits['proficiency bonus'] = MONSTER_DEFAULTS['PB'][MONSTER_DEFAULTS['CR'].index(tidbits['challenge'])]


    if 'saving throws' in tidbits:
        ABILITY_SCORE_DECODER = {
            'STR': 'Strength',
            'DEX': 'Dexterity',
            'CON': 'Constitution',
            'INT': 'Intelligence',
            'WIS': 'Wisdom',
            'CHA': 'Charisma'
        }
        saving_throws = {}
        for m in re.finditer(r'(?P<ability>[A-Z]+)\s+(?P<bonus>[+-]\d+)', tidbits['saving throws'], re.IGNORECASE):
            saving_throws[ABILITY_SCORE_DECODER.get(m['ability'].upper(), m['ability'].title())] = int(m['bonus'])
        tidbits['saving throws'] = saving_throws

    if 'skills' in tidbits:
        skills = {}
        for m in re.finditer(r'(?P<skill>[A-Z]+)\s+(?P<bonus>[+-]\d+)', tidbits['skills'], re.IGNORECASE):
            skills[m['skill'].title()] = int(m['bonus'])
        tidbits['skills'] = skills

    if 'senses' in tidbits:
        senses = {}
        for m in re.finditer(r'\b(?P<sense>[\w\s]+) (?P<value>\d+(?: ft.(?: \([^\)]+\))?)?)', tidbits['senses'], re.IGNORECASE):
            senses[m['sense'].title()] = m['value']
        if 'Passive Perception' in senses:
            senses['Passive Perception'] = int(senses['Passive Perception'])
        else:
            if debugging: print(tidbits['senses'])
        tidbits['senses'] = senses

    if debugging: print(tidbits)
    return tidbits

def parse_traits(html, **kwargs):
    debugging = kwargs.get('debugging', False)

    re_trait = re.compile(
        r'^\s*(?P<full_name>'
            r'(?P<name>'
                r'(?:[A-Z][^\.\s]+|\+\d)'
                r'(?:'
                    r'\s+(?:[A-Z][^\,\.\s]+|and|at|a|but|by|for|from|in|of|on|or|the|through|to|with)\,?'
                r')*'
            r')'
            r'(?:\s+\((?P<params>[^\)]+)\))?'
        r')'
        r'\s*[\.\?]'
        r'\s*(?P<description>.*)$',
    )

    def _line_type(tag, **kwargs):
        if tag.name in ['ol','ul']:
            return 'list'
        if tag.name == 'li':
            return 'option'

        tags = []
        tag_names = []
        if tag.name:
            if len(tag.contents) == 0:
                print(tag)
            c0 = tag.contents[0]
            if c0.name:
                tags.append(c0)
                tag_names.append(c0.name)
                c1 = c0.contents[0]
                if c1.name:
                    tags.append(c1)
                    tag_names.append(c1.name)

        if tag_names == ['strong','em']:
            return 'trait'
        elif tag_names == ['em','strong']:
            return 'trait'
        elif tag_names == ['strong']:
            return 'option'
        elif tag_names == ['em']:
            if ':' in c0.get_text():
                return 'description'
            elif '.' in c0.get_text():
                return 'option'
            else:
                return 'unknown'
        elif tag_names == ['em','span']:
            if 'Serif-Character-Style_Inline-Subhead-Serif' in c1.get('class', []):
                return 'trait'
            else:
                return 'unknown'
        elif tag_names == ['span']:
            if 'Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif' in c0.get('class', []):
                return 'trait'
            elif 'Sans-Serif-Character-Styles_Bold-Italic-Sans-Serif' in c0.get('class', []):
                return 'trait'
            elif 'Serif-Character-Style_Inline-Subhead-Serif' in c0.get('class', []):
                return 'trait'
            elif 'Sans-Serif-Character-Styles_Bold-Sans-Serif' in c0.get('class', []):
                return 'option'
            else:
                return 'unknown'
        elif tag_names == ['span','a']:
            if 'Sans-Serif-Character-Styles_Inline-Subhead-Sans-Serif' in c0.get('class', []):
                return 'trait'
            elif 'Sans-Serif-Character-Styles_Bold-Italic-Sans-Serif' in c0.get('class', []):
                return 'trait'
            elif 'Serif-Character-Style_Inline-Subhead-Serif' in c0.get('class', []):
                return 'trait'
            elif 'Sans-Serif-Character-Styles_Bold-Sans-Serif' in c0.get('class', []):
                return 'option'
            else:
                return 'unknown'
        elif tag_names == []:
            return 'description'
        else:
            return 'unknown'

    html = html.replace('\n','')
    if len(html) == 0:
        return {'traits': []}
    
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.contents[0]

    traits = []

    # find section description
    trait = dict(name='description', description=[])
    while tag:
        line_type = _line_type(tag)
        if line_type == 'description':
            traits.append(tag.get_text().strip())
            #trait['description'].append(tag.get_text().strip())
        elif line_type in ['trait','option']:
            break
        else:
            pass
        tag = tag.next_sibling
    if debugging: print(trait)
    if trait['description']:
        traits.append(trait)
    
    # find traits
    while tag:
        m = re_trait.match(tag.get_text())
        if not m:
            if debugging: print(tag.get_text())
        trait = dict(name=m['full_name'], description=[m['description']])
        tag = tag.next_sibling
        while tag:
            line_type = _line_type(tag)
            if line_type == 'option':
                trait['description'].append(tag.get_text())
            elif line_type == 'description':
                trait['description'].append(tag.get_text())
            elif line_type == 'list':
                #trait['description'].append({
                #    'content_type': 'List',
                #    'html': str(tag),
                #})
                options = []
                item = {}
                for li in tag.find_all('li'):
                    item_type = _line_type(li)
                    if item_type in ['trait','option']:
                        if item: options.append(item)
                        m = re_trait.match(li.get_text())
                        if m:
                            item = dict(name=m['full_name'], description=[m['description']])
                        else:
                            item = li.get_text().strip()
                    else:
                        item['description'].append(li.get_text().strip())
                if item: options.append(item)

                trait['description'].append({
                    'list_type': 'ordered' if tag.name == 'ol' else 'unordered',
                    'list_items': options,
                })
                
            elif line_type == 'trait':
                break
            else:
                pass
            tag = tag.next_sibling
        if debugging: print(trait)
        traits.append(trait)

    return {'traits': traits}

def parse_actions(html, **kwargs):
    return {'actions': parse_traits(html, **kwargs)['traits']}

def parse_bonus_actions(html, **kwargs):
    return {'bonus actions': parse_traits(html, **kwargs)['traits']}

def parse_reactions(html, **kwargs):
    return {'reactions': parse_traits(html, **kwargs)['traits']}

def parse_legendary_actions(html, **kwargs):
    return {'legendary actions': parse_traits(html, **kwargs)['traits']}

def parse_mythic_actions(html, **kwargs):
    return {'mythic actions': parse_traits(html, **kwargs)['traits']}

def parse_roleplaying_information(html, **kwargs):
    debugging = kwargs.get('debugging', False)

    def _line_type(tag, **kwargs):
        if re.match(
                r'\s*(Ideal|Bond|Flaw):',
                tag.get_text(),
            ):
            return 'trait'
        else:
            return 'description'

    html = html.replace('\n','')
    if len(html) == 0:
        return {'roleplaying information': []}
    
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.contents[0]

    traits = []

    # find section description
    trait = dict(name='description', description=[])
    while tag:
        line_type = _line_type(tag)
        if line_type == 'description':
            trait['description'].append(tag.get_text())
        elif line_type == 'trait':
            break
        else:
            pass
        tag = tag.next_sibling
    if trait['description']:
        traits.append(trait)
    
    # find traits
    while tag:
        m = re.match(
            r'^\s*(?P<full_name>'
                r'Ideal|Bond|Flaw'
            r')'
            r'\s*:'
            r'\s*(?P<description>.*)$',
            tag.get_text(),
        )
        if not m:
            if debugging: print(tag.get_text())
        trait = dict(name=m['full_name'], description=[m['description']])
        tag = tag.next_sibling
        while tag:
            line_type = _line_type(tag)
            if line_type == 'description':
                trait['description'].append(tag.get_text())
            elif line_type == 'trait':
                break
            else:
                pass
            tag = tag.next_sibling
        if debugging: print(trait)
        traits.append(trait)

    return {'roleplaying information': traits}

def parse_figure(html, **kwargs):
    debugging = kwargs.get('debugging', False)

    soup = BeautifulSoup(html, 'html.parser')

    figure = {}

    tag = soup.find('span', class_='artist-credit')
    if tag: figure['artist'] = tag.get_text()

    tag = soup.find('img')
    if tag: figure['src'] = tag['src']

    tag = soup.find('figcaption')
    if tag: figure['caption'] = tag.get_text()

    if figure and debugging:
        print(figure)
    
    return {'figure': figure}

def splitup_html(html, debugging=False):
    sections = {
        'header': '',
        'meta': '',
        'attributes': '',
        'abilities': '',
        'tidbits': '',
        'traits': '',
        'actions': '',
        'bonus actions': '',
        'reactions': '',
        'legendary actions': '',
        'mythic actions': '',
        'roleplaying information': '',
        'figure': '',
    }

    soup = BeautifulSoup(html.replace('\n',''), 'html.parser')
    if soup.contents[0].name == 'div':
        soup.contents[0].unwrap()

    # header
    tag = soup.contents[0]
    sections['header'] = str(tag)
    if debugging: print(str(tag))

    # meta
    tag = tag.next_sibling
    sections['meta'] = str(tag)
    if debugging: print(str(tag))

    # attributes
    tag = tag.next_sibling
    while tag.name != 'div':
        sections['attributes'] += str(tag)
        if debugging: print(str(tag))
        tag = tag.next_sibling

    # ability scores
    sections['abilities'] = str(tag)

    # tidbits
    tag = tag.next_sibling
    while tag:
        if tag.get_text(' ', strip=True).lower() in sections:
            break
        else:
            sections['tidbits'] += f'\n{str(tag)}'
        tag = tag.next_sibling

    # the rest
    while tag:
        #print(tag)
        section = tag.get_text(' ', strip=True).lower()
        if section in sections:
            #s = BeautifulSoup('', 'html.parser')
            tag = tag.next_sibling
            while tag:
                #if not tag.name: continue
                #print(tag)
                if tag.get_text(' ', strip=True).lower() in sections:
                    break
                elif tag.name in ['figure']:
                    break
                elif tag.name in ['a'] and 'ddb-lightbox-outer' in tag['class']:
                    break
                else:
                    sections[section] += f'\n{str(tag)}'
                
                tag = tag.next_sibling

        elif tag.name == 'figure':
            sections['figure'] += f'{str(tag)}'
            tag = tag.next_sibling
        elif tag.name == 'a':
            sections['figure'] += f'{str(tag)}'
            tag = tag.next_sibling
        else:
            tag = tag.next_sibling

    return sections