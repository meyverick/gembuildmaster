class BitStream:
    """
    Gère l'écriture de bits en 'Lowest-bit-first order' (Little Endian)
    et l'encodage Base64 spécifique à Guild Wars.
    """
    def __init__(self):
        self.data = 0
        self.bit_count = 0

    def write(self, value, num_bits):
        # On écrit les bits du poids faible vers le poids fort
        self.data |= (value << self.bit_count)
        self.bit_count += num_bits

    def get_gw_base64(self):
        # Alphabet Base64 standard (A-Z, a-z, 0-9, +, /)
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        encoded = ""
        temp_data = self.data
        current_bits = self.bit_count
        
        # Le format GW convertit le flux binaire en caractères par tranches de 6 bits
        while current_bits > 0:
            val = temp_data & 0x3F # Prend les 6 premiers bits
            encoded += chars[val]
            temp_data >>= 6
            current_bits -= 6
        return encoded

class BuildTemplate:
    """
    Générateur de Template conforme à la doc officielle.
    Supporte les tailles de bits dynamiques pour Attributs et Skills.
    """
    
    PROFS = {
        'None': 0, 'Warrior': 1, 'Ranger': 2, 'Monk': 3, 'Necromancer': 4,
        'Mesmer': 5, 'Elementalist': 6, 'Assassin': 7, 'Ritualist': 8,
        'Paragon': 9, 'Dervish': 10
    }

    def __init__(self):
        self.primary_prof = 0
        self.secondary_prof = 0
        self.attributes = [] 
        self.skills = [0] * 8 

    def set_profession(self, primary, secondary='None'):
        # Accepte soit le Nom (str) soit l'ID (int)
        if isinstance(primary, int): self.primary_prof = primary
        else: self.primary_prof = self.PROFS.get(primary, 0)

        if isinstance(secondary, int): self.secondary_prof = secondary
        else: self.secondary_prof = self.PROFS.get(secondary, 0)

    def add_attribute(self, attr_id, value):
        # On ignore les IDs négatifs (Rangs PvE)
        if attr_id < 0: return
        self.attributes.append((attr_id, value))

    def set_skills(self, skill_ids):
        # Remplit avec des 0 si < 8 skills
        if len(skill_ids) < 8:
            skill_ids += [0] * (8 - len(skill_ids))
        self.skills = skill_ids[:8]

    def _calc_bits_needed(self, value):
        """Calcule le nombre de bits nécessaires pour stocker une valeur."""
        if value == 0: return 0
        return value.bit_length()

    def generate_code(self):
        stream = BitStream()
        
        # --- 1. HEADER ---
        # Type 14 (0xE) + Version 0
        stream.write(14, 4)
        stream.write(0, 4)

        # --- 2. PROFESSIONS ---
        # Calcul de la taille nécessaire pour les IDs de profession
        # Formule doc: bits = code * 2 + 4.
        # Max ID est 10 (Dervish), donc 4 bits suffisent (Code 0).
        max_prof_id = max(self.primary_prof, self.secondary_prof)
        bits_needed = max(4, self._calc_bits_needed(max_prof_id))
        
        # On doit trouver le 'code' tel que: bits <= code * 2 + 4
        # Pour GW1 standard (max ID 10), code est toujours 0 (4 bits).
        prof_code = 0 
        if bits_needed > 4: prof_code = 1 # Si un jour ID > 15 (jamais arrivé)
        
        stream.write(prof_code, 2)
        prof_bits = (prof_code * 2) + 4
        stream.write(self.primary_prof, prof_bits)
        stream.write(self.secondary_prof, prof_bits)

        # --- 3. ATTRIBUTES ---
        count = len(self.attributes)
        stream.write(count, 4)

        if count > 0:
            # Trouver l'ID max (ex: 44 pour Mysticism)
            max_attr_id = max(attr[0] for attr in self.attributes)
            # Calculer bits nécessaires. Ex: 44 nécessite 6 bits.
            attr_bits_needed = max(4, self._calc_bits_needed(max_attr_id))
            
            # Formule doc: bits = code + 4
            # Code = bits - 4
            attr_code = attr_bits_needed - 4
            
            stream.write(attr_code, 4)
            
            for attr_id, value in self.attributes:
                stream.write(attr_id, attr_bits_needed) # ID sur X bits
                stream.write(value, 4) # Points toujours sur 4 bits
        else:
            # Si pas d'attributs, code 0
            stream.write(0, 4)

        # --- 4. SKILLS ---
        # Formule doc: bits = code + 8
        # Standard skill IDs vont jusqu'à ~3000 -> 12 bits -> Code 4
        max_skill_id = max(self.skills)
        skill_bits_needed = max(8, self._calc_bits_needed(max_skill_id))
        skill_code = skill_bits_needed - 8
        
        stream.write(skill_code, 4)
        for skill_id in self.skills:
            stream.write(skill_id, skill_bits_needed)

        # --- 5. TAIL ---
        # "1 Bit - Always zero"
        stream.write(0, 1)

        return stream.get_gw_base64()
