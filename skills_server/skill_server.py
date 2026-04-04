import asyncio
import importlib
import pkgutil
import os
import sys
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 动态加载 skills 目录下的所有模块
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
sys.path.append(os.path.dirname(__file__)) # 确保能导入 skills

# 注册所有 Skill 模块
skill_modules = []
if os.path.exists(SKILLS_DIR):
    for _, name, _ in pkgutil.iter_modules([SKILLS_DIR]):
        try:
            module = importlib.import_module(f"skills.{name}")
            if hasattr(module, "get_tools") and hasattr(module, "handle_call"):
                skill_modules.append(module)
                print(f"Loaded skill module: {name}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to load skill {name}: {e}", file=sys.stderr)

# 1. 创建 Server 实例
server = Server("my-custom-mcp-server")

# 2. 动态注册工具
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    all_tools = []
    for module in skill_modules:
        all_tools.extend(module.get_tools())
    return all_tools

# 3. 动态分发调用
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    
    for module in skill_modules:
        # 这里简单遍历，更好的做法是建立 map 映射
        tools = module.get_tools()
        tool_names = [t.name for t in tools]
        if name in tool_names:
            return await module.handle_call(name, arguments)
            
    raise ValueError(f"Unknown tool: {name}")

# 4. 启动服务
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-custom-mcp-server",
                server_version="0.2.0", # Version bumped
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
