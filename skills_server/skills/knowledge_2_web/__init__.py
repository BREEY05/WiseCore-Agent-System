import mcp.types as types
import os
import subprocess
import sys
import json

# 定位脚本路径
SKILL_DIR = os.path.dirname(__file__)
SCRIPT_PATH = os.path.join(SKILL_DIR, "scripts", "knowledge-to-web.py")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_knowledge_web_page",
            description="将知识文章内容（JSON格式）转换为精美的交互式网页，自动生成配图。需要提供JSON文件路径。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_json_path": {"type": "string", "description": "包含文章内容的JSON文件绝对路径"},
                    "api_key": {"type": "string", "description": "Google Gemini API Key (可选，若环境变量 GOOGLE_API_KEY 已设置)"},
                    "style": {"type": "string", "description": "插图风格: historical, scientific, cultural, nature", "enum": ["historical", "scientific", "cultural", "nature"], "default": "historical"}
                },
                "required": ["content_json_path"]
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "generate_knowledge_web_page":
        json_path = arguments.get("content_json_path")
        api_key = arguments.get("api_key")
        style = arguments.get("style", "historical")

        if not os.path.exists(json_path):
            return [types.TextContent(type="text", text=f"错误：文件不存在 {json_path}")]

        # 构建命令
        cmd = [sys.executable, SCRIPT_PATH, json_path]
        if api_key:
            cmd.append(api_key)
        
        cmd.extend(["--style", style])

        try:
            # 运行脚本
            env = os.environ.copy()
            if api_key:
                env["GOOGLE_API_KEY"] = api_key

            # 切换到 CWD 运行，因为脚本会在 os.getcwd()/output 生成文件
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                encoding='utf-8',
                cwd=os.getcwd()
            )

            if result.returncode == 0:
                return [types.TextContent(type="text", text=f"任务完成！\n\n{result.stdout}")]
            else:
                return [types.TextContent(type="text", text=f"任务失败 (Exit Code {result.returncode}):\n{result.stderr}\n\nStdout:\n{result.stdout}")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"执行脚本出错: {str(e)}")]

    return []
