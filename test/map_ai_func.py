import google.generativeai as genai
import io
import base64
from PIL import Image
import json

def generate_map_analysis(user_input, mission_data=None, uploaded_image=None):
    """
    使用Gemini API分析地图和任务数据
    """
    # 配置API
    genai.configure(api_key="AIzaSyD7okw014tpGtTevqPYe2-e1MgXhNSshMg")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 准备内容列表
    contents = []
    
    # 添加用户输入和任务数据
    prompt = f"User message: {user_input}\n\n"
    
    if mission_data:
        prompt += f"""Mission Data:{json.dumps(mission_data, indent=2)}

    Please analyze this fire mission scenario and provide recommendations for:
    1. Optimal flight path from start point to fire location
    2. Risk assessment and safety considerations
    3. Recommended equipment and approach strategy
    4. Weather and environmental factors to consider
    5. Emergency procedures and backup plans

    """
    
    contents.append(prompt)
    
    # 如果有上传的图片，添加到内容中
    if uploaded_image is not None:
        try:
            # 读取上传的图片
            image_bytes = uploaded_image.getvalue()
            image = Image.open(io.BytesIO(image_bytes))
            contents.append(image)
            contents.append("Please also analyze the uploaded map/image in the context of the fire mission.")
        except Exception as e:
            print(f"Error processing uploaded image: {e}")
    
    try:
        # 生成内容
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"
    
def generate_content_with_map_context(user_input, mission_data=None, uploaded_image=None):
    """
    兼容原有接口的函数
    """
    return generate_map_analysis(user_input, mission_data, uploaded_image)

def main():
    # 示例调用
    user_input = "What is the best approach for this fire mission?"
    mission_data = {
        "start_point": {"lat": 37.7749, "lng": -122.4194},
        "fire_point": {"lat": 37.7849, "lng": -122.4094},
        "timestamp": "2023-10-01T12:00:00Z"
    }
    
    # 假设上传的图片是一个BytesIO对象
    uploaded_image = None  # 替换为实际的BytesIO对象
    
    result = generate_map_analysis(user_input, mission_data, uploaded_image)
    print(result)
if __name__ == "__main__":
    main()