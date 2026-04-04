import mcp.types as types
import os

SKILL_DIR = os.path.dirname(__file__)
SKILL_FILE = os.path.join(SKILL_DIR, "SKILL.md")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="consult_docx_guide",
            description="获取处理复杂 DOCX 文档（如编辑、修订、批注、XML操作）的详细指南和工作流。当你需要对 DOCX 进行高级操作（不仅仅是读取文本）时使用此工具。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "consult_docx_guide":
        try:
            with open(SKILL_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"无法读取 DOCX 指南: {str(e)}")]
    
    return []
