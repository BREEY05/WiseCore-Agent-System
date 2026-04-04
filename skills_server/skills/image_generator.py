import requests
import os
import sys
import json
from datetime import datetime
from typing import Any, List
import mcp.types as types

BYTEDANCE_API_KEY = "35e01833-c9da-41f0-bb82-7432f18c1987"
API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SKILL_DIR)
AGENT_SKILL_DIR = os.path.dirname(SKILLS_DIR)
MY_AGENT_DIR = os.path.dirname(AGENT_SKILL_DIR)
OUTPUT_DIR = os.path.join(MY_AGENT_DIR, "data", "images")

def get_tools():
    """返回可用的工具列表"""
    return [
        types.Tool(
            name="generate_image",
            description="使用字节跳动Seedream API生成图片。当用户需要生成图片、配图、插图时调用此工具。",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图片描述文本，描述你想要生成的图片内容"
                    },
                    "size": {
                        "type": "string",
                        "description": "图片尺寸，可选值: 1K, 2K, 4K，默认: 2K",
                        "default": "2K"
                    },
                    "watermark": {
                        "type": "boolean",
                        "description": "是否添加水印，默认: true",
                        "default": True
                    }
                },
                "required": ["prompt"]
            }
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """处理工具调用"""
    if name == "generate_image":
        return await generate_image_handler(arguments)
    raise ValueError(f"Unknown tool: {name}")

async def generate_image_handler(arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """生成图片的处理函数"""
    if not arguments:
        arguments = {}
    
    prompt = arguments.get("prompt", "")
    size = arguments.get("size", "2K")
    watermark = arguments.get("watermark", True)
    
    if not prompt:
        return [types.TextContent(type="text", text="错误: 请提供图片描述(prompt)")]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BYTEDANCE_API_KEY}"
    }
    
    data = {
        "model": "doubao-seedream-5-0-260128",
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "b64_json",
        "size": size,
        "stream": False,
        "watermark": watermark
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data") and len(result["data"]) > 0:
                image_b64 = result["data"][0].get("b64_json")
                
                if image_b64:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"image_{timestamp}.jpg"
                    
                    os.makedirs(OUTPUT_DIR, exist_ok=True)
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    
                    import base64
                    img_data = base64.b64decode(image_b64)
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    
                    # 先返回文本信息，再返回图片数据
                    content = []
                    content.append(types.TextContent(type="text", text=f"图片生成成功！\n保存路径: {filepath}\n访问链接: /data/images/{filename}"))
                    content.append(types.ImageContent(type="image", data=image_b64, mimeType="image/jpeg"))
                    return content
                else:
                    return [types.TextContent(type="text", text=f"生成失败: 未获取到图片数据")]
            else:
                return [types.TextContent(type="text", text=f"生成失败: {result}")]
        else:
            return [types.TextContent(type="text", text=f"API调用失败: {response.status_code} - {response.text}")]
            
    except Exception as e:
        return [types.TextContent(type="text", text=f"生成图片时出错: {str(e)}")]
