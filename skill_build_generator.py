class BitStream:
    def __init__(self):
        self.data = 0
        self.bit_count = 0

    def write(self, value, num_bits):
        # Écrit les bits du LSB vers le MSB
        self.data |= (value << self.bit_count)
        self.bit_count += num_bits

    def get_gw_base64(self):
        # Encodage spécifique à Guild Wars (tranches de 6 bits)
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        encoded = ""
        temp_data = self.data
        # On traite tant qu'il reste des bits (même si < 6, on prend ce qui reste)
        current_bits = self.bit_count
        while current_bits > 0:
            val = temp_data & 0x3F # Prend les 6 derniers bits
            encoded += chars[val]
            temp_data >>= 6
            current_bits -= 6
        return encoded

class BuildTemplate:
    def __init__(self):
        self.primary_prof = 0
        self.secondary_prof = 0
        self.attributes = [] 
        self.skills = [0] * 8
        
        # MAPPING ESSENTIEL : Global ID -> Local ID (Index)
        # Pour que cela marche avec toutes les classes, cette liste doit être complète.
        # Voici les IDs pour Derviche et Parangon basés sur le Wiki.
        self.ATTR_MAP = {
            # Dervish (Prof 10)
            44: 0, # Mysticism
            41: 1, # Scythe Mastery
            42: 2, # Wind Prayers
            43: 3, # Earth Prayers
            
            # Paragon (Prof 9)
            36: 0, # Leadership
            37: 1, # Spear Mastery
            38: 2, # Command
            39: 3, # Motivation
            
            # Warrior (Exemple pour montrer la logique)
            1: 0, # Strength
            2: 1, # Axe
            # ... à compléter pour un usage complet
        }

    def set_profession(self, primary, secondary):
        self.primary_prof = primary
        self.secondary_prof = secondary

    def add_attribute(self, global_attr_id, value):
        # Conversion automatique Global ID -> Local ID
        local_id = self.ATTR_MAP.get(global_attr_id)
        
        if local_id is None:
            # Fallback si l'ID n'est pas dans notre map (risque d'erreur in-game)
            # On suppose que c'est déjà un ID local si < 16
            local_id = global_attr_id if global_attr_id < 16 else 0
            print(f"Warning: Attribute {global_attr_id} not mapped. Using {local_id}.")
            
        self.attributes.append((local_id, value))

    def set_skills(self, skill_ids):
        if len(skill_ids) < 8:
            skill_ids += [0] * (8 - len(skill_ids))
        self.skills = skill_ids[:8]

    def generate_code(self):
        stream = BitStream()
        
        # 1. Header (Type 14, Version 0)
        # GW écrit Type (4) puis Version (4).
        # En binaire Little Endian dans le stream : Version(0) << 4 | Type(14) ??
        # Non, l'ordre d'écriture est strict : Type d'abord.
        stream.write(14, 4) # Type 14 (0xE)
        stream.write(0, 4)  # Version 0

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

# --- TEST AVEC VOS DONNEES ---

build = BuildTemplate()
build.set_profession(10, 9) # Dervish/Paragon

# Le script va maintenant convertir ces IDs globaux en IDs locaux (0, 1, 2, 3...)
build.add_attribute(43, 12) # Earth Prayers
build.add_attribute(41, 12) # Scythe Mastery
build.add_attribute(44, 3)  # Mysticism

build.set_skills([1759, 1510, 1497, 1485, 1488, 1495, 1558, 1595])

code = build.generate_code()
print(f"Template Code: {code}")
