# test.py

import google.generativeai as genai
import base64
import io
from PIL import Image

def generate_content(user_input, uploaded_image=None, map_context=None, map_screenshot=None):
    """
    生成基于用户输入、图像、地图上下文和地图截图的响应
    
    Args:
        user_input: 用户输入的文本
        uploaded_image: 上传的图像文件
        map_context: 包含火点和无人机起始点的地图数据
        map_screenshot: 地图截图的base64编码
    """
    try:
        # 配置Gemini API
        genai.configure(api_key="AIzaSyD7okw014tpGtTevqPYe2-e1MgXhNSshMg")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 构建prompt
        prompt = f"""
        You are a forest firefighting planning assistant. Analyze the following information and provide a detailed firefighting strategy:

        User Input: {user_input}
        
        Map Information:
        """
        
        if map_context:
            if map_context.get('fire_points'):
                prompt += f"- Fire points: {len(map_context['fire_points'])} locations\n"
                for i, point in enumerate(map_context['fire_points']):
                    prompt += f"  Fire {i+1}: Latitude {point['lat']:.6f}, Longitude {point['lng']:.6f}\n"
            
            if map_context.get('drone_start_point'):
                point = map_context['drone_start_point']
                prompt += f"- Drone start point: Latitude {point['lat']:.6f}, Longitude {point['lng']:.6f}\n"
        
        # 准备输入内容
        content_parts = [prompt]
        
        # 添加上传的图像
        if uploaded_image:
            uploaded_image.seek(0)
            image_data = uploaded_image.read()
            image = Image.open(io.BytesIO(image_data))
            content_parts.append(image)
            content_parts.append("This is an uploaded map image for reference.")
        
        # 添加地图截图
        if map_screenshot:
            # 将base64解码为图像
            screenshot_data = base64.b64decode(map_screenshot)
            screenshot_image = Image.open(io.BytesIO(screenshot_data))
            content_parts.append(screenshot_image)
            content_parts.append("This is the current map view showing fire points and drone start position.")
        
        # 生成响应
        response = model.generate_content(content_parts)
        return response.text
        
    except Exception as e:
        return f"Error generating content: {str(e)}"
