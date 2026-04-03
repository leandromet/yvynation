"""
Geometry and buffer event handlers.
Covers drawn features, GeoJSON upload, KML import, buffer creation, and
geometry info popup.

Also defines BufferGeometry (used in AppState vars and imported by __init__).
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import hashlib
import json

import ee
import reflex as rx

logger = logging.getLogger(__name__)


def _compute_geometry_hash(geometry: Dict[str, Any]) -> str:
    """Compute a SHA256 hash of geometry coordinates to detect duplicates."""
    try:
        # Only hash the coordinates to identify duplicate geometries
        coords_str = json.dumps(geometry.get("coordinates", []), sort_keys=True)
        return hashlib.sha256(coords_str.encode()).hexdigest()
    except Exception as e:
        logger.warning(f"Error computing geometry hash: {e}")
        return ""


@dataclass
class BufferGeometry:
    """Represents a buffer geometry used for analysis."""

    name: str
    geometry: Dict[str, Any]
    created_at: str
    metadata: Dict[str, Any]


class GeometryMixin(rx.State, mixin=True):
    """Event handlers for drawn features, buffers, and geometry management."""

    # ---- Drawn feature CRUD ---------------------------------------------

    def set_selected_geometry(self, idx: int):
        """Select a drawn geometry by its list index."""
        if 0 <= idx < len(self.drawn_features):
            self.selected_geometry_idx = idx
            logger.info(f"Selected geometry {idx}: {self.drawn_features[idx].get('type', 'Unknown')}")

    def add_drawn_feature(self, feature: Dict[str, Any]):
        """Append a newly drawn feature, stamping its index fields.
        Auto-selects the first geometry for immediate analysis (no 'Save Drawing' needed).
        """
        feature["_idx"] = len(self.drawn_features)
        feature["_display_idx"] = len(self.drawn_features) + 1
        self.drawn_features.append(feature)
        self.all_drawn_features.append(feature)
        # Auto-select the first geometry when added
        if self.selected_geometry_idx is None:
            self.selected_geometry_idx = 0
        self.geometry_version += 1
        logger.info(f"Added drawn feature: {feature.get('type', 'Unknown')} (auto-selected)")

    def remove_geometry(self, idx: int):
        """Remove the drawn geometry whose _idx matches *idx*."""
        self.drawn_features = [f for f in self.drawn_features if f.get("_idx") != idx]
        if self.selected_geometry_idx == idx:
            self.selected_geometry_idx = None
        self.geometry_version += 1
        logger.info(f"Removed geometry _idx={idx}")

    def clear_geometries(self):
        """Clear all drawn geometries and reset selection."""
        self.drawn_features = []
        self.selected_geometry_idx = None
        self._processed_geometry_hashes = set()
        self.geometry_version += 1
        logger.info("Cleared all geometries")

    # kept as alias for backward compatibility
    def clear_drawn_features(self):
        self.drawn_features = []
        self._processed_geometry_hashes = set()
        self.geometry_version += 1

    # ---- EE geometry helper ---------------------------------------------

    def get_selected_geometry_ee(self) -> Optional[Any]:
        """Return the Earth Engine geometry for the currently selected feature."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            return None

        feature = self.drawn_features[self.selected_geometry_idx]
        if feature.get("_ee_geometry"):
            return feature["_ee_geometry"]

        coords = feature.get("coordinates")
        if coords:
            try:
                geom_type = feature.get("type")
                if geom_type == "Polygon":
                    return ee.Geometry.Polygon(coords)
                elif geom_type == "LineString":
                    return ee.Geometry.LineString(coords)
                elif geom_type == "Point":
                    return ee.Geometry.Point(coords)
            except Exception as e:
                logger.error(f"Error converting coordinates to EE geometry: {e}")
        return None

    # ---- GeoJSON from browser (JS bridge) -------------------------------

    def add_geojson_feature(self):
        """Placeholder — GeoJSON capture is handled by load_geojson_from_browser."""
        logger.info("GeoJSON feature add requested (form integration needed)")

    def capture_drawn_features(self):
        """Trigger JS extraction of drawn features from the Leaflet iframe."""
        pass  # JS callback → load_geojson_from_browser

    def load_geojson_from_browser(self, geojson_data: str):
        """
        Receive GeoJSON captured from the Leaflet Draw layer via JS bridge.

        *geojson_data* is a JSON string (FeatureCollection or error object).
        Uses geometry hashes to avoid duplicates when "Save Drawing" is clicked multiple times.
        """
        try:
            data = json.loads(geojson_data) if isinstance(geojson_data, str) else geojson_data

            if "error" in data and "features" not in data:
                self.error_message = str(data["error"])
                logger.warning(f"JS bridge error: {data['error']}")
                return

            features = data.get("features", [])
            if not features:
                self.error_message = "No drawn geometries found. Draw a polygon or rectangle first."
                return

            new_count = 0
            duplicate_count = 0
            
            for feature in features:
                try:
                    geom = feature.get("geometry", {})
                    geom_type = geom.get("type", "Unknown")
                    if not geom or not geom.get("coordinates"):
                        continue

                    # Compute hash to detect duplicates
                    geom_hash = _compute_geometry_hash(geom)
                    if geom_hash in self._processed_geometry_hashes:
                        logger.debug(f"Skipping duplicate geometry with hash {geom_hash}")
                        duplicate_count += 1
                        continue
                    
                    # Mark this geometry as processed
                    if geom_hash:
                        self._processed_geometry_hashes.add(geom_hash)

                    idx = len(self.drawn_features)
                    feature_obj = {
                        "_idx": idx,
                        "_display_idx": idx + 1,
                        "type": geom_type,
                        "name": f"Drawing {idx + 1}",
                        "geometry": geom,
                        "properties": feature.get("properties", {}),
                        "coordinates": geom.get("coordinates", []),
                    }
                    self.drawn_features.append(feature_obj)
                    self.all_drawn_features.append(feature_obj)
                    new_count += 1
                except Exception as feature_err:
                    logger.warning(f"Error processing feature: {feature_err}")

            if new_count:
                msg = f"Captured {new_count} new drawing(s)"
                if duplicate_count:
                    msg += f" ({duplicate_count} duplicate(s) skipped)"
                msg += f" ({len(self.drawn_features)} total)"
                self.error_message = msg
                self.geometry_version += 1
            elif duplicate_count:
                self.error_message = f"All {duplicate_count} drawing(s) were duplicates. No new geometries added."
            else:
                self.error_message = "No valid geometries could be extracted"

        except Exception as e:
            self.error_message = f"Error loading geometries: {e}"
            logger.error(f"Error in load_geojson_from_browser: {e}")

    # ---- Test geometry --------------------------------------------------

    def add_test_geometry(self):
        """Add a sample polygon for UI testing (no Earth Engine required)."""
        idx = len(self.drawn_features)
        test_feature = {
            "_idx": idx,
            "_display_idx": idx + 1,
            "type": "Polygon",
            "name": "Test Territory",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-60.5, -3.0], [-60.0, -3.0], [-60.0, -2.5], [-60.5, -2.5], [-60.5, -3.0],
                ]],
            },
            "properties": {"name": "Test Territory", "description": "Sample geometry for testing"},
            "coordinates": [[
                [-60.5, -3.0], [-60.0, -3.0], [-60.0, -2.5], [-60.5, -2.5], [-60.5, -3.0],
            ]],
        }
        self.drawn_features.append(test_feature)
        self.all_drawn_features.append(test_feature)
        self.geometry_version += 1
        self.error_message = "✓ Test geometry loaded. You can now test the analysis features."

    # ---- Geometry info popup --------------------------------------------

    def show_geometry_info(self, geometry_idx: int):
        """Populate and show the geometry info popup for a given index."""
        if 0 <= geometry_idx < len(self.drawn_features):
            feature = self.drawn_features[geometry_idx]
            self.geometry_popup_info = {
                "index": geometry_idx,
                "type": feature.get("type", "Unknown"),
                "area_km2": feature.get("area_km2", 0),
                "coordinates_count": self._count_coordinates(feature.get("geometry", {})),
                "created_at": feature.get("created_at", "Unknown"),
                "name": feature.get("name", f"Geometry {geometry_idx}"),
            }
            self.show_geometry_popup = True

    def hide_geometry_info(self):
        """Hide the geometry info popup and clear its data."""
        self.show_geometry_popup = False
        self.geometry_popup_info = {}

    def _count_coordinates(self, geometry: Dict[str, Any]) -> int:
        """Recursively count coordinate pairs in a GeoJSON geometry."""
        if not geometry:
            return 0

        def _count(obj):
            if isinstance(obj, list) and obj:
                if isinstance(obj[0], (int, float)):
                    return 1
                return sum(_count(item) for item in obj)
            return 0

        return _count(geometry.get("coordinates", []))

    # ---- Geometry upload ------------------------------------------------

    def upload_geometry_from_geojson(
        self, geojson_data: Dict[str, Any], file_name: str = "Uploaded Geometry"
    ) -> bool:
        """Process and store an uploaded GeoJSON geometry."""
        try:
            from ..utils.buffer_utils import convert_feature_collection_to_ee_geometry
            from ..utils.geometry_handler import validate_geometry

            is_valid, error_msg = validate_geometry(geojson_data)
            if not is_valid:
                self.error_message = f"Invalid geometry: {error_msg}"
                return False

            feature_name = file_name.rsplit(".", 1)[0] if file_name else "Uploaded Geometry"

            ee_geometry = convert_feature_collection_to_ee_geometry(geojson_data)
            if not ee_geometry:
                self.error_message = "Failed to convert geometry to Earth Engine format"
                return False

            raw_geom = (
                geojson_data.get("features", [{}])[0].get("geometry")
                if geojson_data.get("type") == "FeatureCollection"
                else geojson_data.get("geometry")
            )
            feature = {
                "type": "Feature",
                "name": feature_name,
                "properties": {"name": feature_name, "type": "uploaded_geometry", "source": "upload"},
                "geometry": raw_geom,
            }
            self.add_drawn_feature(feature)
            # Auto-selection happens inside add_drawn_feature
            self.error_message = ""
            return True

        except Exception as e:
            self.error_message = f"Error processing geometry: {e}"
            return False

    async def handle_geometry_upload(self, files: list):
        """Handle file upload from the geometry upload widget (.json/.geojson/.kml)."""
        try:
            from ..utils.geometry_handler import parse_geojson, parse_kml, validate_geometry

            if not files:
                self.error_message = "No file selected"
                return

            upload_data = files[0]
            if not upload_data:
                self.error_message = "No file data"
                return

            file_name = getattr(upload_data, "name", "unknown")

            try:
                if hasattr(upload_data, "read"):
                    file_content = await upload_data.read()
                else:
                    file_content = upload_data
            except Exception as e:
                self.error_message = f"Could not read file: {e}"
                return

            if isinstance(file_content, bytes):
                try:
                    file_content = file_content.decode("utf-8")
                except UnicodeDecodeError:
                    self.error_message = "File must be UTF-8 encoded text"
                    return

            file_ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""

            if file_ext in ("json", "geojson"):
                geojson_data = parse_geojson(file_content, file_name)
            elif file_ext == "kml":
                geojson_data = parse_kml(file_content, file_name)
            else:
                self.error_message = f"Unsupported file type: .{file_ext}. Use .json or .kml"
                return

            if not geojson_data:
                self.error_message = "Failed to parse file. Check format and try again."
                return

            success = self.upload_geometry_from_geojson(geojson_data, file_name)
            if success:
                self.error_message = f"✅ Loaded {file_name}"

        except Exception as e:
            self.error_message = f"Upload error: {e}"

    # ---- Buffer management ----------------------------------------------

    def add_buffer_geometry(
        self, name: str, geometry: Dict[str, Any], metadata: Dict[str, Any] = None
    ):
        """Store a buffer geometry in state."""
        import datetime
        # BufferGeometry is defined at the top of this module

        buffer_obj = BufferGeometry(
            name=name,
            geometry=geometry,
            created_at=datetime.datetime.now().isoformat(),
            metadata=metadata or {},
        )
        self.buffer_geometries[name] = buffer_obj

    def delete_buffer_geometry(self, name: str):
        """Remove a buffer geometry from state."""
        if name in self.buffer_geometries:
            del self.buffer_geometries[name]
        if self.current_buffer_for_analysis == name:
            self.current_buffer_for_analysis = None

    def set_current_buffer(self, name: Optional[str]):
        """Set the active buffer for analysis."""
        self.current_buffer_for_analysis = name

    def toggle_buffer_compare_mode(self):
        """Toggle buffer comparison mode."""
        self.buffer_compare_mode = not self.buffer_compare_mode

    def create_buffer_from_geometry(self, geometry_name: str, buffer_distance_km: float) -> bool:
        """Create an external buffer around the named geometry."""
        try:
            from ..utils.buffer_utils import (
                create_external_buffer,
                create_buffer_geometry_dict,
                convert_geojson_to_ee_geometry,
            )
            from ..utils.ee_service_extended import get_ee_service
            import datetime

            ee_geom = None

            # 1. Try EE territory geometry
            try:
                ee_service = get_ee_service()
                territory_geom = ee_service.get_territory_geometry(geometry_name)
                if territory_geom:
                    ee_geom = territory_geom
            except Exception:
                pass

            # 2. Search drawn features
            if not ee_geom:
                for feat in self.all_drawn_features + self.drawn_features:
                    name = feat.get("name") or feat.get("properties", {}).get("name", "")
                    if name == geometry_name:
                        ee_geom = convert_geojson_to_ee_geometry(feat)
                        break

            # 3. Territory GeoJSON cache
            if not ee_geom:
                for feat in self.territory_geojson_features:
                    if feat.get("name") == geometry_name:
                        ee_geom = convert_geojson_to_ee_geometry(feat)
                        break

            if not ee_geom:
                self.error_message = f"Geometry '{geometry_name}' not found"
                return False

            buffer_geom = create_external_buffer(ee_geom, buffer_distance_km)
            if not buffer_geom:
                self.error_message = "Failed to create buffer"
                return False

            buffer_name = f"Buffer {buffer_distance_km}km - {geometry_name}"
            buffer_dict = create_buffer_geometry_dict(
                name=buffer_name,
                ee_geometry=buffer_geom,
                buffer_size_km=buffer_distance_km,
                source_name=geometry_name,
                created_at=datetime.datetime.now().isoformat(),
            )
            self.add_buffer_geometry(buffer_name, buffer_dict)
            self.current_buffer_for_analysis = buffer_name
            self.error_message = ""
            return True

        except Exception as e:
            self.error_message = f"Error creating buffer: {e}"
            return False

    def handle_create_buffer(self):
        """Handle buffer creation from UI input (gets distance from state)."""
        try:
            distance_km = float(self.buffer_distance_input)
            if distance_km <= 0:
                self.error_message = "Buffer distance must be greater than 0"
                return
            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Select a geometry first"
                return
            
            # Get the geometry name/identifier from the selected feature
            feature = self.drawn_features[self.selected_geometry_idx]
            geometry_name = feature.get("name") or feature.get("properties", {}).get("name") or f"geometry_{self.selected_geometry_idx}"
            
            self.create_buffer_from_geometry(geometry_name, distance_km)
        except ValueError:
            self.error_message = "Invalid buffer distance. Enter a number."
        except Exception as e:
            self.error_message = f"Buffer error: {e}"

    # ---- Geometry analysis type / year ----------------------------------

    def set_geometry_analysis_type(self, analysis_type: str):
        """Set analysis type for drawn geometries ('mapbiomas' or 'hansen')."""
        if analysis_type in ("mapbiomas", "hansen"):
            self.geometry_analysis_type = analysis_type

    def set_geometry_analysis_year(self, year: Any):
        """Set the year for geometry analysis (int for MapBiomas, str for Hansen)."""
        try:
            if self.geometry_analysis_type == "mapbiomas":
                self.geometry_analysis_year = int(year)
            else:
                self.geometry_analysis_year = str(year)
        except (ValueError, TypeError):
            pass
