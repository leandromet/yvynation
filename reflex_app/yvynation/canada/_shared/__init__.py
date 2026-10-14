"""What the Canada page borrows from its parent app.

The Canada package was ported from camposcope/camposcope/canada, which imports
a handful of modules from camposcope itself (zones, tiles, the Leaflet
component, …). Those live here instead of being threaded through Yvynation's
own Brazil-side modules, so the two pages stay independent: Brazil keeps its
Folium workspace, Canada its native Leaflet map, and neither imports the
other's state.
"""
