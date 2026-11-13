from .content import *
from .__monster_parser import construct_monster
import re

def ability_score_modifier(ability_score):
    return int(ability_score/2 - 5)

class Monster(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.url = kwargs.get('url', None)
        self.book_path = kwargs.get('book_path', None)

        self.size = kwargs.get('size', None)
        self.type = kwargs.get('type', None)
        self.subtype = kwargs.get('subtype', None)
        self.alignment = kwargs.get('alignment', None)

        self.armor_class = kwargs.get('armor class', None)
        self.initiative = kwargs.get('initiative', None)
        self.hit_points = kwargs.get('hit points', None)
        self.speed = kwargs.get('speed', {})

        self.ability_scores = kwargs.get('ability scores', {})

        self.saving_throws = kwargs.get('saving throws', {})
        self.skills = kwargs.get('skills', {})
        self.damage_vulnerabilities = kwargs.get('damage vulnerabilities', None)
        self.damage_resistances = kwargs.get('damage resistance', None)
        self.damage_immunities = kwargs.get('damage immunities', None)
        self.condition_immunities = kwargs.get('condition immunities', None)
        self.gear = kwargs.get('gear', None)
        self.senses = kwargs.get('senses', {})
        self.languages = kwargs.get('language', None)
        self.challenge = kwargs.get('challenge', None)
        self.xp = kwargs.get('xp', None)
        self.proficiency_bonus = kwargs.get('proficiency bonus', None)

        self.traits = kwargs.get('traits', [])
        self.actions = kwargs.get('actions', [])
        self.bonus_actions = kwargs.get('bonus actions', [])
        self.reactions = kwargs.get('reactions', [])
        self.legendary_actions = kwargs.get('legendary actions', [])
        self.mythic_actions = kwargs.get('mythic actions', [])
        self.roleplaying_information = kwargs.get('roleplaying information', [])
        self.figure = kwargs.get('figure', None)

        self.html = kwargs.get('html', None)
        if self.html: self.__process_html(**kwargs)

    def __repr__(self):
        return f'{self.to_dict()}'

    def __getitem__(self, key):
        return self.__dict__[key.replace(' ', '_')]
    
    def __setitem__(self, key, value):
        self.__dict__[key.replace(' ', '_')] = value

    def __process_html(self, **kwargs):
        mon = construct_monster(self.html, rules='2014', debugging=kwargs.get('debugging', False))

        for k, v in mon.items():
            self[k] = v

        if not self.initiative:
            if 'Dexterity' in self.ability_scores:
                self.initiative = ability_score_modifier(self.ability_scores['Dexterity'])
    
    def to_dict(self):
        return {
            'content_type': 'Monster',
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'book path': self.book_path,
            'size': self.size,
            'type': self.type,
            'subtype': self.subtype,
            'alignment': self.alignment,
            'armor class': self.armor_class,
            'initiative': self.initiative,
            'hit points': self.hit_points,
            'speed': self.speed,
            'ability scores': self.ability_scores,
            'saving throws': self.saving_throws,
            'skills': self.skills,
            'damage vulnerabilities': self.damage_vulnerabilities,
            'damage resistances': self.damage_resistances,
            'damage immunities': self.damage_immunities,
            'condition immunities': self.condition_immunities,
            'gear': self.gear,
            'senses': self.senses,
            'languages': self.languages,
            'challenge': self.challenge,
            'xp': self.xp,
            'proficiency bonus': self.proficiency_bonus,
            'traits': self.traits,
            'actions': self.actions,
            'bonus actions': self.bonus_actions,
            'reactions': self.reactions,
            'legendary actions': self.legendary_actions,
            'mythic actions': self.mythic_actions,
            'roleplaying information': self.roleplaying_information,
            'figure': self.figure,
        }

    def challenge_rating(self):
        """
        Monster CR in decimal form.

        Returns
        -------
        cr : float
            The monster's challenge rating in decimal form. Returns ``None`` if missing.
        """
        if type(self.challenge) is not str:
            return None
        
        m = re.match(r'(?P<numerator>\d+)(?:/(?P<denominator>\d+))?', self.challenge)
        if m:
            n, d = m.groups(1)
            return n/d
        else:
            return None
    
    def is_legendary(self):
        """
        Returns ``True`` if the monster is legendary.

        Returns
        -------
        ans : bool
            ``True`` if the monster has any legendary actions.
        """
        if self.legendary_actions:
            return True
        else:
            return False

    def is_mythic(self):
        """
        Returns ``True`` if the monster is mythic.

        Returns
        -------
        ans : bool
            ``True`` if the monster has any mythic actions.
        """
        if self.mythic_actions:
            return True
        else:
            return False

    def to_str(self, rules='2024'):
        """
        Converts the monster to a plain text string.

        Parameters
        ----------
        rules : str
            Determines how the stat block is formatted, either ``'2014'`` or ``'2024'``. 
            If ``'2014'`` the stat block will be formatted to match monsters published under the 2014 rules (5e), 
            and if ``'2024'`` the format will match those published under the 2024 rules (5.5e).
            Default value ``'2024'``.
        
        Returns
        -------
        text : str
            Plain text monster stat block.
        """
        pt = []
        
        # name
        pt.append(self.name)

        if self.subtype:
            pt.append(f'{self.size} {self.type} ({self.subtype}), {self.alignment}')
        else:
            pt.append(f'{self.size} {self.type}, {self.alignment}')

        pt.append(f'Armor Class {self.armor_class}')
        
        pt.append(f'Initiative {self.initiative:+d}')
        
        pt.append(f'Hit Points {self.hit_points}')

        speed = ', '.join([f'{k} {v}' for k, v in self.speed.items()])
        pt.append(f'Speed {speed[5:]}')
        pt.append('')

        ## abilities
        def ability_score_modifier(ability_score):
            return int(ability_score/2 - 5)

        if rules == '2014':
            for k, v in self.ability_scores.items(): # 2014
                pt.append(f'{k[0:3].upper()} {v} ({ability_score_modifier(int(v)):+d})')
        elif rules == '2024':
            pt.append(f'Ability Mod Save')
            for k, v in self.ability_scores.items():
                m = ability_score_modifier(int(v))
                s = self.saving_throws.get(k, m)
                pt.append(f'{k[0:3].upper()} {v:3d}{m:+4d}{s:+5d}')
        pt.append('')

        ## tidbits
        if self.saving_throws: 
            if rules == '2014':
                pt.append('Saving Throws ' + ', '.join([f'{k[0:3].upper()} {v:+d}' for k, v in self.saving_throws.items()]))
        
        if self.skills: pt.append('Skills ' + ', '.join([f'{k} {v:+d}' for k, v in self.skills.items()]))

        if self.damage_vulnerabilities: 
            if rules == '2014':
                pt.append(f'Damage Vulnerabilities {self.damage_vulnerabilities}')
            elif rules == '2024':
                pt.append(f'Vulnerabilities {self.damage_vulnerabilities}')
        
        if self.damage_resistances: 
            if rules == '2014':
                pt.append(f'Damage Resistances {self.damage_resistances}')
            elif rules == '2024':
                pt.append(f'Resistances {self.damage_resistances}')

        if rules == '2014':
            if self.damage_immunities: 
                pt.append(f'Damage Immunities {self.damage_immunities}')
            
            if self.condition_immunities: 
                pt.append(f'Condition Immunities {self.condition_immunities}')

        elif rules == '2024':
            immunities = []
            if self.damage_immunities:    immunities.append(self.damage_immunities)
            if self.condition_immunities: immunities.append(self.condition_immunities)
            if immunities:
                pt.append('Immunities ' + '; '.join(immunities))
        
        if self.senses:
            if rules == '2014':
                pt.append('Senses ' + ', '.join([f'{k} {v}' for k, v in self.senses.items()]))
            
            elif rules == '2024': 
                senses = ', '.join([f'{k} {v}' for k, v in self.senses.items() if k != 'Passive Perception'])
                senses += '; Passive Perception ' + str(self.senses['Passive Perception'])
                pt.append(f'Senses {senses}')
        
        if self.languages: pt.append(f'Languages {self.languages}')

        if type(self.proficiency_bonus) is int:
            pb = f'{self.proficiency_bonus:+d}'
        else:
            pb = f'{self.proficiency_bonus}'
        
        if self.challenge:
            if rules == '2014':
                pt.append(f'Challenge {self.challenge} ({self.xp:,d} XP)')
            elif rules == '2024':
                pt.append(f'Challenge {self.challenge} (XP {self.xp}; PB {pb})')
        
        if self.proficiency_bonus:
            if rules == '2014':
                pt.append(f'Proficiency Bonus {pb}')

        pt.append('')

        def feature_to_str(f):
            if type(f) is str: return f

            name = f['name']
            ft = []
            for line in f['description']:
                if type(line) is dict:
                    ft.append(option_list_to_str(line))
                else:
                    ft.append(line)
            return f'{name}. ' + '\n'.join(ft)

        def option_list_to_str(option_list):
            list_type = option_list['list_type']
            i = 0
            ot = []
            for li in option_list['list_items']:
                i += 1
                prefix = f' {i}.' if list_type == 'ordered' else ' *'
                ot.append(f'{prefix} {feature_to_str(li)}')
            return '\n'.join(ot)

        # traits
        if self.traits:
            pt.append('Traits')
            for trait in self.traits:
                pt.append(feature_to_str(trait))
            pt.append('')

        # actions
        if self.actions:
            pt.append('Actions')
            for action in self.actions:
                pt.append(feature_to_str(action))
            pt.append('')

        # bonus actions
        if self.bonus_actions:
            pt.append('Bonus Actions')
            for action in self.bonus_actions:
                pt.append(feature_to_str(action))
            pt.append('')

        # reactions
        if self.reactions:
            pt.append('Reactions')
            for action in self.reactions:
                pt.append(feature_to_str(action))
            pt.append('')

        # legendary actions
        if self.legendary_actions:
            pt.append('Legendary Actions')
            for action in self.legendary_actions:
                pt.append(feature_to_str(action))
            pt.append('')

        # legendary actions
        if self.mythic_actions:
            pt.append('Mythic Actions')
            for action in self.mythic_actions:
                pt.append(feature_to_str(action))
            pt.append('')

        # roleplaying information
        if self.roleplaying_information:
            pt.append('Roleplaying Information')
            for action in self.roleplaying_information:
                pt.append(feature_to_str(action))
            pt.append('')
        
        return '\n'.join(pt)