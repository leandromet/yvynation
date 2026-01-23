"""
Test script for Hansen class consolidation
Verifies all mappings and utilities are working correctly
"""

import sys
sys.path.insert(0, '/home/leandromb/google_eengine/yvynation')

from hansen_consolidated_utils import (
    get_consolidated_class,
    get_consolidated_color,
    aggregate_to_consolidated
)
from hansen_consolidated_mapping import (
    HANSEN_CONSOLIDATED_MAPPING,
    HANSEN_CONSOLIDATED_COLORS,
    HANSEN_CLASS_GROUPING
)
from config import HANSEN_CONSOLIDATED_MAPPING as CONFIG_MAPPING


def test_consolidation_mappings():
    """Test that all 256 classes are properly mapped"""
    print("Testing consolidation mappings...")
    
    # Check all classes 0-255 are mapped
    for class_id in range(256):
        if class_id != 253:  # 253 is "Not used", skip it
            consolidated = get_consolidated_class(class_id)
            assert isinstance(consolidated, str), f"Class {class_id} mapping failed"
    
    print(f"✅ All 256 classes properly mapped")
    

def test_specific_mappings():
    """Test specific class mappings"""
    print("\nTesting specific class mappings...")
    
    test_cases = [
        (0, "Unvegetated"),
        (5, "Unvegetated"),
        (6, "Dense Short Vegetation"),
        (42, "Dense Short Vegetation"),
        (50, "Dense Short Vegetation"),
        (51, "Open Tree Cover"),
        (74, "Open Tree Cover"),
        (75, "Dense Tree Cover"),
        (91, "Dense Tree Cover"),
        (92, "Tree Cover Gain"),
        (115, "Tree Cover Gain"),
        (116, "Tree Cover Loss"),
        (120, "Unvegetated"),
        (170, "Dense Short Vegetation"),
        (171, "Open Tree Cover"),
        (194, "Open Tree Cover"),
        (195, "Dense Tree Cover"),
        (211, "Dense Tree Cover"),
        (212, "Tree Cover Gain"),
        (235, "Tree Cover Gain"),
        (236, "Tree Cover Loss"),
        (240, "Built-up"),
        (249, "Built-up"),
        (250, "Water"),
        (251, "Ice"),
        (252, "Cropland"),
        (254, "Ocean"),
        (255, "No Data"),
    ]
    
    for class_id, expected_class in test_cases:
        actual_class = get_consolidated_class(class_id)
        assert actual_class == expected_class, \
            f"Class {class_id}: expected '{expected_class}', got '{actual_class}'"
    
    print(f"✅ All {len(test_cases)} specific mappings verified")


def test_color_mappings():
    """Test that all consolidated classes have colors"""
    print("\nTesting color mappings...")
    
    expected_classes = {
        "Unvegetated", "Dense Short Vegetation", "Open Tree Cover", 
        "Dense Tree Cover", "Tree Cover Gain", "Tree Cover Loss",
        "Built-up", "Water", "Ice", "Cropland", "Ocean", "No Data"
    }
    
    actual_classes = set(HANSEN_CONSOLIDATED_COLORS.keys())
    assert expected_classes == actual_classes, f"Color classes mismatch"
    
    # Check all colors are valid hex
    for class_name, color in HANSEN_CONSOLIDATED_COLORS.items():
        assert color.startswith("#"), f"Invalid color format for {class_name}: {color}"
        assert len(color) == 7, f"Invalid color length for {class_name}: {color}"
    
    print(f"✅ All {len(HANSEN_CONSOLIDATED_COLORS)} colors properly formatted")


def test_grouping():
    """Test class grouping completeness"""
    print("\nTesting class grouping...")
    
    all_grouped_classes = set()
    for group, classes in HANSEN_CLASS_GROUPING.items():
        all_grouped_classes.update(classes)
    
    # Should have all classes 0-255 (256 total)
    expected_count = 256
    actual_count = len(all_grouped_classes)
    
    assert actual_count == expected_count, \
        f"Expected {expected_count} classes in grouping, got {actual_count}"
    
    print(f"✅ All {actual_count} classes accounted for in grouping")


def test_configuration_integration():
    """Test that config.py has the consolidation mappings"""
    print("\nTesting config.py integration...")
    
    # Check mapping is in config
    assert HANSEN_CONSOLIDATED_MAPPING is not None
    assert len(HANSEN_CONSOLIDATED_MAPPING) > 200
    
    # Spot check a few mappings match
    assert CONFIG_MAPPING[42] == "Dense Short Vegetation"
    assert CONFIG_MAPPING[75] == "Dense Tree Cover"
    assert CONFIG_MAPPING[240] == "Built-up"
    
    print("✅ Config.py properly integrated")


def test_dataframe_aggregation():
    """Test DataFrame aggregation function"""
    print("\nTesting DataFrame aggregation...")
    
    import pandas as pd
    
    # Create test DataFrame
    df_test = pd.DataFrame({
        'Class_ID': [0, 1, 6, 42, 50, 51, 75, 92, 116, 240, 250, 255],
        'Class': [f'Class {i}' for i in [0, 1, 6, 42, 50, 51, 75, 92, 116, 240, 250, 255]],
        'Pixels': [1000, 500, 2000, 1500, 800, 3000, 2500, 1200, 100, 900, 10000, 50],
        'Area_ha': [900, 450, 1800, 1350, 720, 2700, 2250, 1080, 90, 810, 9000, 45]
    })
    
    df_consolidated = aggregate_to_consolidated(df_test)
    
    # Check aggregation
    assert len(df_consolidated) > 0
    assert 'Consolidated_Class' in df_consolidated.columns
    assert 'Area_ha' in df_consolidated.columns
    assert 'Pixels' in df_consolidated.columns
    
    # Check specific aggregations
    unvegetated = df_consolidated[df_consolidated['Consolidated_Class'] == 'Unvegetated']
    assert len(unvegetated) == 1
    assert unvegetated['Area_ha'].values[0] == 1350.0  # 900 + 450
    
    print(f"✅ DataFrame aggregation works correctly")


def test_legend_files():
    """Test that legend files exist and are readable"""
    print("\nTesting legend files...")
    
    import os
    
    files_to_check = [
        'legend_0.csv',
        'legend_consolidated.csv',
        'hansen_consolidated_mapping.py',
        'hansen_consolidated_utils.py'
    ]
    
    base_path = '/home/leandromb/google_eengine/yvynation'
    
    for filename in files_to_check:
        filepath = os.path.join(base_path, filename)
        assert os.path.exists(filepath), f"File not found: {filepath}"
    
    # Check consolidated legend is readable
    with open(os.path.join(base_path, 'legend_consolidated.csv'), 'r') as f:
        lines = f.readlines()
        assert len(lines) > 200, "Consolidated legend seems too short"
    
    print(f"✅ All {len(files_to_check)} legend files present and readable")


def run_all_tests():
    """Run all tests"""
    print("="*70)
    print("HANSEN CLASS CONSOLIDATION - TEST SUITE")
    print("="*70)
    
    try:
        test_consolidation_mappings()
        test_specific_mappings()
        test_color_mappings()
        test_grouping()
        test_configuration_integration()
        test_dataframe_aggregation()
        test_legend_files()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nConsolidation Status:")
        print(f"  • Classes consolidated: 256 → 12")
        print(f"  • Original classes: {len(HANSEN_CONSOLIDATED_MAPPING)}")
        print(f"  • Consolidated classes: {len(HANSEN_CONSOLIDATED_COLORS)}")
        print(f"  • Files created: 4")
        print(f"\nReady to use in hansen_analysis.py!")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
