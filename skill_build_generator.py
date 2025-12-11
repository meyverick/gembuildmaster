import sys

class BitStream:
    """Version simplifiée et robuste pour éviter les erreurs de bitwise."""
    def __init__(self):
        self.bits = [] # On stocke les bits comme une liste de 0 et 1 (plus lent mais sûr)

    def write(self, value, num_bits):
        # Convertit la valeur en binaire (ex: 14 -> '1110')
        bin_str = format(value, f'0{num_bits}b')
        # Guild Wars lit LSB (Least Significant Bit) en premier
        # Donc on inverse la chaîne pour l'écrire
        self.bits.extend([int(b) for b in reversed(bin_str)])

    def get_gw_base64(self):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        encoded = ""
        # On lit par paquets de 6 bits
        for i in range(0, len(self.bits), 6):
            chunk = self.bits[i:i+6]
            # Si le dernier paquet est incomplet, on complète avec des 0
            if len(chunk) < 6:
                chunk.extend([0] * (6 - len(chunk)))
            
            # Reconversion bit list -> int (LITTLE ENDIAN)
            val = 0
            for idx, bit in enumerate(chunk):
                val += bit * (2**idx)
            encoded += chars[val]
        return encoded

class BuildTemplate:
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
        # Accepte ID (int) ou Nom (str)
        p_id = primary if isinstance(primary, int) else self.PROFS.get(primary, 0)
        s_id = secondary if isinstance(secondary, int) else self.PROFS.get(secondary, 0)
        self.primary_prof = p_id
        self.secondary_prof = s_id
        print(f"DEBUG: Set Professions -> Prim: {p_id}, Sec: {s_id}")

    def add_attribute(self, attr_id, value):
        # CRITIQUE : On ignore les IDs négatifs (Rangs PvE comme Sunspear -2)
        # Ils ne doivent PAS être dans le template code.
        if attr_id < 0: 
            print(f"DEBUG: Skipped PvE Attribute ID {attr_id}")
            return
        self.attributes.append((attr_id, value))

    def set_skills(self, skill_ids):
        if len(skill_ids) < 8:
            skill_ids += [0] * (8 - len(skill_ids))
        self.skills = skill_ids[:8]
        print(f"DEBUG: Set Skills -> {self.skills}")

    def _calc_bits_needed(self, value):
        return value.bit_length()

    def generate_code(self):
        try:
            stream = BitStream()
            
            # 1. HEADER
            stream.write(14, 4) # Type
            stream.write(0, 4)  # Version

            # 2. PROFESSIONS
            max_prof_id = max(self.primary_prof, self.secondary_prof)
            bits_needed = max(4, self._calc_bits_needed(max_prof_id))
            prof_code = 1 if bits_needed > 4 else 0
            
            stream.write(prof_code, 2)
            prof_bits = (prof_code * 2) + 4
            stream.write(self.primary_prof, prof_bits)
            stream.write(self.secondary_prof, prof_bits)

            # 3. ATTRIBUTES
            count = len(self.attributes)
            stream.write(count, 4)

            if count > 0:
                max_attr_id = max(attr[0] for attr in self.attributes)
                attr_bits_needed = max(4, self._calc_bits_needed(max_attr_id))
                attr_code = attr_bits_needed - 4
                
                stream.write(attr_code, 4)
                for attr_id, value in self.attributes:
                    stream.write(attr_id, attr_bits_needed)
                    stream.write(value, 4)
            else:
                stream.write(0, 4) # Dummy code if no attributes

            # 4. SKILLS
            max_skill_id = max(self.skills)
            skill_bits_needed = max(8, self._calc_bits_needed(max_skill_id))
            skill_code = skill_bits_needed - 8
            
            stream.write(skill_code, 4)
            for skill_id in self.skills:
                stream.write(skill_id, skill_bits_needed)

            # 5. TAIL
            stream.write(0, 1)

            return stream.get_gw_base64()
            
        except Exception as e:
            return f"ERROR generating code: {str(e)}"
