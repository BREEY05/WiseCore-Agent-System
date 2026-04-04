import mcp.types as types
import os

SKILL_DIR = os.path.dirname(__file__)
SKILL_FILE = os.path.join(SKILL_DIR, "SKILL.md")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="consult_manimgl_guide",
            description="获取 ManimGL (3b1b版) 的最佳实践指南概览。了解核心概念、动画类型和交互式开发流程。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="read_manimgl_resource",
            description="读取 ManimGL 的具体规则文件或示例代码。可以读取 rules/ 下的 markdown 文件或 examples/ 下的 python 代码。",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_path": {"type": "string", "description": "资源相对路径，例如 'rules/scenes.md' 或 'examples/basic_animations.py'"}
                },
                "required": ["resource_path"]
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "consult_manimgl_guide":
        try:
            with open(SKILL_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"无法读取 ManimGL 指南: {str(e)}")]
    
    elif name == "read_manimgl_resource":
        path = arguments.get("resource_path")
        # 安全检查：防止路径遍历
        if ".." in path or path.startswith("/") or ":" in path:
             return [types.TextContent(type="text", text="错误：非法路径，只能读取 rules/ 或 examples/ 下的文件")]
        
        full_path = os.path.join(SKILL_DIR, path)
        if not os.path.exists(full_path):
             return [types.TextContent(type="text", text=f"错误：文件不存在 {path}")]
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"读取文件失败: {str(e)}")]

    return []
