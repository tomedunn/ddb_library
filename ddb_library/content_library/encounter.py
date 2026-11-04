from .content import *
from bs4 import BeautifulSoup
import numpy as np
import re
import uuid

class Encounter(Content):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.type = kwargs.get('type', None)
        self.book_path = kwargs.get('book_path', None)
        self.allies = kwargs.get('allies', [])
        self.bystanders = kwargs.get('bystanders', [])
        self.enemies = kwargs.get('monsters', [])
        self.enemies = kwargs.get('enemies', self.enemies)
        self.html = kwargs.get('html', None)

        if self.html: self.__process_html()

    def __repr__(self):
        return f'{self.to_dict()}'

    def to_dict(self):
        return {
            'content_type': 'Encounter',
            'id': self.id,
            'book_path': self.book_path,
            'type': self.type,
            'allies': self.allies,
            'bystanders': self.bystanders,
            'enemies': self.enemies,
        }

    def __process_html(self):
        TEXT_TO_NUMBER = {
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5,
            'six': 6,
            'seven': 7,
            'eight': 8,
            'nine': 9,
            'ten': 10,
            'eleven': 11,
            'twelve': 12,
            'dozen': 12,
            'thirteen': 13,
            'fourteen': 14,
            'fifteen': 15,
            'sixteen': 16,
            'seventeen': 17,
            'eighteen': 18,
            'nineteen': 19,
            'twenty': 20,
            '.': 1,
        }

        soup = BeautifulSoup(self.html, 'html.parser')

        enemies = []
        number = 1
        monster = ''
        for tag in soup.contents:
            if not tag.name: continue
            for c in tag.contents:
                if c.name == 'a':
                    if 'monster-tooltip' not in c.get('class', []): continue
                    monster = c['href'].split('/')[-1]
                    m = re.match(r'^(?P<id_num>\d+)-.*$', monster)
                    if not m: continue
                    enemies += [(number, monster)]
                    number = 1
                elif not c.name:
                    m = re.match(r'.*\b(?P<number>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|\.)\b', c.get_text('', strip=False), re.IGNORECASE)
                    if not m: continue
                    number = m['number'].lower()
                    if re.match(r'\d+', number):
                        number = int(number)
                    else:
                        number = TEXT_TO_NUMBER.get(number, 1)
                elif c.name == 'span':
                    if 'plural-monster-tooltip' in c.get('class', ''):
                        if 'monster-tooltip' not in c.a.get('class', []): continue
                        monster = c.a['href'].split('/')[-1]
                        m = re.match(r'^(?P<id_num>\d+)-.*$', monster)
                        if not m: continue
                        enemies += [(number, monster)]
                        number = 1

                else:
                    pass

        self.enemies = enemies
        
    def allies_xp_values(self):
        """
        Returns a list of XP values for the ally monsters in the encounter.

        Returns
        ----------
        xp_vals : list
            The XP values for each ally monster in the encounter.
        """
        xp_vals = []
        for monster in self.allies:
            xp_vals.extend(monster[0]*[monster[2]])
        
        return xp_vals

    def enemy_cr_values_from_xp(self):
        """
        Returns a list of CR values for the enemy monsters in the encounter.

        These CR values are determined from the monsters' XP values, which may differ from the default values for each CR.

        Returns
        ----------
        cr_vals : list
            The CR values for each enemy monster in the encounter.
        """
        XP_VALS = [0, 25, 50, 100, 200, 450, 700, 1100, 1800, 2300, 2900, 3900, 5000, 
            5900, 7200, 8400, 10000, 11500, 13000, 15000, 18000, 20000, 22000, 25000, 
            33000, 41000, 50000, 62000, 75000, 90000, 105000, 120000, 135000, 155000]
        CR_VALS = [0, 1/8, 1/4, 1/2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 
            14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
        
        def _find_nearest_loc(array, value):
            array = np.asarray(array)
            idx = (np.abs(array - value)).argmin()
            return idx
        
        cr_vals = []
        for xp in self.enemy_xp_values():
            id = _find_nearest_loc(XP_VALS, xp)
            cr_vals.append(CR_VALS[id])
        return cr_vals

    def enemy_monster_ids(self):
        """
        Returns a list of monster Ids for the enemy monsters in the encounter.

        Returns
        ----------
        ids : list
            The monster ids for each enemy monster in the encounter.
        """
        ids = []
        for monster in self.enemies:
            ids.extend(monster[0]*[monster[1]])
        
        return ids
    
    def enemy_xp_values(self):
        """
        Returns a list of XP values for the enemy monsters in the encounter.

        Returns
        ----------
        xp_vals : list
            The XP values for each enemy monster in the encounter.
        """
        xp_vals = []
        for monster in self.enemies:
            xp_vals.extend(monster[0]*[monster[2]])
        
        return xp_vals

    def enemy_xp_total(self):
        """
        Returns the total XP value of all enemy monsters in the encounter.

        Returns
        ----------
        xp_total : float
            The total of all enemy monster XP values in the encounter.
        """
        
        return sum(self.enemy_xp_values())

    def adjusted_enemy_xp_total(self, pc_levels, rules='2014'):
        """
        Returns the adjusted XP total for the encounter.

        Parameters
        ----------
        pc_levels : list
            The level of each PC in the encounter.
        
        rules : str
            The version of the encounter building rules used for the calculation. Default value ``'2014'``.

        Returns
        ----------
        xp_total : float
            The adjusted total XP for the encounter.
        """
        def encounter_multiplier_2024_DMG(pc_count, npc_count):
            """Returns the encounter multiplier given by the DMG
            pc_count -- number of PCs in the encounter
            npc_count -- number of NPCs in the encounter
            """
            n_array = np.asarray([1,2,3,7,11,15])
            m_array = np.asarray([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0])
            i = 1 + n_array[n_array <= max(npc_count,1)].argmax()
            if pc_count >= 6:
                i -= 1
            elif pc_count <= 2:
                i += 1
            return m_array[i]
        
        if rules == '2014':
            em = encounter_multiplier_2024_DMG(len(pc_levels), len(self.enemy_xp_values()))
            return em*self.enemy_xp_total()
        elif rules == '2024':
            return self.enemy_xp_total()
        elif rules == 'tfb':
            xp_vals = self.enemy_xp_values()
            xp_total = sum(xp_vals)
            xp_square = sum(np.sqrt(xp_vals))**2
            xp_multi = 0.5*(xp_square - xp_total)
            return xp_total + xp_multi*0.3