import base64

class BitStream:
    """Helper class to write bits for the GW Template format."""
    def __init__(self):
        self.data = 0
        self.bit_count = 0

    def write(self, value, num_bits):
        """Writes 'num_bits' from 'value' into the stream (Little Endian approach)."""
        self.data |= (value << self.bit_count)
        self.bit_count += num_bits

    def get_base64(self):
        """Converts the bit stream to a GW-compatible Base64 string."""
        num_bytes = (self.bit_count + 7) // 8
        byte_array = bytearray()
        
        temp_data = self.data
        for _ in range(num_bytes):
            byte_array.append(temp_data & 0xFF)
            temp_data >>= 8
            
        encoded = base64.b64encode(byte_array).decode('utf-8')
        return encoded

class BuildTemplate:
    """
    Generates a Guild Wars 1 Skill Template Code.
    Now supports both Profession Names (Strings) and IDs (Integers).
    """
    
    # Mapping for convenience if the AI decides to use names
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
        """
        Accepts either Profession ID (int) OR Profession Name (str).
        Example: set_profession(10, 1) OR set_profession('Dervish', 'Warrior')
        """
        # Logic for Primary Profession
        if isinstance(primary, int):
            self.primary_prof = primary
        else:
            self.primary_prof = self.PROFS.get(primary, 0)

        # Logic for Secondary Profession
        if isinstance(secondary, int):
            self.secondary_prof = secondary
        else:
            self.secondary_prof = self.PROFS.get(secondary, 0)

    def add_attribute(self, attr_id, value):
        """
        attr_id: The integer ID of the attribute
        value: The number of points (0-12)
        """
        self.attributes.append((attr_id, value))

    def set_skills(self, skill_ids):
        """
        skill_ids: A list of 8 integers representing Skill IDs.
        """
        if len(skill_ids) != 8:
            # Auto-fill with 0s if list is short, just for safety
            skill_ids += [0] * (8 - len(skill_ids))
        self.skills = skill_ids[:8] # Ensure max 8

    def generate_code(self):
        stream = BitStream()

        # 1. Header (Type 14, Version 0)
        stream.write(14, 4) 
        stream.write(0, 4)  

        # 2. Profession Length (2 bits) -> 0 means standard size
        stream.write(0, 2)

        # 3. Professions (4 bits each)
        stream.write(self.primary_prof, 4)
        stream.write(self.secondary_prof, 4)

        # 4. Attribute Count (4 bits)
        stream.write(len(self.attributes), 4)

        # 5. Attributes (4 bits ID + 4 bits Value)
        for attr_id, value in self.attributes:
            stream.write(attr_id, 4)
            stream.write(value, 4)

        # 6. Skills (12 bits each)
        for skill_id in self.skills:
            stream.write(skill_id, 12)

        return stream.get_base64()
