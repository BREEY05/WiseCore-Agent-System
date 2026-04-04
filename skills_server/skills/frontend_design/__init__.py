import mcp.types as types
import os

SKILL_DIR = os.path.dirname(__file__)
SKILL_FILE = os.path.join(SKILL_DIR, "SKILL.md")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="consult_frontend_design_guidelines",
            description="获取高质量前端界面设计的指导原则和审美建议。当你需要设计网页、组件或应用UI时，使用此工具获取设计灵感和规范。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "consult_frontend_design_guidelines":
        try:
            with open(SKILL_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"无法读取设计指南: {str(e)}")]
    
    return []
