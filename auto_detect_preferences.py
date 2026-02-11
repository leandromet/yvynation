"""
Auto-detection module for language and region preferences.
Detects user location via browser Geolocation API (streamlit-geolocation) and browser language.
Uses GPS coordinates directly to determine region (no reverse geocoding).
"""

import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from typing import Optional


def get_browser_language() -> Optional[str]:
    """
    Detect browser's preferred language using JavaScript.
    Stores result in localStorage which is read on subsequent page loads.
    
    Returns:
        'en' or 'pt-br' based on browser language
    """
    # Inject JavaScript to detect browser language on page load
    lang_detect_js = """
    <script>
    if (!localStorage.getItem('streamlit_browser_lang')) {
        const browserLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
        const detectedLang = browserLang.includes('pt') ? 'pt-br' : 'en';
        localStorage.setItem('streamlit_browser_lang', detectedLang);
    }
    </script>
    """
    
    st.markdown(lang_detect_js, unsafe_allow_html=True)
    
    # Check if we have language in query params (user's browser sent it)
    if 'lang' in st.query_params:
        lang = str(st.query_params['lang']).lower()
        if 'pt' in lang:
            return 'pt-br'
        return 'en'
    
    # Check session state cache
    if 'detected_browser_language' in st.session_state:
        return st.session_state.detected_browser_language
    
    return None


def get_region_from_coordinates(lat: float, lng: float) -> str:
    """
    Determine region from GPS coordinates.
    
    Args:
        lat: Latitude (positive = North)
        lng: Longitude (negative = West)
    
    Returns:
        'Canada' if North America, 'Brazil' otherwise
    """
    # North America (latitude > 10N, longitude < 0W)
    if lat > 10 and lng < 0:
        return 'Canada'
    # Default to Brazil
    return 'Brazil'


def get_language_from_coordinates(lat: float, lng: float) -> Optional[str]:
    """
    Determine language from GPS coordinates.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        'en' if outside South America, None to use browser language for SA
    """
    # South America rough bounds: -5 to -56 latitude, -30 to -85 longitude
    in_south_america = (-56 <= lat <= -5) and (-85 <= lng <= -30)
    
    if not in_south_america:
        # Outside South America → English
        return 'en'
    
    # Inside South America → use browser language or default
    return None


def get_user_location_and_region() -> Optional[str]:
    """
    Get user's location from browser geolocation and determine region/language.
    Uses GPS coordinates directly (no reverse geocoding).
    
    Returns:
        Region name ('Canada' or 'Brazil') or None if denied/failed
    """
    # Get location from browser via streamlit-geolocation
    location = streamlit_geolocation()
    
    if location and location.get('latitude') is not None and location.get('longitude') is not None:
        lat = location['latitude']
        lng = location['longitude']
        
        # Determine region from coordinates
        region = get_region_from_coordinates(lat, lng)
        
        # Determine language from coordinates
        lang_override = get_language_from_coordinates(lat, lng)
        
        # Store both in session state for apply_auto_detected_preferences
        st.session_state.detected_region_from_location = region
        st.session_state.detected_language_override = lang_override
        st.session_state.detected_coordinates = {'lat': lat, 'lng': lng}
        
        st.success(f"✅ Location detected: {region} ({lat:.1f}°, {lng:.1f}°)")
        return region
    
    return None


def should_auto_detect() -> bool:
    """Check if user has already made a preference choice (not first visit)."""
    return "auto_detect_checked" not in st.session_state


def map_country_to_region(country_code: str) -> str:
    """
    Map country code to supported region.
    
    Returns:
        'Brazil', 'Canada', or default based on geography
    """
    country_code = country_code.upper() if country_code else ""
    
    # Brazil
    if country_code == 'BR':
        return 'Brazil'
    

    
    if country_code in north_american_codes:
        return 'Canada'
    
    # South America, Africa, Europe, Asia → Brazil (has broader coverage)
    # Default to Brazil as it's the primary focus region
    return 'Brazil'


def map_country_to_language(country_code: str) -> str:
    """
    Map country code to preferred language.
    
    Returns:
        'en' or 'pt-br'
    """
    country_code = country_code.upper() if country_code else ""
    
    if country_code == 'BR':
        return 'pt-br'
    else:
        # Default to English
        return 'en'


def show_auto_detect_permission_dialog():
    """
    Removed - now directly shows geolocation request on first visit.
    """
    pass


def show_geolocation_request():
    """
    Show the geolocation request widget using streamlit-geolocation.
    Shows on first visit to auto-detect location and language.
    """
    # Skip if user has already granted location permission
    if "detected_region_from_location" in st.session_state:
        return
    
    with st.sidebar:
        with st.container(border=True):
            st.markdown("#### 📍 Set Your Location & Language")
            st.markdown("Click below to allow location access (or select manually below):")
            
            # Get region from browser geolocation using coordinates directly
            region = get_user_location_and_region()
            
            if region:
                st.session_state.auto_detect_checked = True


def apply_auto_detected_preferences():
    """
    Apply auto-detected preferences to session state.
    Runs after location is detected from GPS coordinates.
    """
    # Get detected region from coordinates
    detected_region = st.session_state.get('detected_region_from_location')
    lang_override = st.session_state.get('detected_language_override')
    
    # Get browser language
    browser_lang = get_browser_language()
    
    # Set language
    if st.session_state.get('language') == 'en':  # Only override default
        # Prefer language override from coordinates
        if lang_override:
            st.session_state.language = lang_override
        elif browser_lang:
            st.session_state.language = browser_lang
        
        st.session_state.language_auto_detected = True
    
    # Set region
    if detected_region and st.session_state.get('selected_country') == 'Brazil':  # Only override default
        st.session_state.selected_country = detected_region
        st.session_state.region_auto_detected = True
    
    print(f"✅ Final: Language={st.session_state.language}, Region={st.session_state.selected_country}")


def show_auto_detect_confirmation():
    """
    Show confirmation of auto-detected preferences.
    Only shown if preferences were auto-detected.
    """
    if not st.session_state.get('language_auto_detected') and not st.session_state.get('region_auto_detected'):
        return  # Nothing was auto-detected
    
    if "auto_detect_confirmation_shown" in st.session_state:
        return  # Already showed this session
    
    st.session_state.auto_detect_confirmation_shown = True
    
    with st.sidebar:
        with st.container(border=True):
            st.markdown("#### ✨ System Configured")
            
            if st.session_state.get('language_auto_detected'):
                lang_display = "🇬🇧 English" if st.session_state.language == 'en' else "🇧🇷 Português"
                st.caption(f"**Language**: {lang_display}")
            
            if st.session_state.get('region_auto_detected'):
                flag = "🇧🇷" if st.session_state.selected_country == "Brazil" else "🇨🇦"
                st.caption(f"**Region**: {flag} {st.session_state.selected_country}")
            
            st.caption("💡 Change anytime in the selectors below")


def initialize_preferences():
    """
    Initialize preferences with auto-detection if needed.
    On first visit, directly shows geolocation request (no lengthy dialog).
    """
    # Initialize default values
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = "Brazil"
    
    # First visit - directly show geolocation request (no permission dialog)
    if "auto_detect_checked" not in st.session_state:
        st.session_state.auto_detect_enabled = True
        st.session_state.auto_detect_checked = True
    
    # Show geolocation widget if enabled and haven't detected location yet
    if st.session_state.get("auto_detect_enabled") and "detected_region_from_location" not in st.session_state:
        show_geolocation_request()
        
    # Apply detected preferences
    if "detected_region_from_location" in st.session_state:
        apply_auto_detected_preferences()
        show_auto_detect_confirmation()
