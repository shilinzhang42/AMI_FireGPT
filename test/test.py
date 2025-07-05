from google import genai
client = genai.Client(api_key="AIzaSyD7okw014tpGtTevqPYe2-e1MgXhNSshMg")
with open('test/test_image/2.png', 'rb') as f:
        image_bytes = f.read()

response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
                genai.types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/png',
                 ),
                'Caption this image.'
                 ]
         )

print(response.text)