import streamlit as st
import folium
from streamlit_folium import st_folium
import googlemaps
from test_func import generate_content
import base64
import io
from PIL import Image
import requests

st.set_page_config(page_title="Forest Firefighting Planning System", layout="wide")

st.title("Forest Firefighting Planning System")
st.write("Upload a description or a map and we'll help you plan a drone firefighting route.")

# Google Maps API Key (您需要替换为您的实际API密钥)
GOOGLE_MAPS_API_KEY = "AIzaSyDK7bsI0iO4u_4uYghuSAloEhrFPEeQyoY"
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

def generate_map_screenshot(map_center, fire_points, drone_start_point):
    """
    Generate a map screenshot using Google Static Maps API
    """
    try:
        # Build markers string for fire points
        markers = []
        
        # Add fire points
        for i, point in enumerate(fire_points):
            markers.append(f"color:red|label:F{i+1}|{point['lat']},{point['lng']}")
        
        # Add drone start point
        if drone_start_point:
            markers.append(f"color:blue|label:D|{drone_start_point['lat']},{drone_start_point['lng']}")
        
        # Construct Google Static Maps URL
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        params = {
            "center": f"{map_center[0]},{map_center[1]}",
            "zoom": 12,
            "size": "640x480",
            "maptype": "satellite",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        # Add markers to URL
        if markers:
            params["markers"] = "|".join(markers)
        
        # Make request to Google Static Maps API
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            # Convert response to PIL Image
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to base64 for Gemini
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            st.info("Map screenshot generated successfully.")
            
            return img_base64
        else:
            st.error(f"Failed to generate map screenshot: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error generating map screenshot: {e}")
        return None


# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "fire_points" not in st.session_state:
    st.session_state.fire_points = []
if "drone_start_point" not in st.session_state:
    st.session_state.drone_start_point = None

# Create two columns for layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Map Controls")
    
    # Location search
    location_search = st.text_input("Search location (address or coordinates)")
    if st.button("Search Location"):
        if location_search:
            try:
                geocode_result = gmaps.geocode(location_search)
                if geocode_result:
                    location = geocode_result[0]['geometry']['location']
                    st.session_state.map_center = [location['lat'], location['lng']]
                    st.success(f"Found: {geocode_result[0]['formatted_address']}")
                else:
                    st.error("Location not found")
            except Exception as e:
                st.error(f"Error searching location: {e}")
    
    # Point management
    st.subheader("Point Management")
    
    # Add fire point
    if st.button("🔥 Add Fire Point (Click on Map)"):
        st.session_state.adding_fire_point = True
        st.info("Click on the map to add a fire point")
    
    # Add drone start point
    if st.button("🚁 Set Drone Start Point (Click on Map)"):
        st.session_state.adding_drone_point = True
        st.info("Click on the map to set drone start point")
    
    # Clear points
    if st.button("Clear All Points"):
        st.session_state.fire_points = []
        st.session_state.drone_start_point = None
        st.success("All points cleared")
    
    # Capture map screenshot button
    if st.button("📸 Capture Map Screenshot"):
        if st.session_state.fire_points or st.session_state.drone_start_point:
            st.session_state.capture_map_screenshot = True
            st.info("Map screenshot will be included in next message")
        else:
            st.warning("Please add some points to the map first")
    
    # Display current points
    if st.session_state.fire_points:
        st.write("**Fire Points:**")
        for i, point in enumerate(st.session_state.fire_points):
            st.write(f"Fire {i+1}: {point['lat']:.6f}, {point['lng']:.6f}")
    
    if st.session_state.drone_start_point:
        point = st.session_state.drone_start_point
        st.write(f"**Drone Start:** {point['lat']:.6f}, {point['lng']:.6f}")

    # Support image upload (used only once at the beginning)
    if "uploaded_image" not in st.session_state:
        uploaded_image = st.file_uploader("Upload a map image (optional)", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            st.session_state.uploaded_image = uploaded_image
            st.image(uploaded_image, caption="Uploaded map", use_container_width=True)
    else:
        st.image(st.session_state.uploaded_image, caption="Uploaded map", use_container_width=True)

    # Text input for prompt
    user_input = st.text_input("Enter your message (situation update, questions, etc.)")

    # Submit button for continuing the conversation
    if st.button("Send"):
        if user_input.strip() == "":
            st.warning("Please enter a message.")
        else:
            with st.spinner("Generating response..."):
                # Include map data in the context
                map_context = {
                    "fire_points": st.session_state.fire_points,
                    "drone_start_point": st.session_state.drone_start_point
                }
                
                # Generate map screenshot if requested
                map_screenshot = None
                if st.session_state.get('capture_map_screenshot', False):
                    try:
                        map_screenshot = generate_map_screenshot(
                            st.session_state.map_center,
                            st.session_state.fire_points,
                            st.session_state.drone_start_point
                        )
                        st.session_state.capture_map_screenshot = False
                    except Exception as e:
                        st.error(f"Error capturing map screenshot: {e}")
                
                # Append input and result to history
                result = generate_content(
                    user_input, 
                    st.session_state.uploaded_image if "uploaded_image" in st.session_state else None,
                    map_context,
                    map_screenshot
                )
                st.session_state.history.append({
                    "input": user_input,
                    "result": result,
                    "has_map_screenshot": map_screenshot is not None
                })

    # Clear history button
    if st.button("Clear Conversation History"):
        st.session_state.history.clear()
        if "uploaded_image" in st.session_state:
            del st.session_state.uploaded_image
        st.success("Conversation history cleared.")

with col2:
    st.subheader("Interactive Map")
    
    # Initialize map center
    if "map_center" not in st.session_state:
        st.session_state.map_center = [48.1351, 11.5820]  # Munich coordinates as default
    
    # Create folium map
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    # Add fire points to map
    for i, point in enumerate(st.session_state.fire_points):
        folium.Marker(
            [point['lat'], point['lng']],
            popup=f"Fire Point {i+1}",
            tooltip=f"Fire Point {i+1}",
            icon=folium.Icon(color='red', icon='fire', prefix='fa')
        ).add_to(m)
    
    # Add drone start point to map
    if st.session_state.drone_start_point:
        point = st.session_state.drone_start_point
        folium.Marker(
            [point['lat'], point['lng']],
            popup="Drone Start Point",
            tooltip="Drone Start Point",
            icon=folium.Icon(color='blue', icon='plane', prefix='fa')
        ).add_to(m)
    
    # Display map and capture clicks
    map_data = st_folium(m, key="map", width=700, height=500)
    
    # Handle map clicks
    if map_data['last_clicked']:
        clicked_lat = map_data['last_clicked']['lat']
        clicked_lng = map_data['last_clicked']['lng']
        
        if st.session_state.get('adding_fire_point', False):
            st.session_state.fire_points.append({
                'lat': clicked_lat,
                'lng': clicked_lng
            })
            st.session_state.adding_fire_point = False
            st.success(f"Fire point added at: {clicked_lat:.6f}, {clicked_lng:.6f}")
            st.rerun()
        
        elif st.session_state.get('adding_drone_point', False):
            st.session_state.drone_start_point = {
                'lat': clicked_lat,
                'lng': clicked_lng
            }
            st.session_state.adding_drone_point = False
            st.success(f"Drone start point set at: {clicked_lat:.6f}, {clicked_lng:.6f}")
            st.rerun()

# Display conversation history
if st.session_state.history:
    st.markdown("---")
    st.subheader("Conversation History")
    for i, record in enumerate(st.session_state.history, 1):
        st.markdown(f"**User {i}:** {record['input']}")
        st.markdown(f"**System {i}:** {record['result']}")

