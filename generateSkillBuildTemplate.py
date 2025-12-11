import base64

class BitStream:
    """Helper class to write bits for the GW Template format."""
    def __init__(self):
        self.data = 0
        self.bit_count = 0

    def write(self, value, num_bits):
        """Writes 'num_bits' from 'value' into the stream (Little Endian approach)."""
        # GW templates pack bits from LSB to MSB for the integer values
        self.data |= (value << self.bit_count)
        self.bit_count += num_bits

    def get_base64(self):
        """Converts the bit stream to a GW-compatible Base64 string."""
        # Pad to multiple of 6 for Base64 conversion
        # but GW format usually expects 8-bit byte alignment for the underlying buffer
        # Let's convert our huge integer into bytes first.
        
        # Calculate total bytes needed
        num_bytes = (self.bit_count + 7) // 8
        byte_array = bytearray()
        
        temp_data = self.data
        for _ in range(num_bytes):
            byte_array.append(temp_data & 0xFF)
            temp_data >>= 8
            
        # Encode to Base64
        encoded = base64.b64encode(byte_array).decode('utf-8')
        return encoded

class BuildTemplate:
    """
    Generates a Guild Wars 1 Skill Template Code.
    Ref: https://wiki.guildwars.com/wiki/Skill_template_format
    """
    
    # Profession IDs
    PROFS = {
        'None': 0, 'Warrior': 1, 'Ranger': 2, 'Monk': 3, 'Necromancer': 4,
        'Mesmer': 5, 'Elementalist': 6, 'Assassin': 7, 'Ritualist': 8,
        'Paragon': 9, 'Dervish': 10
    }

    # Attribute IDs (Examples for Dervish - this list would need to be complete in a real DB)
    # The ID corresponds to the in-game attribute ID.
    # Mysticism ID is 29 for Dervish.
    # Note: You would need a full mapping of Name -> ID for the Gem to use this fully.
    
    def __init__(self):
        self.primary_prof = 0
        self.secondary_prof = 0
        self.attributes = [] # List of tuples (id, value)
        self.skills = [0] * 8 # List of 8 Skill IDs

    def set_profession(self, primary, secondary='None'):
        self.primary_prof = self.PROFS.get(primary, 0)
        self.secondary_prof = self.PROFS.get(secondary, 0)

    def add_attribute(self, attr_id, value):
        """
        attr_id: The integer ID of the attribute (e.g., 29 for Mysticism)
        value: The number of points (0-12)
        """
        self.attributes.append((attr_id, value))

    def set_skills(self, skill_ids):
        """
        skill_ids: A list of 8 integers representing Skill IDs.
        """
        if len(skill_ids) != 8:
            raise ValueError("Build must have exactly 8 skills.")
        self.skills = skill_ids

    def generate_code(self):
        stream = BitStream()

        # 1. Header (Type 14, Version 0) - Total 8 bits
        # The format expects Type (4 bits) then Version (4 bits)
        # Type 14 = 0xE
        stream.write(14, 4) # Type
        stream.write(0, 4)  # Version

        # 2. Profession Length (2 bits)
        # Usually 0, indicating standard lengths for profs (4 bits each)
        stream.write(0, 2)

        # 3. Professions (4 bits each)
        stream.write(self.primary_prof, 4)
        stream.write(self.secondary_prof, 4)

        # 4. Attribute Count (4 bits)
        stream.write(len(self.attributes), 4)

        # 5. Attributes (4 bits ID + 4 bits Value)
        # Note: Valid Attributes usually typically involve offsets, 
        # but for raw template generation, we write ID then Value.
        for attr_id, value in self.attributes:
            stream.write(attr_id, 4)
            stream.write(value, 4)

        # 6. Skills (12 bits each)
        for skill_id in self.skills:
            stream.write(skill_id, 12)

        return stream.get_base64()

# --- EXAMPLE USAGE FOR THE GEM ---

def create_example_build():
    # Example: Dervish / Warrior
    # Mysticism (ID 29): 12
    # Scythe Mastery (ID 30): 12
    # Skills: 
    # 1. Vow of Silence (ID: 1537) - Elite
    # 2. Mystic Sweep (ID: 1546)
    # ... (filling with dummy ID 1 for example)
    
    generator = BuildTemplate()
    generator.set_profession('Dervish', 'Warrior')
    
    # Adding Attributes (IDs are hypothetical/game specific)
    # Dervish: Mysticism=29, Scythe Mastery=30, Wind Prayers=31, Earth Prayers=32
    generator.add_attribute(29, 12) # Mysticism 12
    generator.add_attribute(30, 12) # Scythe Mastery 12

    # Adding 8 Skills (IDs must be integers)
    # Note: In a real Gem scenario, the Gem must lookup the ID from the Skill Name.
    skill_list = [
        1537, # Vow of Silence
        1546, # Mystic Sweep
        1555, # Eremite's Zeal
        301,  # Example Warrior Skill (e.g. Sprint)
        0, 0, 0, 0 # Empty slots (ID 0)
    ]
    generator.set_skills(skill_list)

    return generator.generate_code()

if __name__ == "__main__":
    print(f"Generated Code: {create_example_build()}")
