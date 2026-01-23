"""
Hansen Class Mapping based on reference-labels.csv
Maps 256 Hansen classes to 11 stratum categories using the Map column from reference-labels.csv
"""

# Strata names (from reference-labels.csv second table, rows 25-35)
HANSEN_STRATUM_NAMES = {
    1: "bare ground",
    2: "semi-arid vegetation",
    3: "dense short vegetation",
    4: "open or short trees of >=3m",
    5: "dense and tall tree cover",
    6: "wetland",
    7: "permanent surface water",
    8: "permanent ice",
    9: "cropland",
    10: "built-up land",
    11: "treed land uses",
}

# Class ID (0-255) to Stratum (1-11) mapping from legend_glcluc_year.csv
# Simplified and corrected mapping based on GLCLUC official category structure
# The legend_glcluc_year.csv has a cleaner structure with 4 main categories:
#   Classes 0-96:    Terra Firma (various short vegetation, trees, etc.) → Stratum varies by sub-class
#   Classes 100-196: Wetland (tree cover and vegetation in wetland areas) → Stratum 6
#   Classes 200-207: Open surface water → Stratum 7
#   Classes 240-255: Special categories (ice, cropland, built-up, ocean, no data) → Various
HANSEN_CLASS_TO_STRATUM = {
    # TERRA FIRMA (0-96): Short vegetation and tree cover
    # Short vegetation classes (0-24)
    0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1,
    10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1,
    20: 1, 21: 1, 22: 1, 23: 1, 24: 1,
    
    # Tree cover classes (25-48) - all map to Stratum 5 (dense and tall tree cover)
    25: 5, 26: 5, 27: 5, 28: 5, 29: 5, 30: 5, 31: 5, 32: 5, 33: 5, 34: 5,
    35: 5, 36: 5, 37: 5, 38: 5, 39: 5, 40: 5, 41: 5, 42: 5, 43: 5, 44: 5,
    45: 5, 46: 5, 47: 5, 48: 5,
    
    # Classes 49-96: Not used or sparse classes in Terra Firma → default to stratum 1
    49: 1, 50: 1, 51: 1, 52: 1, 53: 1, 54: 1, 55: 1, 56: 1, 57: 1, 58: 1,
    59: 1, 60: 1, 61: 1, 62: 1, 63: 1, 64: 1, 65: 1, 66: 1, 67: 1, 68: 1,
    69: 1, 70: 1, 71: 1, 72: 1, 73: 1, 74: 1, 75: 1, 76: 1, 77: 1, 78: 1,
    79: 1, 80: 1, 81: 1, 82: 1, 83: 1, 84: 1, 85: 1, 86: 1, 87: 1, 88: 1,
    89: 1, 90: 1, 91: 1, 92: 1, 93: 1, 94: 1, 95: 1, 96: 1,
    
    # WETLAND (100-196): All wetland classes map to Stratum 6
    # This includes wetland with short vegetation (100-124) and tree cover (125-196)
    100: 6, 101: 6, 102: 6, 103: 6, 104: 6, 105: 6, 106: 6, 107: 6, 108: 6, 109: 6,
    110: 6, 111: 6, 112: 6, 113: 6, 114: 6, 115: 6, 116: 6, 117: 6, 118: 6, 119: 6,
    120: 6, 121: 6, 122: 6, 123: 6, 124: 6, 125: 6, 126: 6, 127: 6, 128: 6, 129: 6,
    130: 6, 131: 6, 132: 6, 133: 6, 134: 6, 135: 6, 136: 6, 137: 6, 138: 6, 139: 6,
    140: 6, 141: 6, 142: 6, 143: 6, 144: 6, 145: 6, 146: 6, 147: 6, 148: 6, 149: 6,
    150: 6, 151: 6, 152: 6, 153: 6, 154: 6, 155: 6, 156: 6, 157: 6, 158: 6, 159: 6,
    160: 6, 161: 6, 162: 6, 163: 6, 164: 6, 165: 6, 166: 6, 167: 6, 168: 6, 169: 6,
    170: 6, 171: 6, 172: 6, 173: 6, 174: 6, 175: 6, 176: 6, 177: 6, 178: 6, 179: 6,
    180: 6, 181: 6, 182: 6, 183: 6, 184: 6, 185: 6, 186: 6, 187: 6, 188: 6, 189: 6,
    190: 6, 191: 6, 192: 6, 193: 6, 194: 6, 195: 6, 196: 6,
    
    # OPEN SURFACE WATER (200-207): All water classes map to Stratum 7
    200: 7, 201: 7, 202: 7, 203: 7, 204: 7, 205: 7, 206: 7, 207: 7,
    
    # SPECIAL CATEGORIES (240-255): Cropland, built-up, ice, ocean, no data
    # Classes 208-239: Not used in official legend
    208: 11, 209: 11, 210: 11, 211: 11, 212: 11, 213: 11, 214: 11, 215: 11,
    216: 11, 217: 11, 218: 11, 219: 11, 220: 11, 221: 11, 222: 11, 223: 11,
    224: 11, 225: 11, 226: 11, 227: 11, 228: 11, 229: 11, 230: 11, 231: 11,
    232: 11, 233: 11, 234: 11, 235: 11, 236: 11, 237: 11, 238: 11, 239: 11,
    
    # Cropland
    244: 9,
    # Snow/ice
    241: 8,
    # Built-up
    250: 10,
    # Ocean
    254: 11,
    # No data
    255: 11,
    # Not used/other
    97: 11, 98: 11, 99: 11, 240: 11, 242: 11, 243: 11, 245: 11, 246: 11, 247: 11,
    248: 11, 249: 11, 251: 11, 252: 11, 253: 11
}

# Color palette for the 11 strata
# These should match the visual characteristics of the data
HANSEN_STRATUM_COLORS = {
    1: "#D4D4A8",      # bare ground - tan/beige
    2: "#F4D584",      # semi-arid vegetation - light yellow
    3: "#A8D4A8",      # dense short vegetation - light green
    4: "#70C070",      # open or short trees - medium green
    5: "#1F8040",      # dense and tall tree cover - dark green
    6: "#C0B0A8",      # wetland - grayish-brown
    7: "#4A90E2",      # permanent surface water - blue
    8: "#E0E0E0",      # permanent ice - light gray
    9: "#FFD700",      # cropland - gold/yellow
    10: "#FF6B35",     # built-up land - orange-red
    11: "#90EE90",     # treed land uses - light green
}

def get_stratum(class_id):
    """Get stratum number for a Hansen class ID."""
    return HANSEN_CLASS_TO_STRATUM.get(class_id, 11)

def get_stratum_name(class_id):
    """Get stratum name for a Hansen class ID."""
    stratum = get_stratum(class_id)
    return HANSEN_STRATUM_NAMES.get(stratum, "Unknown")

def get_stratum_color(class_id):
    """Get color for a Hansen class ID based on its stratum."""
    stratum = get_stratum(class_id)
    return HANSEN_STRATUM_COLORS.get(stratum, "#808080")
