from .content import *
from .__monster_parser import construct_monster
import re

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
        self.speed = kwargs.get('speed', None)

        self.ability_scores = kwargs.get('ability scores', None)

        self.saving_throws = kwargs.get('saving throws', None)
        self.skills = kwargs.get('skills', None)
        self.damage_vulnerabilities = kwargs.get('damage vulnerabilities', None)
        self.damage_resistances = kwargs.get('damage resistance', None)
        self.damage_immunities = kwargs.get('damage immunities', None)
        self.condition_immunities = kwargs.get('condition immunities', None)
        self.gear = kwargs.get('gear', None)
        self.senses = kwargs.get('senses', None)
        self.languages = kwargs.get('language', None)
        self.challenge = kwargs.get('challenge', None)
        self.xp = kwargs.get('xp', None)
        self.proficiency_bonus = kwargs.get('proficiency bonus', None)

        self.traits = kwargs.get('traits', None)
        self.actions = kwargs.get('actions', None)
        self.bonus_actions = kwargs.get('bonus actions', None)
        self.reactions = kwargs.get('reactions', None)
        self.legendary_actions = kwargs.get('legendary actions', None)
        self.mythic_actions = kwargs.get('mythic actions', None)
        self.roleplaying_information = kwargs.get('roleplaying information', None)
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