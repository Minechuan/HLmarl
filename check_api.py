from openai import OpenAI

BASE_URL = "https://api.jisuai.top/v1"
API_KEY = "sk-ELIhvy3qDRcSwGaxCReISEQEuLxaR1sVlQe3e5FrH9Cxgpla"   # 替换为你的真实 key
MODEL = "gemini-3-pro-preview"    # 先用一个平台最常见、成功率最高的模型测试

client = OpenAI(
    api_key=API_KEY,
    base_url=f"{BASE_URL}",
)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
)

print(response.choices[0].message.content)