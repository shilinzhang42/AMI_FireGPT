# planner.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_plan(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "你是森林火灾应急规划专家，生成多无人机灭火计划"},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
