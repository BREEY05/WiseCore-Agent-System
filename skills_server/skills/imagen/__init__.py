import mcp.types as types
import os
import subprocess
import sys

# 定位脚本路径
SKILL_DIR = os.path.dirname(__file__)
SCRIPT_PATH = os.path.join(SKILL_DIR, "scripts", "generate_image.py")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_image_with_imagen",
            description="使用 Google Imagen 模型生成图片。不需要额外依赖。",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "图片描述提示词"},
                    "output_path": {"type": "string", "description": "输出图片路径 (可选，默认在当前目录生成 timestamp 命名的文件)"},
                    "api_key": {"type": "string", "description": "Google Gemini API Key (可选，若环境变量 GEMINI_API_KEY 已设置)"},
                    "image_size": {"type": "string", "description": "图片尺寸: 512, 1K, 2K", "enum": ["512", "1K", "2K"], "default": "1K"}
                },
                "required": ["prompt"]
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "generate_image_with_imagen":
        prompt = arguments.get("prompt")
        output_path = arguments.get("output_path")
        api_key = arguments.get("api_key")
        image_size = arguments.get("image_size", "1K")

        # 构建命令
        cmd = [sys.executable, SCRIPT_PATH, prompt]
        if output_path:
            cmd.append(output_path)
        
        try:
            # 环境变量
            env = os.environ.copy()
            if api_key:
                env["GEMINI_API_KEY"] = api_key
            if image_size:
                env["IMAGE_SIZE"] = image_size

            # 运行脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                encoding='utf-8',
                cwd=os.getcwd(),
                timeout=120  # 增加超时限制，防止卡死
            )

            if result.returncode == 0:
                # 尝试从 stdout 中提取生成的图片路径
                # 假设脚本输出 "File: /path/to/image.png"
                import re
                match = re.search(r"File: (.+)", result.stdout)
                image_path = match.group(1).strip() if match else output_path or "generated-image.png"
                
                # 如果是在 Web 环境下，我们需要返回一个可以被前端访问的路径
                # 这里简单起见，我们返回绝对路径，并让前端尝试通过 file:// 或者后端提供文件服务
                # 更好的做法是将图片转为 base64 或者移动到 static 目录
                
                # 尝试将图片转换为 Base64 以便直接在前端显示
                try:
                    if os.path.exists(image_path):
                        import base64
                        with open(image_path, "rb") as img_file:
                            b64_data = base64.b64encode(img_file.read()).decode('utf-8')
                            return [
                                types.TextContent(type="text", text=f"图片生成成功！"),
                                types.ImageContent(type="image", data=b64_data, mimeType="image/png")
                            ]
                except Exception as e:
                    return [types.TextContent(type="text", text=f"图片已生成但无法读取: {image_path} ({e})")]

                return [types.TextContent(type="text", text=f"图片生成成功！路径: {image_path}")]
            else:
                return [types.TextContent(type="text", text=f"生成失败 (Exit Code {result.returncode}):\n{result.stderr}\n\nStdout:\n{result.stdout}")]

        except subprocess.TimeoutExpired:
            return [types.TextContent(type="text", text="图片生成超时 (超过120秒)。请稍后重试或简化提示词。")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"执行脚本出错: {str(e)}")]

    return []
