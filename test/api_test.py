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

# Google Maps API Key - 建议使用环境变量或Streamlit secrets
GOOGLE_MAPS_API_KEY = "AIzaSyDK7bsI0iO4u_4uYghuSAloEhrFPEeQyoY"

def test_google_maps_api():
    """测试Google Maps API密钥是否有效"""
    try:
        # 测试Geocoding API
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        result = gmaps.geocode("Munich, Germany")
        
        if result:
            st.success("✅ Google Maps API key is valid and working")
            return True
        else:
            st.error("❌ Google Maps API key is invalid or has no permissions")
            return False
            
    except googlemaps.exceptions.ApiError as e:
        st.error(f"❌ Google Maps API Error: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Error testing API key: {e}")
        return False

def test_static_maps_api():
    """测试Static Maps API是否可用"""
    try:
        test_url = "https://maps.googleapis.com/maps/api/staticmap"
        params = {
            "center": "48.1351,11.5820",  # Munich
            "zoom": 10,
            "size": "400x400",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if content_type.startswith('image'):
                st.success("✅ Static Maps API is working")
                # 显示测试图片
                st.image(response.content, caption="Test Static Map", width=300)
                return True
            else:
                try:
                    error_data = response.json()
                    st.error(f"❌ Static Maps API Error: {error_data}")
                except:
                    st.error(f"❌ Static Maps API returned non-image content: {response.text[:200]}")
                return False
        elif response.status_code == 403:
            st.error("❌ Static Maps API: 403 Forbidden - Check API key permissions and billing")
            st.info("确保以下设置正确：")
            st.info("1. Static Maps API 已启用")
            st.info("2. API密钥有正确的权限")
            st.info("3. 计费账户已设置")
            return False
        else:
            st.error(f"❌ Static Maps API Error: HTTP {response.status_code}")
            try:
                error_response = response.json()
                st.json(error_response)
            except:
                st.text(response.text[:300])
            return False
            
    except Exception as e:
        st.error(f"❌ Error testing Static Maps API: {e}")
        return False

# 在侧边栏添加API测试功能
with st.sidebar:
    st.subheader("🔧 API Status Check")
    
    if st.button("Test Google Maps API"):
        test_google_maps_api()
    
    if st.button("Test Static Maps API"):
        test_static_maps_api()
    
    # API密钥配置说明
    with st.expander("📋 API Setup Instructions"):
        # 修复字符串格式化问题
        api_key_preview = GOOGLE_MAPS_API_KEY[:10] + "..." if len(GOOGLE_MAPS_API_KEY) > 10 else GOOGLE_MAPS_API_KEY
        
        st.markdown("""
        **Google Cloud Console 设置步骤：**
        
        1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
        2. 创建新项目或选择现有项目
        3. 启用以下API：
           - Maps JavaScript API
           - Geocoding API
           - Static Maps API
        4. 创建API密钥：
           - 导航到 "APIs & Services" > "Credentials"
           - 点击 "Create Credentials" > "API Key"
        5. 设置API密钥限制（可选但推荐）
        6. 确保计费账户已设置
        """)
        
        st.markdown("**当前API密钥状态：**")
        st.code(f"Key: {api_key_preview}")

def generate_map_screenshot(map_center, fire_points, drone_start_point):
    """
    Generate a map screenshot using Google Static Maps API with enhanced error handling
    """
    try:
        # 首先检查API密钥
        if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_API_KEY_HERE":
            st.error("❌ Google Maps API key not configured")
            return None
        
        # Build markers string for fire points
        markers = []
        
        # Add fire points with improved formatting
        for i, point in enumerate(fire_points):
            markers.append(f"color:red|label:F{i+1}|{point['lat']:.6f},{point['lng']:.6f}")
        
        # Add drone start point
        if drone_start_point:
            markers.append(f"color:blue|label:D|{drone_start_point['lat']:.6f},{drone_start_point['lng']:.6f}")
        
        # Construct Google Static Maps URL
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        params = {
            "center": f"{map_center[0]:.6f},{map_center[1]:.6f}",
            "zoom": "12",
            "size": "640x480",
            "maptype": "satellite",
            "key": GOOGLE_MAPS_API_KEY,
            "format": "png"
        }
        
        # Add markers to URL
        if markers:
            params["markers"] = "|".join(markers)
        
        # Display the URL for debugging
        st.info("Testing Static Maps URL...")
        
        # Make request with timeout
        response = requests.get(base_url, params=params, timeout=15)
        
        if response.status_code == 200:
            # Check if response is actually an image
            content_type = response.headers.get('content-type', '')
            if content_type.startswith('image'):
                # Convert response to PIL Image
                image = Image.open(io.BytesIO(response.content))
                
                # Display the image for verification
                st.image(image, caption="Generated Map Screenshot", width=400)
                
                # Convert to base64 for Gemini
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                st.success("📸 Map screenshot generated successfully")
                
                return img_base64
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error_message', 'Unknown API error')
                    st.error(f"❌ Google Maps API Error: {error_msg}")
                    st.json(error_data)
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
            st.error("5. API配额已用完")
            
            # 显示详细的错误信息
            try:
                error_data = response.json()
                st.error("详细错误信息：")
                st.json(error_data)
            except:
                st.text(response.text[:300])
            return None
            
        elif response.status_code == 400:
            st.error(f"❌ 400 Bad Request - 检查参数格式")
            st.info(f"Request URL: {response.url}")
            try:
                error_data = response.json()
                st.json(error_data)
            except:
                st.text(response.text[:300])
            return None
        else:
            st.error(f"❌ HTTP Error {response.status_code}")
            st.info(f"Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout - 请检查网络连接")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error - 请检查网络连接")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return None

# 初始化Google Maps客户端（带错误处理）
try:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    # 测试API密钥是否有效
    test_result = gmaps.geocode("Munich, Germany")
    if not test_result:
        st.warning("⚠️ Google Maps API may not be working properly")
    else:
        st.success("🟢 Google Maps client initialized successfully")
except Exception as e:
    st.error(f"❌ Error initializing Google Maps client: {e}")
    gmaps = None

# 添加一个简单的测试界面
st.subheader("🧪 Quick API Test")

col1, col2 = st.columns(2)

with col1:
    if st.button("🗺️ Test Geocoding"):
        if gmaps:
            try:
                result = gmaps.geocode("Technical University of Munich")
                if result:
                    location = result[0]['geometry']['location']
                    st.success(f"Found TUM at: {location['lat']:.6f}, {location['lng']:.6f}")
                    st.json(result[0])
                else:
                    st.error("No results found")
            except Exception as e:
                st.error(f"Geocoding error: {e}")
        else:
            st.error("Google Maps client not initialized")

with col2:
    if st.button("📸 Test Screenshot"):
        # Test with TUM coordinates
        test_center = [48.1351, 11.5820]
        test_fire_points = [
            {'lat': 48.140, 'lng': 11.580},
            {'lat': 48.130, 'lng': 11.590}
        ]
        test_drone_point = {'lat': 48.135, 'lng': 11.570}
        
        screenshot = generate_map_screenshot(test_center, test_fire_points, test_drone_point)
        if screenshot:
            st.balloons()

# 地图和路径规划功能
st.subheader("🚀 Route Planning")

# 显示当前的fire_points和drone_start_point
st.write("当前火点：", st.session_state.get("fire_points", []))
st.write("无人机起始点：", st.session_state.get("drone_start_point", None))

# 地图显示
map_center = st.session_state.get("map_center", [48.1351, 11.5820])
m = folium.Map(location=map_center, zoom_start=12, control_scale=True, tiles="OpenStreetMap")

# 添加火点标记
if st.session_state.get("fire_points"):
    for i, point in enumerate(st.session_state.fire_points):
        folium.Marker(
            location=[point["lat"], point["lng"]],
            popup=f"火点 {i+1}",
            icon=folium.Icon(color="red", icon="fire"),
        ).add_to(m)

# 添加无人机起始点标记
if st.session_state.get("drone_start_point"):
    drone_point = st.session_state.drone_start_point
    folium.Marker(
        location=[drone_point["lat"], drone_point["lng"]],
        popup="无人机起始点",
        icon=folium.Icon(color="blue", icon="plane"),
    ).add_to(m)

# 显示地图
st_data = st_folium(m, width=700, height=500)

# 路径规划逻辑
if st.button("🛤️ 规划最佳路径"):
    if not st.session_state.get("fire_points") or not st.session_state.get("drone_start_point"):
        st.warning("请确保已添加火点和无人机起始点")
    else:
        # TODO: 添加路径规划算法
        st.success("路径规划功能尚未实现")