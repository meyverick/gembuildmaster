class BitWriter:
    """
    Helper class to write bits into a Base64 string in lowest-bit-first order.
    Unlike standard Base64 which processes byte-aligned data MSB-first,
    GW1 templates are a continuous stream of bits packed into 6-bit chunks LSB-first.
    """
    def __init__(self):
        self._value = 0
        self._bit_count = 0
        self._output = []
        self._chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    def write(self, value, num_bits):
        """Writes an integer value using the specified number of bits."""
        # Mask value to ensure it fits
        value &= (1 << num_bits) - 1
        
        # Add bits to the accumulator
        self._value |= (value << self._bit_count)
        self._bit_count += num_bits

        # Extract complete 6-bit chunks
        while self._bit_count >= 6:
            chunk = self._value & 0x3F
            self._output.append(self._chars[chunk])
            self._value >>= 6
            self._bit_count -= 6

    def get_code(self):
        """Finalizes the stream and returns the string."""
        # Flush remaining bits if any
        if self._bit_count > 0:
            chunk = self._value & 0x3F
            self._output.append(self._chars[chunk])
        
        return "".join(self._output)


class BuildTemplate:
    def __init__(self):
        self.primary_profession = 0
        self.secondary_profession = 0
        self.attributes = [] # List of tuples (id, value)
        self.skills = [0] * 8 # Always 8 slots
    
    def set_profession(self, primary, secondary):
        """Sets the primary and secondary profession IDs."""
        self.primary_profession = primary
        self.secondary_profession = secondary

    def add_attribute(self, attr_id, value):
        """Adds an attribute rank. Value should be between 0 and 12."""
        if attr_id < 0: return
        self.attributes.append((attr_id, value))

    def set_skills(self, skill_ids):
        """Sets the list of skills. Pads with 0 to ensure 8 slots."""
        self.skills = skill_ids[:8] + [0] * (8 - len(skill_ids))

    def generate_code(self):
        """Compiles the build data into a Base64 template string."""
        writer = BitWriter()

        # Attributes must be sorted by ID for valid templates
        sorted_attributes = sorted(self.attributes, key=lambda x: x[0])

        # --- 1. Header ---
        # Type 14 (0xE) - 4 bits
        writer.write(14, 4)
        # Version 0 - 4 bits
        writer.write(0, 4)

        # --- 2. Professions ---
        # Determine bit width needed for profession IDs
        max_prof_id = max(self.primary_profession, self.secondary_profession)
        prof_code = 0
        # Formula: bits = code * 2 + 4
        while (prof_code * 2 + 4) < self._min_bits_for(max_prof_id):
            prof_code += 1
        prof_bit_width = prof_code * 2 + 4
        
        writer.write(prof_code, 2)
        writer.write(self.primary_profession, prof_bit_width)
        writer.write(self.secondary_profession, prof_bit_width)

        # --- 3. Attributes ---
        writer.write(len(sorted_attributes), 4)

        if sorted_attributes:
            max_attr_id = max(a[0] for a in sorted_attributes)
            attr_code = 0
            # Formula: bits = code + 4
            while (attr_code + 4) < self._min_bits_for(max_attr_id):
                attr_code += 1
            attr_bit_width = attr_code + 4
        else:
            attr_code = 0
            attr_bit_width = 4

        writer.write(attr_code, 4)

        for attr_id, value in sorted_attributes:
            writer.write(attr_id, attr_bit_width)
            writer.write(value, 4)

        # --- 4. Skills ---
        max_skill_id = max(self.skills)
        skill_code = 0
        # Formula: bits = code + 8
        while (skill_code + 8) < self._min_bits_for(max_skill_id):
            skill_code += 1
        skill_bit_width = skill_code + 8

        writer.write(skill_code, 4)

        for skill_id in self.skills:
            writer.write(skill_id, skill_bit_width)

        # --- 5. Tail ---
        # 1 Bit - Always zero
        writer.write(0, 1)

        return writer.get_code()

    def _min_bits_for(self, value):
        if value == 0: return 1
        return value.bit_length()

# --- Usage Example ---
if __name__ == "__main__":
    build = BuildTemplate()
    
    # 1. Set Professions: Dervish (10) / Paragon (9)
    build.set_profession(10, 9)

    # 2. Add Attributes
    # (Order doesn't matter here, generator sorts them)
    build.add_attribute(43, 12) # Earth Prayers
    build.add_attribute(41, 10) # Scythe Mastery
    build.add_attribute(44, 9)  # Mysticism
    build.add_attribute(38, 9)  # Command

    # 3. Set Skills
    build.set_skills([
        1759, # Vow of Strength
        1510, # Sand Shards
        2116, # Staggering Force
        1484, # Mystic Sweep
        1485, # Eremite's Attack
        1516, # Mystic Regeneration
        1558, # "Go for the Eyes!"
        1595  # "Fall Back!"
    ])

    code = build.generate_code()
    print("Generated Template Code:", code)
    # Expected: OgGjkyslqS8E7w+GvF9G5G0G
