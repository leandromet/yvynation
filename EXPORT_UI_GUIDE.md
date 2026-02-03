# Export Feature - UI Location & Flow

## 🎨 Where the Export Button Appears

```
┌─────────────────────────────────────────────────────────────────┐
│                  Yvynation - Land Cover Analysis                │
│                                                                  │
│  [Tutorial Expander] [Map] [Active Layers]                     │
│                                                                  │
│  ═══════════════════════════════════════════════════════════   │
│                                                                  │
│              💾 Export Analysis                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                                                     │       │
│  │  💡 No data to export yet. Draw polygons or analyze│       │
│  │     territories to generate exports.               │       │
│  │                                                     │       │
│  │     (Button appears when data is available)        │       │
│  │                                                     │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ═══════════════════════════════════════════════════════════   │
│                                                                  │
│              🏛️ Territory Analysis Results                      │
│  [Land Cover Charts] [Data Tables] [Territory Info]            │
│                                                                  │
│  ═══════════════════════════════════════════════════════════   │
│                                                                  │
│              📊 Analysis & Statistics                            │
│  [MapBiomas Analysis] [Hansen Analysis] [Comparison] [About]   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📍 When Data is Available

After drawing a polygon or analyzing a territory:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│              💾 Export Analysis                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                                                     │       │
│  │   📦 Export All Data & Visualizations             │       │
│  │                                                     │       │
│  │   ℹ️ What's included in this export               │       │
│  │                                                     │       │
│  │   - Geometries: 2 drawn polygon(s) + territory    │       │
│  │   - Data Files: Analysis results as CSV           │       │
│  │   - Metadata: Analysis parameters and timestamps  │       │
│  │   - GeoJSON: All geometries for GIS software      │       │
│  │                                                     │       │
│  │   Territory: Yanomami Territory                   │       │
│  │   Data Source: MapBiomas                          │       │
│  │   Years: 2020 to 2023                             │       │
│  │                                                     │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ User Interaction Flow

### Step 1: Start Analysis
```
┌──────────────┐
│ Draw polygon │  or  │ Select territory │
│ on the map   │      │ and click analyze │
└──────┬───────┘      └────────┬──────────┘
       │                       │
       └───────────┬───────────┘
                   ▼
          Data stored in session
         (all_drawn_features,
          territory_result, etc.)
```

### Step 2: Export Button Activates
```
       ┌─────────────────────────────────┐
       │ generate_export_button() checks │
       │ if data is available            │
       └─────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
   Yes, has data          No data yet
       │                       │
       ▼                       ▼
   Show button            Show info message
   "📦 Export All..."     "No data to export"
```

### Step 3: User Clicks Export
```
┌──────────────────────────────────┐
│ User clicks:                     │
│ 📦 Export All Data & Visualizations
└─────────────┬────────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ create_export_zip() runs:     │
   │ • Gathers all data           │
   │ • Creates ZIP file           │
   │ • Shows success message      │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ Download button appears:     │
   │ 📥 Download Export Package   │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ User clicks download button  │
   │ ZIP file saved to computer   │
   └──────────────────────────────┘
```

### Step 4: User Extracts ZIP
```
yvynation_export_yanomami_20240203_105230.zip
    ├── Extract all
    │
    ▼
yvynation_export_yanomami_20240203_105230/
    ├── metadata.json
    ├── geometries.geojson
    ├── data/
    │   └── analysis_2023.csv
    ├── comparison/
    │   └── analysis_2020.csv
    └── figures/
        └── (ready for future visualizations)
```

## 🔄 State Management

```
Session State Components:
├── all_drawn_features     ──┐
├── last_drawn_feature      ├─→ Used by export_button
├── territory_geom          │   to create ZIP
├── territory_name          │
├── territory_result        │
├── territory_result_year2  │
├── territory_year/year2    │
└── territory_source        ──┘
```

## 🎯 Button Behavior

| Condition | Display | Action |
|-----------|---------|--------|
| No polygons, no territory | Info message | None |
| Has drawn polygons | Active button | Export polygons + metadata |
| Territory analyzed | Active button | Export territory + data |
| Both polygons + territory | Active button | Export all together |
| Multiple years | Active button | Include comparison data |

## 📱 Responsive Design

```
Desktop (wide screen)
┌──────────────────────────────────────┐
│  💾 Export Analysis                  │
│  ┌────────────────────────────────┐  │
│  │ 📦 Export Button (full width) │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘

Mobile (narrow screen)
┌──────────────────┐
│ 💾 Export        │
│ Analysis         │
│ ┌──────────────┐ │
│ │ 📦 Export   │ │
│ │ Button      │ │
│ └──────────────┘ │
└──────────────────┘
```

## 🎨 Visual Feedback

### When Processing
```
⏳ 🔄 Preparing export package...
```

### Success
```
✅ Export ready! Click above to download yvynation_export_yanomami_20240203_105230.zip

📋 What's included in this export ▼
  - Geometries: 2 drawn polygon(s) + territory boundary
  - Data Files: Analysis results as CSV
  - Metadata: Analysis parameters and timestamps
  - GeoJSON: All geometries for use in GIS software
  
  Territory: Yanomami Territory
  Data Source: MapBiomas
  Years: 2020 to 2023
```

### Error
```
❌ Export failed: [Error message]
```

## 🔗 Related UI Elements

The export button sits between:

**Above**: Map & layer controls  
**Below**: Territory analysis results & charts

This placement ensures:
- ✅ Visible after user generates data
- ✅ Before detailed analysis results
- ✅ Easy one-click access
- ✅ Clear section headers
- ✅ Professional layout

## 💡 UX Best Practices Implemented

1. **Visibility**: Clear heading "💾 Export Analysis"
2. **Affordance**: Button clearly labeled with action
3. **Feedback**: Progress messages and success confirmations
4. **Context**: Shows what's being exported
5. **Accessibility**: Full-width button for easy clicking
6. **Discoverability**: Appears automatically when data is ready
7. **Help**: "What's included" expandable section
8. **Error Handling**: Clear error messages if export fails
