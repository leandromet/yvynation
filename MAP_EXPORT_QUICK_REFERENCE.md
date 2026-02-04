# 🗺️ Map Export Feature - Quick Reference

## 🎯 What Can I Export?

```
┌─────────────────────────────────────────────────────┐
│ INTERACTIVE MAPS WITH POLYGON OVERLAYS             │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ✅ MapBiomas Layers                                │
│    • One map per selected year (1985-2023)         │
│    • Land cover classification                     │
│    • Your drawn polygons highlighted               │
│                                                     │
│ ✅ Hansen Forest Change Layers                     │
│    • One map per selected year (2000-2020)         │
│    • Global forest change detection                │
│    • Your polygons overlaid                        │
│                                                     │
│ ✅ Google Satellite Basemap                        │
│    • Real satellite imagery                        │
│    • Perfect for ground-truthing                   │
│    • Your polygons on top                          │
│                                                     │
│ ✅ Google Maps Basemap                             │
│    • Road map for location reference               │
│    • Place names and features                      │
│    • Your polygons visible                         │
│                                                     │
│ ✅ Territory Boundaries                            │
│    • Indigenous territory outlines                 │
│    • Context for your analysis                     │
│    • On all exported maps                          │
│                                                     │
│ ✅ Scale Bars & Measurement Tools                  │
│    • Distance reference (kilometers)               │
│    • Click-to-measure feature                      │
│    • On every map                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 📋 Step-by-Step Instructions

### STEP 1: Prepare Your Analysis
```
□ Select MapBiomas years  (sidebar checkboxes)
□ Select Hansen years     (sidebar checkboxes)
□ Draw polygons           (map drawing tools)
□ [Optional] Analyze territory  (sidebar button)
```

### STEP 2: Prepare Maps for Export
```
□ Scroll to "🗺️ Export Maps with Polygon Overlays"
□ Read the information text
□ Click "📊 Prepare Maps for Export" button
□ Wait for: "✓ Maps prepared! They will be included..."
```

### STEP 3: Export Everything
```
□ Scroll to "💾 Export Analysis"
□ Click "📦 Export All Data & Visualizations"
□ WAIT - "🔄 Preparing export package..." message
□ See: "✓ Export ready! Click above to download..."
□ Click "📥 Download Export Package" button
```

### STEP 4: Use Your Maps
```
□ Download completes → yvynation_export_TERRITORY_DATE.zip
□ Extract ZIP file to a folder
□ Open: maps/MapBiomas_2023.html (in web browser)
□ Explore the interactive map:
  • Zoom in/out with scroll wheel
  • Click layer control (top-right) to toggle layers
  • Click ruler icon to measure distances
  • Click polygon marker to see information
```

## 📁 What's in the ZIP?

```
yvynation_export_TERRITORY_DATETIME.zip
│
├── maps/  ← YOUR MAPS GO HERE
│   ├── MapBiomas_2023.html       (interactive map)
│   ├── MapBiomas_2020.html       (interactive map)
│   ├── Hansen_2020.html          (interactive map)
│   ├── Satellite_Basemap.html    (interactive map)
│   └── GoogleMaps_Basemap.html   (interactive map)
│
├── geometries.geojson            (your polygons as GeoJSON)
├── metadata.json                 (analysis information)
│
├── polygons/                     (polygon analysis results)
│   └── polygon_1/
│       ├── *.csv (data tables)
│       └── *.png (charts)
│
├── territory/                    (territory analysis results)
│   └── TERRITORY_NAME/
│       ├── *.csv (data tables)
│       ├── *.html (Sankey diagrams)
│       └── *.png (charts)
│
└── figures/                      (additional visualizations)
    └── *.html & *.png
```

## 🖱️ Using Exported Maps

### Opening a Map
```
Right-click: MapBiomas_2023.html
├─ "Open with..." → Select web browser
└─ (Chrome, Firefox, Safari, Edge - all work)
```

### Map Controls
```
┌─────────────────────────────────┐
│          ⌗ Layer Control        │  ← Click to toggle layers
├─────────────────────────────────┤
│ Map Display Area                │
│                                 │
│  Your Polygons:                 │
│  • Blue outlines               │
│  • Labeled "Polygon 1", etc.   │
│  • Click center marker for info │
│                                 │
│  Territory:                      │
│  • Purple outline (if analyzed) │
│                                 │
│  Basemap:                        │
│  • Satellite/Roads (depends)    │
│                                 │
│  Data Layer:                     │
│  • MapBiomas/Hansen (if selected)│
│                                 │
└─────────────────────────────────┘

Left side: [ ⎘ ] Full screen
Bottom left: Scale bar (shows kilometers)
```

### Common Tasks

| Task | How To |
|------|--------|
| **Zoom in** | Scroll mouse wheel up |
| **Zoom out** | Scroll mouse wheel down |
| **Pan map** | Click and drag the map |
| **Toggle layers** | Click ⌗ (top-right) to show/hide |
| **Measure distance** | Click ⎘ (ruler icon), draw line |
| **Polygon info** | Click blue marker on polygon |
| **Full screen** | Click square icon (left side) |
| **Print to PDF** | Ctrl+P (Windows) or Cmd+P (Mac) |

## 💾 Saving Maps for Later

### Save as PDF (for reports/presentations)
```
1. Open map in browser
2. Press Ctrl+P (Windows) or Cmd+P (Mac)
3. Choose "Save as PDF"
4. Select location and save
```

### Share Maps with Others
```
1. Email the .html file directly
   → Recipient opens in any browser
   
2. Upload to cloud storage (Google Drive, Dropbox)
   → Share link with colleagues
   
3. Embed in website/blog (advanced)
   → Use <iframe> tag
```

### Keep Maps Organized
```
Create folder structure:
yvynation_export_territory_2024/
├── maps/
│   ├── MapBiomas_2023.html
│   ├── Hansen_2020.html
│   └── Satellite_Basemap.html
├── data/
│   ├── metadata.json
│   └── geometries.geojson
└── notes.txt (your observations)
```

## ⚡ Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **Map won't open** | Try different browser (Chrome, Firefox, Edge) |
| **Map is blank** | Check if HTML file is complete (file size >1MB) |
| **Polygons not showing** | Make sure you drew polygons BEFORE preparing maps |
| **No data layer visible** | Click layer control (⌗) to toggle layers on |
| **Map is very slow** | Close other browser tabs; try refreshing |
| **Can't zoom properly** | Try zooming with +/- buttons instead of scroll |

## 🎨 Understanding Map Colors

### MapBiomas Classes (example)
```
🟢 Green    = Forest / Vegetation
🟡 Yellow   = Agriculture / Grassland  
🔴 Red      = Urban / Built-up areas
🔵 Blue     = Water
🟣 Purple   = Indigenous Territory (your boundary)
🔵 Blue     = Your drawn polygons
```

### Hansen Forest Change (example)
```
🟩 Dark Green = Dense tree cover
🟩 Light Green = Open tree cover / Gain
🔴 Red = Tree loss / Deforestation
🟨 Yellow = Cropland
🔵 Blue = Water
```

## 📊 Example Uses

### Use Case 1: Verify Land Classification
```
Workflow:
1. Draw polygon around area of interest
2. Export Satellite_Basemap.html
3. Export MapBiomas_2023.html
4. Compare satellite image vs classification
5. Verify if colors match reality
```

### Use Case 2: Document Change Over Time
```
Workflow:
1. Draw polygon
2. Select MapBiomas 1985 and 2023
3. Export both years
4. Compare maps to see 38-year change
5. Use for report or presentation
```

### Use Case 3: Territory Monitoring
```
Workflow:
1. Analyze indigenous territory
2. Select multiple years (2010, 2015, 2020, 2023)
3. Export all years
4. Create animation by scrolling through maps
5. Document territorial changes
```

### Use Case 4: Share with Stakeholders
```
Workflow:
1. Complete analysis
2. Export all maps
3. Email maps folder to community leaders
4. They open maps in browsers (no software needed)
5. Discuss findings together
```

## 🔍 Pro Tips

✨ **Tip 1:** Draw multiple polygons and compare
```
- Draw polygon A over forest
- Draw polygon B over agriculture  
- Compare areas in exported maps
```

✨ **Tip 2:** Use satellite map for ground-truthing
```
- MapBiomas says "Forest"
- Satellite_Basemap shows actual forest
- Confirms data quality
```

✨ **Tip 3:** Print maps for field work
```
- Export maps
- Print to PDF
- Bring on field visit
- Verify on-the-ground conditions
```

✨ **Tip 4:** Create presentation with maps
```
- Export maps
- Screenshot portions for slides
- Include full interactive maps on USB
- Present both static and interactive versions
```

✨ **Tip 5:** Archive maps with analysis
```
- Save ZIP file with original analysis metadata
- Keep maps for future reference
- Document decisions made based on maps
- Track changes over time
```

## ❓ Frequently Asked Questions

**Q: Do maps work without internet?**
A: Yes! Once downloaded, maps work completely offline.

**Q: Can I edit the maps?**
A: Maps are read-only for viewing. Edit in QGIS/ArcGIS if needed.

**Q: What if I change my mind about layers?**
A: Go back, select different layers, and export again.

**Q: Can I print maps?**
A: Yes! Use Ctrl+P (Windows) or Cmd+P (Mac) to print as PDF.

**Q: Are my polygons saved?**
A: Yes, in geometries.geojson in the ZIP file.

**Q: Can I zoom/measure on printed maps?**
A: No, but you can keep digital copy for interactive use.

**Q: How large are the map files?**
A: Typically 2-3 MB each, very manageable.

**Q: Can multiple people view same map?**
A: Yes, share the HTML file via email/cloud storage.

## 📚 More Information

For detailed information, see:
- **MAP_EXPORT_FEATURE.md** - Complete user guide
- **MAP_EXPORT_ARCHITECTURE.md** - How it works (technical)
- **MAP_EXPORT_IMPLEMENTATION.md** - What was built
- **MAP_EXPORT_SUMMARY.md** - Overview and use cases

---

**Status:** ✅ Ready to use  
**Last Updated:** February 3, 2026
