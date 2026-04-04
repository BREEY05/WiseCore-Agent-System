import mcp.types as types
import os
import subprocess
import sys
import json

SKILL_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
OOXML_SCRIPTS_DIR = os.path.join(SKILL_DIR, "ooxml", "scripts")

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="pptx_extract_text",
            description="从 PowerPoint 文件中提取所有文本内容，返回结构化的 JSON 数据（包括位置和格式）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {"type": "string", "description": "PPTX 文件的绝对路径"},
                    "output_json": {"type": "string", "description": "输出 JSON 的绝对路径"}
                },
                "required": ["pptx_path", "output_json"]
            },
        ),
        types.Tool(
            name="pptx_unpack",
            description="将 PPTX 文件解压为原始 XML 结构，用于深入分析布局、主题或备注。",
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {"type": "string", "description": "PPTX 文件的绝对路径"},
                    "output_dir": {"type": "string", "description": "解压目录的绝对路径"}
                },
                "required": ["pptx_path", "output_dir"]
            },
        ),
        types.Tool(
            name="pptx_rearrange",
            description="对 PPTX 中的幻灯片进行重新排序、删除或合并。",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_pptx": {"type": "string", "description": "输入文件路径"},
                    "output_pptx": {"type": "string", "description": "输出文件路径"},
                    "commands": {"type": "string", "description": "排序命令，例如 '1,3,2' 表示取第1,3,2张幻灯片"}
                },
                "required": ["input_pptx", "output_pptx", "commands"]
            },
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if not arguments:
        arguments = {}

    def run_python_script(script_path, args):
        cmd = [sys.executable, script_path] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=SKILL_DIR,
                capture_output=True,
                text=True,
                encoding='utf-8',
                check=False
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            return output
        except Exception as e:
            return f"Execution failed: {str(e)}"

    if name == "pptx_extract_text":
        pptx_path = arguments.get("pptx_path")
        output_json = arguments.get("output_json")
        script = os.path.join(SCRIPTS_DIR, "inventory.py")
        output = run_python_script(script, [pptx_path, output_json])
        return [types.TextContent(type="text", text=output)]

    elif name == "pptx_unpack":
        pptx_path = arguments.get("pptx_path")
        output_dir = arguments.get("output_dir")
        script = os.path.join(OOXML_SCRIPTS_DIR, "unpack.py")
        output = run_python_script(script, [pptx_path, output_dir])
        return [types.TextContent(type="text", text=output)]

    elif name == "pptx_rearrange":
        input_pptx = arguments.get("input_pptx")
        output_pptx = arguments.get("output_pptx")
        commands = arguments.get("commands")
        script = os.path.join(SCRIPTS_DIR, "rearrange.py")
        output = run_python_script(script, [input_pptx, output_pptx, "--slides", commands])
        return [types.TextContent(type="text", text=output)]

    return []
