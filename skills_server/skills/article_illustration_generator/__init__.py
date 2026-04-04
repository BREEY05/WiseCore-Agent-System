import mcp.types as types
import os
import subprocess
import sys

# 定位脚本路径
SKILL_DIR = os.path.dirname(__file__)
SCRIPT_PATH = os.path.join(SKILL_DIR, "scripts", "article-Illustration-generator.py")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_article_illustrations",
            description="为文章生成插图并导出为精美的 HTML 页面。需要提供文章文本文件路径。使用 Gemini 模型生成图片。",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_file_path": {"type": "string", "description": "包含文章内容的文本文件绝对路径"},
                    "api_key": {"type": "string", "description": "Google Gemini API Key (可选，若环境变量 GOOGLE_API_KEY 已设置)"},
                    "num_images": {"type": "integer", "description": "生成图片数量 (默认 5)", "default": 5}
                },
                "required": ["article_file_path"]
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "generate_article_illustrations":
        article_path = arguments.get("article_file_path")
        api_key = arguments.get("api_key")
        num_images = arguments.get("num_images", 5)

        if not os.path.exists(article_path):
            return [types.TextContent(type="text", text=f"错误：文件不存在 {article_path}")]

        # 构建命令
        cmd = [sys.executable, SCRIPT_PATH, article_path]
        if api_key:
            cmd.append(api_key)
        
        cmd.extend(["--images", str(num_images)])

        # 确保输出目录存在 (脚本会在 CWD/output 生成，建议我们切换到 temp 目录或者让脚本输出到指定位置？)
        # 脚本硬编码了 output 目录在 os.getcwd()。
        # 我们可以在调用前切换 cwd，或者就让它生成在当前工作目录 (d:\anaconda\envs\agent\my_agent)
        
        try:
            # 运行脚本
            # 使用 subprocess.run 捕获输出
            env = os.environ.copy()
            if api_key:
                env["GOOGLE_API_KEY"] = api_key # 脚本也支持环境变量

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                encoding='utf-8',
                cwd=os.getcwd() # 在当前项目根目录生成 output
            )

            if result.returncode == 0:
                return [types.TextContent(type="text", text=f"任务完成！\n\n{result.stdout}")]
            else:
                return [types.TextContent(type="text", text=f"任务失败 (Exit Code {result.returncode}):\n{result.stderr}\n\nStdout:\n{result.stdout}")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"执行脚本出错: {str(e)}")]

    return []
