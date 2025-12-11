class BitStream:
    """Gère l'écriture de bits et la conversion Base64 spécifique à Guild Wars."""
    def __init__(self):
        self.data = 0
        self.bit_count = 0

    def write(self, value, num_bits):
        # Guild Wars stocke les données en Little Endian
        self.data |= (value << self.bit_count)
        self.bit_count += num_bits

    def get_gw_base64(self):
        # Alphabet Base64 standard
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        encoded = ""
        temp_data = self.data
        current_bits = self.bit_count
        
        # On découpe par tranches de 6 bits pour obtenir les caractères
        while current_bits > 0:
            val = temp_data & 0x3F # Masque pour prendre les 6 premiers bits
            encoded += chars[val]
            temp_data >>= 6
            current_bits -= 6
        return encoded

class BuildTemplate:
    """
    Génère un Template Code Guild Wars 1 valide.
    Gère la conversion ID Global -> ID Local.
    """
    
    PROFS = {
        'None': 0, 'Warrior': 1, 'Ranger': 2, 'Monk': 3, 'Necromancer': 4,
        'Mesmer': 5, 'Elementalist': 6, 'Assassin': 7, 'Ritualist': 8,
        'Paragon': 9, 'Dervish': 10
    }

    # MAPPING: Global ID (CSV) -> Local ID (0-15 pour le Template)
    # Basé sur l'ordre standard des attributs dans le jeu (Primary = toujours 0)
    ATTR_MAP = {
        # Mesmer
        0: 0, # Fast Casting (Primary)
        1: 1, 2: 2, 3: 3, # Illusion, Domination, Inspiration
        
        # Necromancer
        6: 0, # Soul Reaping (Primary)
        7: 1, 5: 2, 4: 3, # Curses, Death, Blood (Ordre std: Curses, Death, Blood)
        
        # Elementalist
        12: 0, # Energy Storage (Primary)
        8: 1, 9: 2, 10: 3, 11: 4, # Air, Earth, Fire, Water
        
        # Monk
        16: 0, # Divine Favor (Primary)
        13: 1, 14: 2, 15: 3, # Healing, Smiting, Protection
        
        # Warrior
        17: 0, # Strength (Primary)
        18: 1, 19: 2, 20: 3, 21: 4, # Axe, Hammer, Sword, Tactics
        
        # Ranger
        23: 0, # Expertise (Primary)
        22: 1, 24: 2, 25: 3, # Beast, Wilderness, Marksmanship
        
        # Assassin
        35: 0, # Critical Strikes (Primary)
        29: 1, 30: 2, 31: 3, # Dagger, Deadly, Shadow
        
        # Ritualist
        36: 0, # Spawning Power (Primary)
        32: 1, 33: 2, 34: 3, # Communing, Restoration, Channeling
        
        # Paragon
        40: 0, # Leadership (Primary)
        37: 1, 38: 2, 39: 3, # Spear, Command, Motivation
        
        # Dervish
        44: 0, # Mysticism (Primary)
        41: 1, 42: 2, 43: 3  # Scythe, Wind, Earth
    }

    def __init__(self):
        self.primary_prof = 0
        self.secondary_prof = 0
        self.attributes = [] 
        self.skills = [0] * 8 

    def set_profession(self, primary, secondary='None'):
        # Gestion hybride : ID (int) ou Nom (str)
        if isinstance(primary, int): self.primary_prof = primary
        else: self.primary_prof = self.PROFS.get(primary, 0)

        if isinstance(secondary, int): self.secondary_prof = secondary
        else: self.secondary_prof = self.PROFS.get(secondary, 0)

    def add_attribute(self, global_id, value):
        # C'est ici que la magie opère : on convertit l'ID global (ex: 44) en local (0)
        local_id = self.ATTR_MAP.get(global_id)
        
        if local_id is None:
            # Fallback de sécurité : si l'ID est inconnu, on le met à 0 pour éviter le crash
            # Cela permet de débuguer si votre CSV contient un ID exotique
            local_id = 0 
        
        self.attributes.append((local_id, value))

    def set_skills(self, skill_ids):
        # Sécurité : remplit avec des 0 si moins de 8 skills
        if len(skill_ids) < 8:
            skill_ids += [0] * (8 - len(skill_ids))
        self.skills = skill_ids[:8]

    def generate_code(self):
        stream = BitStream()
        
        # 1. Header (Type 14, Version 0) - Ordre strict
        stream.write(14, 4) 
        stream.write(0, 4)  

        # 2. Profession Length (2 bits) -> 0 = Standard
        stream.write(0, 2)

        # 3. Professions (4 bits each)
        stream.write(self.primary_prof, 4)
        stream.write(self.secondary_prof, 4)

        # 4. Attribute Count (4 bits)
        stream.write(len(self.attributes), 4)

        # 5. Attributes (4 bits LocalID + 4 bits Value)
        for local_id, value in self.attributes:
            stream.write(local_id, 4)
            stream.write(value, 4)

        # 6. Skills (12 bits each)
        for skill_id in self.skills:
            stream.write(skill_id, 12)

        return stream.get_gw_base64()
