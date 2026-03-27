# Code Reference - Key Changes

## 1. Layout Reorganization (index.py)

### Before: Horizontal Split Layout
```python
rx.hstack(
    sidebar(),
    rx.hstack(  # HORIZONTAL split
        leaflet_map(),     # 50% width
        results_panel(),   # 50% width
        width="100%"
    )
)
```

### After: Vertical Stack Layout
```python
rx.hstack(
    sidebar(),
    rx.box(width="4px", on_mouse_down=AppState.start_resize),  # Resize handle
    rx.vstack(  # VERTICAL stack
        leaflet_map(),     # Full width
        results_panel(),   # Full width, below map
        width="100%"
    )
)
```

## 2. Year Button Improvements (sidebar.py)

### Before: Fixed Grid Layout
```python
rx.vstack(
    rx.foreach(
        [MAPBIOMAS_YEARS[i:i+5] for i in range(0, len(MAPBIOMAS_YEARS), 5)],
        lambda row: rx.hstack(
            rx.foreach(
                row,
                lambda year: rx.button(
                    str(year),
                    width="100%",  # Each button 20% of 100%
                    size="1"
                )
            ),
            width="100%"
        )
    )
)
```

### After: Responsive Wrap Layout
```python
rx.wrap(
    rx.foreach(
        MAPBIOMAS_YEARS,
        lambda year: rx.button(
            str(year),
            size="sm",          # Smaller size
            padding="6px 10px", # Compact padding
            font_size="11px"    # Smaller text
        )
    ),
    spacing="1",
    width="100%"  # Buttons wrap naturally
)
```

## 3. Sidebar Resize Feature (state.py)

### State Variables
```python
class AppState(rx.State):
    sidebar_width: int = 300          # Sidebar width in pixels
    is_resizing_sidebar: bool = False # Whether currently resizing
```

### State Methods
```python
def start_resize(self):
    """Start resizing the sidebar."""
    self.is_resizing_sidebar = True

def end_resize(self):
    """Stop resizing the sidebar."""
    self.is_resizing_sidebar = False

def update_sidebar_width(self, width: int):
    """Update sidebar width (called during resize)."""
    constrained_width = max(200, min(500, width))
    self.sidebar_width = constrained_width
```

### Index Layout Integration
```python
rx.box(
    sidebar(),
    width=rx.cond(
        AppState.sidebar_width != 0,
        f"{AppState.sidebar_width}px",
        "300px"
    ),
    max_width="500px",
    min_width="200px"
)

# Resize handle
rx.box(
    width="4px",
    cursor="col-resize",
    on_mouse_down=lambda: AppState.start_resize()
)

# Main content
rx.hstack(
    ...,
    on_mouse_up=lambda: AppState.end_resize(),
    on_mouse_leave=lambda: AppState.end_resize()
)
```

## 4. Geometry Information Popup (geometry_popup.py)

### State Variables
```python
class AppState(rx.State):
    show_geometry_popup: bool = False        # Popup visibility
    geometry_popup_info: Dict[str, Any] = {} # Popup content
```

### State Methods
```python
def show_geometry_info(self, geometry_idx: int):
    """Show geometry info popup for a specific geometry."""
    if 0 <= geometry_idx < len(self.drawn_features):
        feature = self.drawn_features[geometry_idx]
        self.geometry_popup_info = {
            "index": geometry_idx,
            "type": feature.get("type", "Unknown"),
            "area_km2": feature.get("area_km2", 0),
            "coordinates_count": self._count_coordinates(
                feature.get("geometry", {})
            ),
            "created_at": feature.get("created_at", "Unknown"),
            "name": feature.get("name", f"Geometry {geometry_idx}"),
        }
        self.show_geometry_popup = True

def hide_geometry_info(self):
    """Hide geometry info popup."""
    self.show_geometry_popup = False
    self.geometry_popup_info = {}

def _count_coordinates(self, geometry: Dict[str, Any]) -> int:
    """Count total coordinates in a geometry."""
    if not geometry:
        return 0
    
    coords = geometry.get("coordinates", [])
    
    def count_coords(coords_obj):
        if isinstance(coords_obj, list):
            if len(coords_obj) > 0:
                if isinstance(coords_obj[0], (int, float)):
                    return 1
                else:
                    total = 0
                    for item in coords_obj:
                        total += count_coords(item)
                    return total
        return 0
    
    return count_coords(coords)
```

### Popup Component
```python
def geometry_info_popup() -> rx.Component:
    """Display popup with detailed geometry information."""
    return rx.cond(
        AppState.show_geometry_popup,
        rx.dialog(
            rx.dialog_content(
                rx.dialog_header("📍 Geometry Information"),
                rx.dialog_body(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Name:", font_weight="bold"),
                            rx.text(AppState.geometry_popup_info.get("name"))
                        ),
                        rx.hstack(
                            rx.text("Type:", font_weight="bold"),
                            rx.badge(AppState.geometry_popup_info.get("type"))
                        ),
                        rx.hstack(
                            rx.text("Area:", font_weight="bold"),
                            rx.text(f"{AppState.geometry_popup_info['area_km2']:.2f} km²")
                        ),
                        # ... more fields
                    )
                ),
                rx.dialog_footer(
                    rx.hstack(
                        rx.button("🗑️ Delete", ...),
                        rx.button("Analyze", ...),
                        rx.button("Close", ...)
                    )
                )
            )
        ),
        rx.box()
    )
```

## 5. Index Component Update

### Imports
```python
from ..components.geometry_popup import geometry_info_popup

def index() -> rx.Component:
    """Main application layout with modern design."""
    return rx.vstack(
        navbar(),
        # ... main content ...
        error_toast(AppState),
        loading_overlay(AppState),
        geometry_info_popup(),  # NEW: Add popup component
        width="100%",
        height="100vh"
    )
```

## 6. CSS/Styling Details

### Resize Handle Styling
```python
rx.box(
    width="4px",
    bg="linear-gradient(90deg, #d0d0d0 0%, #a0a0a0 50%, #d0d0d0 100%)",
    cursor="col-resize",
    transition="background-color 0.2s ease",
    _hover={"bg": "linear-gradient(90deg, #a0a0a0 0%, #707070 50%, #a0a0a0 100%)"},
    user_select="none"
)
```

### Sidebar Container Styling
```python
rx.box(
    sidebar(),
    width=f"{AppState.sidebar_width}px",
    max_width="500px",
    min_width="200px",
    overflow_y="auto",
    overflow_x="hidden",
    border_right="2px solid #d0d0d0",
    bg="white",
    position="relative"
)
```

### Year Button Styling
```python
rx.button(
    str(year),
    size="sm",
    padding="6px 10px",
    font_size="11px",
    is_outline=rx.cond(selected, False, True),
    color_scheme=rx.cond(selected, "green", "gray")
)
```

