"""
Visual mapping of Hansen class consolidation
Shows how the 256 original classes are grouped into 12 consolidated classes
"""

# ============================================================================
# HANSEN CLASS CONSOLIDATION MAPPING
# ============================================================================
# Original → Consolidated mapping with class counts and ranges

CONSOLIDATION_VISUAL = """

TERRA FIRMA STRATA (0-116)
═══════════════════════════════════════════════════════════════════════════

0-5         Unvegetated/Bare Ground
└─ 6 classes: 100%-90% bare ground
   Colors: Light tan (#D4D4A8)

6-50        Dense Short Vegetation  
└─ 45 classes: 88%-0% bare ground (decreasing bare percentage)
   Colors: Light tan-green (#B8D4A8)

51-74       Open Tree Cover
└─ 24 classes: 3m to >25m stable tree height
   Colors: Light green (#90C090)

75-91       Dense Tree Cover
└─ 17 classes: 10m to >25m tree height (high canopy density)
   Colors: Dark green (#1F8040)

92-115      Tree Cover Gain
└─ 24 classes: 3m to >25m afforested tree height
   Colors: Forest green (#4CAF50)

116         Tree Cover Loss
└─ 1 class: Deforestation/forest loss
   Colors: Red (#E53935)


WETLAND STRATA (120-236) - Same structure as Terra firma
════════════════════════════════════════════════════════════════════════════

120-125     Unvegetated/Bare Ground (Wetland)
└─ 6 classes: Salt pans, 100%-90% bare ground
   Colors: Light tan (#D4D4A8)

126-170     Dense Short Vegetation (Wetland)
└─ 45 classes: Sparse vegetation, 88%-0% bare ground
   Colors: Light tan-green (#B8D4A8)

171-194     Open Tree Cover (Wetland)
└─ 24 classes: Wetland trees, 3m to >25m height
   Colors: Light green (#90C090)

195-211     Dense Tree Cover (Wetland)
└─ 17 classes: Wetland forest, 10m to >25m height
   Colors: Dark green (#1F8040)

212-235     Tree Cover Gain (Wetland)
└─ 24 classes: Wetland afforestation
   Colors: Forest green (#4CAF50)

236         Tree Cover Loss (Wetland)
└─ 1 class: Wetland deforestation
   Colors: Red (#E53935)


OTHER CLASSES (240-255)
════════════════════════════════════════════════════════════════════════════

240-249     Built-up
└─ 10 classes: Urban areas (0-10%, 10-20%, ... 90-100%)
   Colors: Orange-red (#FF6B35)

250         Water
└─ 1 class: Lakes, rivers, water bodies
   Colors: Blue (#2196F3)

251         Ice
└─ 1 class: Permanent ice, glaciers
   Colors: Light cyan (#E0F7FA)

252         Cropland
└─ 1 class: Agricultural areas
   Colors: Gold (#FFD700)

253         Not used
└─ Gap in legend (no data for this value)

254         Ocean
└─ 1 class: Oceanic areas
   Colors: Dark blue (#0D47A1)

255         No Data
└─ 1 class: Missing or invalid data
   Colors: Gray (#CCCCCC)


CONSOLIDATION SUMMARY
════════════════════════════════════════════════════════════════════════════

Original Classes:     256 (values 0-255)
Consolidated Classes: 12 major categories
Unmapped gaps:        3 ranges not assigned (117-119, 237-239, 253)

Grouping Strategy:
  ├─ Vegetation classes: Grouped by type (trees vs shrubs/grass)
  ├─ Tree classes: Grouped by canopy density (open vs dense)
  ├─ Change classes: Grouped as gains vs losses
  └─ Other: Each gets own category (Water, Urban, Ice, etc.)

Reduction Factor: 256:12 = ~21:1 simplification


CLASS SIZE DISTRIBUTION
════════════════════════════════════════════════════════════════════════════

Consolidation Size Distribution:
                                    Count
Unvegetated                        12  ███
Dense Short Vegetation             90  ███████████████████████████████
Open Tree Cover                    48  ████████████████
Dense Tree Cover                   34  ███████████
Tree Cover Gain                    48  ████████████████
Tree Cover Loss                     2  █
Built-up                           10  ███
Water                               1  
Ice                                 1  
Cropland                            1  
Ocean                               1  
No Data                              1  


ANALYTICAL USES
════════════════════════════════════════════════════════════════════════════

1. Simplified Visualization
   • Use consolidation for maps and charts
   • 12 colors are more readable than 256

2. Land Cover Change Analysis
   • Compare "Dense Tree Cover" areas over time
   • Track "Tree Cover Gain" vs "Tree Cover Loss"
   • Monitor "Built-up" expansion

3. Multi-Year Comparisons
   • Summarize changes at consolidated level
   • Create summary statistics by broad category
   • Identify major transition patterns

4. Public Communication
   • Easier to explain 12 classes vs 256
   • Consistent color scheme across reports
   • Meaningful class names for stakeholders

5. Detailed Analysis (when needed)
   • Still have access to original classes
   • Can drill down from consolidated → original
   • Preserve data granularity for technical analysis


EXAMPLE CONSOLIDATION IN PRACTICE
════════════════════════════════════════════════════════════════════════════

User draws area and analyzes Hansen 2020 data:

Original Output (256 classes):
  Class 42:  15,000 ha  (2.3% bare ground in short vegetation)
  Class 43:  12,000 ha  (1.4% bare ground in short vegetation)
  Class 44:  10,000 ha  (0.5% bare ground in short vegetation)
  Class 75:   8,000 ha  (10m dense trees)
  Class 76:   6,000 ha  (11m dense trees)
  ...
  [250+ more classes]

Consolidated Output (12 classes):
  Dense Short Vegetation:  37,000 ha  (5.6%)
  Dense Tree Cover:       652,000 ha (99.0%)
  No Data:                12,000 ha  (1.8%)
  ...
  [Total: 659,000 ha]

Benefits: Cleaner visualization, easier interpretation, 21x less classes!
"""

if __name__ == "__main__":
    print(CONSOLIDATION_VISUAL)
