import streamlit as st
import folium
from streamlit_folium import st_folium
import googlemaps
from test_func import generate_content
import base64
import io
from PIL import Image
import requests
import json
import os
from datetime import datetime

st.set_page_config(page_title="Forest Firefighting Planning System", layout="wide")

st.title("Forest Firefighting Planning System")
st.write("Upload a description or a map and we'll help you plan a drone firefighting route.")

# Google Maps API Key (您需要替换为您的实际API密钥)
GOOGLE_MAPS_API_KEY = "AIzaSyDK7bsI0iO4u_4uYghuSAloEhrFPEeQyoY"
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# 创建保存数据的目录
def create_data_directories():
    """创建保存数据的目录结构"""
    base_dir = "saved_data"
    subdirs = ["maps", "coordinates", "screenshots"]
    
    for subdir in subdirs:
        path = os.path.join(base_dir, subdir)
        os.makedirs(path, exist_ok=True)
    
    return base_dir

def save_coordinates_to_file(fire_points, drone_start_point, map_center):
    """保存坐标数据到JSON文件"""
    try:
        base_dir = create_data_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coordinates_{timestamp}.json"
        filepath = os.path.join(base_dir, "coordinates", filename)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "map_center": map_center,
            "fire_points": fire_points,
            "drone_start_point": drone_start_point,
            "total_fire_points": len(fire_points),
            "has_drone_point": drone_start_point is not None
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ 坐标数据已保存到: {filepath}")
        return filepath
    except Exception as e:
        st.error(f"❌ 保存坐标数据失败: {e}")
        return None

def save_map_image(image_base64, fire_points, drone_start_point, map_center=None, zoom_level=None):
    """保存地图截图到本地文件"""
    try:
        base_dir = create_data_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"map_screenshot_{timestamp}.png"
        filepath = os.path.join(base_dir, "screenshots", filename)
        
        # 将base64解码并保存为图片
        image_data = base64.b64decode(image_base64)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # 同时保存图片的元数据
        metadata_filename = f"map_metadata_{timestamp}.json"
        metadata_filepath = os.path.join(base_dir, "screenshots", metadata_filename)
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "image_file": filename,
            "fire_points": fire_points,
            "drone_start_point": drone_start_point,
            "total_fire_points": len(fire_points),
            "has_drone_point": drone_start_point is not None,
            "map_center": map_center,
            "zoom_level": zoom_level,
            "image_size": "640x480"
        }
        
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ 地图截图已保存到: {filepath}")
        st.success(f"✅ 图片元数据已保存到: {metadata_filepath}")
        return filepath, metadata_filepath
    except Exception as e:
        st.error(f"❌ 保存地图截图失败: {e}")
        return None, None

def load_saved_coordinates():
    """加载已保存的坐标文件列表"""
    try:
        coord_dir = os.path.join("saved_data", "coordinates")
        if not os.path.exists(coord_dir):
            return []
        
        files = [f for f in os.listdir(coord_dir) if f.endswith('.json')]
        return sorted(files, reverse=True)  # 最新的在前
    except Exception as e:
        st.error(f"❌ 加载坐标文件列表失败: {e}")
        return []

def load_coordinates_from_file(filename):
    """从文件加载坐标数据"""
    try:
        filepath = os.path.join("saved_data", "coordinates", filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"❌ 加载坐标文件失败: {e}")
        return None

def convert_coordinates_to_pixels(lat_lng_coords, map_center, zoom_level=12, image_size=(640, 480)):
    """
    将经纬度坐标转换为图片上的像素坐标
    这是一个简化的转换，实际的Google Maps投影更复杂
    """
    try:
        import math
        
        # Google Maps 使用Web Mercator投影
        def lat_lng_to_pixel(lat, lng, center_lat, center_lng, zoom, img_width, img_height):
            # 计算相对于中心点的偏移
            lat_rad = math.radians(lat)
            lng_rad = math.radians(lng)
            center_lat_rad = math.radians(center_lat)
            center_lng_rad = math.radians(center_lng)
            
            # 简化的像素计算（近似）
            scale = 2 ** zoom
            pixel_per_degree_x = img_width / (360 / scale * 2)
            pixel_per_degree_y = img_height / (180 / scale)
            
            # 计算像素坐标
            x = img_width / 2 + (lng - center_lng) * pixel_per_degree_x
            y = img_height / 2 - (lat - center_lat) * pixel_per_degree_y
            
            return int(x), int(y)
        
        pixel_coords = []
        center_lat, center_lng = map_center
        
        for coord in lat_lng_coords:
            if coord:  # 检查坐标是否存在
                x, y = lat_lng_to_pixel(
                    coord['lat'], coord['lng'], 
                    center_lat, center_lng, 
                    zoom_level, image_size[0], image_size[1]
                )
                pixel_coords.append({'x': x, 'y': y, 'lat': coord['lat'], 'lng': coord['lng']})
        
        return pixel_coords
    except Exception as e:
        st.error(f"❌ 坐标转换失败: {e}")
        return []

def calculate_optimal_map_view(fire_points, drone_start_point):
    """计算包含所有点的最佳地图中心和缩放级别"""
    all_points = []
    
    # 添加火点
    if fire_points:
        all_points.extend(fire_points)
    
    # 添加无人机起始点
    if drone_start_point:
        all_points.append(drone_start_point)
    
    if not all_points:
        # 如果没有点，返回默认值
        return [48.1351, 11.5820], 12
    
    if len(all_points) == 1:
        # 如果只有一个点，以该点为中心
        point = all_points[0]
        return [point['lat'], point['lng']], 15
    
    # 计算边界
    lats = [p['lat'] for p in all_points]
    lngs = [p['lng'] for p in all_points]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    
    # 计算中心点
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    
    # 计算合适的缩放级别
    lat_diff = max_lat - min_lat
    lng_diff = max_lng - min_lng
    max_diff = max(lat_diff, lng_diff)
    
    # 添加一些边距，确保点不会贴边
    padding_factor = 1.2
    max_diff = max_diff * padding_factor
    
    # 根据点的分布范围确定缩放级别
    if max_diff < 0.001:      # 非常近的点
        zoom = 35
    elif max_diff < 0.005:    # 很近的点
        zoom = 25
    elif max_diff < 0.01:     # 近距离
        zoom = 20
    elif max_diff < 0.05:     # 中等距离
        zoom = 15
    elif max_diff < 0.1:      # 较远距离
        zoom = 13
    elif max_diff < 0.5:      # 远距离
        zoom = 10
    else:                     # 很远距离
        zoom = 8
    
    return [center_lat, center_lng], zoom

def generate_map_screenshot(fire_points, drone_start_point):
    """
    Generate a map screenshot using Google Static Maps API with dynamic centering
    注意：移除了map_center参数，完全依赖动态计算
    """
    try:
        # 首先检查是否有点数据
        if not fire_points and not drone_start_point:
            st.warning("⚠️ 没有标记点，无法生成截图")
            return None
        
        # 使用动态计算的地图中心和缩放级别
        optimal_center, optimal_zoom = calculate_optimal_map_view(fire_points, drone_start_point)
        
        st.info(f"🎯 使用动态计算的视图参数 - 中心: ({optimal_center[0]:.6f}, {optimal_center[1]:.6f}), 缩放: {optimal_zoom}")
        
        # Build markers string for fire points
        markers = []
        
        # Add fire points with high precision coordinates
        for i, point in enumerate(fire_points):
            markers.append(f"color:red|label:F{i+1}|{point['lat']:.6f},{point['lng']:.6f}")
        
        # Add drone start point
        if drone_start_point:
            markers.append(f"color:blue|label:D|{drone_start_point['lat']:.6f},{drone_start_point['lng']:.6f}")
        
        # Construct Google Static Maps URL with optimal parameters
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        params = {
            "center": f"{optimal_center[0]:.6f},{optimal_center[1]:.6f}",
            "zoom": str(optimal_zoom),
            "size": "640x480",
            "maptype": "satellite",
            "key": GOOGLE_MAPS_API_KEY,
            "format": "png"
        }
        
        # Add markers to URL
        if markers:
            params["markers"] = "|".join(markers)
        
        # 显示API请求URL用于调试
        request_url = f"{base_url}?" + "&".join([f"{k}={v}" for k, v in params.items() if k != "key"])
        st.info(f"📸 API请求参数: {request_url}&key=***")
        
        # Make request to Google Static Maps API
        response = requests.get(base_url, params=params, timeout=15)
        
        if response.status_code == 200:
            # Check if response is actually an image
            content_type = response.headers.get('content-type', '')
            if content_type.startswith('image'):
                # Convert response to PIL Image
                image = Image.open(io.BytesIO(response.content))
                
                # Convert to base64 for Gemini
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                st.success(f"✅ 地图截图生成成功！中心点: ({optimal_center[0]:.4f}, {optimal_center[1]:.4f}), 缩放级别: {optimal_zoom}")
                
                # 保存图片和坐标数据（使用优化后的中心点）
                save_map_image(img_base64, fire_points, drone_start_point, optimal_center, optimal_zoom)
                save_coordinates_to_file(fire_points, drone_start_point, optimal_center)
                
                # 计算并显示像素坐标（使用优化后的参数）
                all_points = fire_points.copy()
                if drone_start_point:
                    all_points.append(drone_start_point)
                
                pixel_coords = convert_coordinates_to_pixels(all_points, optimal_center, optimal_zoom)
                
                if pixel_coords:
                    st.info("📍 动态计算的像素坐标:")
                    for i, coord in enumerate(pixel_coords):
                        if i < len(fire_points):
                            st.write(f"🔥 Fire Point {i+1}: 像素({coord['x']}, {coord['y']}) - 经纬度({coord['lat']:.6f}, {coord['lng']:.6f})")
                        else:
                            st.write(f"🚁 Drone Start: 像素({coord['x']}, {coord['y']}) - 经纬度({coord['lat']:.6f}, {coord['lng']:.6f})")
                
                return img_base64
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error_message', 'Unknown API error')
                    st.error(f"❌ Google Maps API Error: {error_msg}")
                except:
                    st.error(f"❌ Unexpected response format: {response.text[:200]}")
                return None
                
        elif response.status_code == 403:
            st.error("❌ 403 Forbidden - API Key Issue")
            st.error("可能的原因：")
            st.error("1. API密钥无效或已过期")
            st.error("2. Static Maps API未启用") 
            st.error("3. API密钥权限不足")
            st.error("4. 计费账户未设置或余额不足")
            return None
            
        elif response.status_code == 400:
            st.error(f"❌ 400 Bad Request - 参数错误")
            try:
                error_data = response.json()
                st.error(f"详细错误: {error_data}")
            except:
                st.error(f"响应内容: {response.text[:300]}")
            return None
        else:
            st.error(f"❌ HTTP Error {response.status_code}")
            st.error(f"响应内容: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ 请求超时 - 请检查网络连接")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ 连接错误 - 请检查网络连接")
        return None
    except Exception as e:
        st.error(f"❌ 生成截图时发生错误: {e}")
        import traceback
        st.error(traceback.format_exc())
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
                
                # 自动生成地图截图（如果有点数据）- 移除map_center参数
                map_screenshot = None
                if st.session_state.fire_points or st.session_state.drone_start_point:
                    try:
                        st.info("📸 正在生成地图截图...")
                        map_screenshot = generate_map_screenshot(
                            st.session_state.fire_points,
                            st.session_state.drone_start_point
                        )
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
    
    # 获取动态地图中心和缩放（与截图逻辑一致）
    map_center, zoom_level = calculate_optimal_map_view(
        st.session_state.fire_points, 
        st.session_state.drone_start_point
    )
    
    # 显示当前使用的地图参数
    if st.session_state.fire_points or st.session_state.drone_start_point:
        st.info(f"🗺️ 当前地图视图 - 中心: ({map_center[0]:.4f}, {map_center[1]:.4f}), 缩放: {zoom_level}")
    
    # Create folium map with dynamic center
    m = folium.Map(
        location=map_center,
        zoom_start=zoom_level,
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
        
        elif st.session_state.get('adding_drone_point', False):
            st.session_state.drone_start_point = {
                'lat': clicked_lat,
                'lng': clicked_lng
            }
            st.session_state.adding_drone_point = False
            st.success(f"Drone start point set at: {clicked_lat:.6f}, {clicked_lng:.6f}")

