import requests
import json
import sys
import os
import urllib.parse
from datetime import datetime

BYTEDANCE_API_KEY = "35e01833-c9da-41f0-bb82-7432f18c1987"
API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SKILL_DIR)
AGENT_SKILL_DIR = os.path.dirname(SKILLS_DIR)
MY_AGENT_DIR = os.path.dirname(AGENT_SKILL_DIR)
OUTPUT_DIR = os.path.join(MY_AGENT_DIR, "data", "images")

def generate_image(prompt: str, model: str = "doubao-seedream-5-0-260128", 
                   size: str = "2K", watermark: bool = True) -> dict:
    """
    使用字节跳动Seedream API生成图片
    
    Args:
        prompt: 图片描述文本
        model: 模型名称
        size: 图片尺寸 (1K, 2K, 4K)
        watermark: 是否添加水印
    
    Returns:
        包含图片路径的字典
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BYTEDANCE_API_KEY}"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": watermark
    }
    
    print(f"正在生成图片...")
    print(f"提示词: {prompt}")
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("data") and len(result["data"]) > 0:
            image_url = result["data"][0].get("url")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"
            
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
                print(f"生成成功! 图片保存到: {filepath}")
                return {"url": image_url, "filepath": filepath, "status": "success"}
            else:
                return {"url": image_url, "status": "error", "message": "Failed to download image"}
        else:
            print(f"生成失败: {result}")
            return {"status": "error", "message": "No image data returned"}
    else:
        error_msg = f"API调用失败，状态码: {response.status_code}"
        print(f"{error_msg}")
        print(f"错误信息: {response.text}")
        return {"status": "error", "message": response.text}


def main():
    if len(sys.argv) < 2:
        prompt = input("请输入图片描述: ")
    else:
        prompt = " ".join(sys.argv[1:])
    
    if not prompt.strip():
        print("错误: 图片描述不能为空")
        sys.exit(1)
    
    result = generate_image(prompt)
    
    if result.get("status") == "success":
        print(f"\n图片文件路径: {result['filepath']}")
        print(f"在线URL: {result['url']}")
    else:
        print(f"\n生成失败: {result.get('message')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
