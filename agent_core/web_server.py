from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
import os
import sys
import httpx
from typing import List, Dict
from contextlib import asynccontextmanager, AsyncExitStack
from types import SimpleNamespace

# 导入本地模块
try:
    from .client import SERVERS_CONFIG, model, MemoryManager
except ImportError:
    from client import SERVERS_CONFIG, model, MemoryManager
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

class AgentBackend:
    def __init__(self):
        self.sessions = {}
        self.tool_to_session_map = {}
        self.all_tools_for_llm = []
        self.stack = AsyncExitStack()
        self.memory_manager = MemoryManager()
        self.system_message = SystemMessage(content="""你是一个强大的智能助手，可以调用本地工具来完成任务。

**重要规则：**
1. **全程中文**：你的所有思考过程、工具参数解释、以及最终回复都必须使用中文。
2. **思考先行**：在执行任何操作前，先输出思考过程。必须包裹在 `<thought>` 和 `</thought>` 标签中。
3. **最终回复**：在 `</thought>` 标签之后给出最终回答。
4. **只在需要时调用工具**：
   - **generate_image**：只有当用户明确要求生成图片、配图、插图时才调用
   - **麦当劳工具**：只有当用户询问麦当劳相关内容（如订餐、地址、菜单）时才调用
   - **GitHub工具**：只有当用户需要GitHub相关操作（如查看仓库、提交代码）时才调用
   - 普通聊天、问答、不涉及上述场景时，直接回答，不要调用任何工具
5. **关于麦当劳MCP**：麦当劳MCP只是一个服务，你不是麦当劳助手，只是在用户询问麦当劳相关问题时可以调用这个服务的工具。
""")

    async def initialize(self):
        print("🔌 正在连接 MCP Servers...")
        await self.stack.__aenter__()
        for server_name, config in SERVERS_CONFIG.items():
            try:
                print(f"  Attempting to connect to {server_name} (Type: {config.get('type', 'stdio')})...")
                
                session = None
                mcp_tools = None

                if config.get("type") == "sse":
                    # 特殊处理麦当劳的 streamablehttp (暂用 HTTP POST 模拟)
                    if "mcd.cn" in config["url"]:
                        print(f"  🍟 发现麦当劳 MCP，正在使用兼容模式连接...")
                        
                        async def mcd_call(name, args):
                            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                                payload = {
                                    "jsonrpc": "2.0",
                                    "method": "tools/call",
                                    "params": {"name": name, "arguments": args},
                                    "id": 1
                                }
                                r = await client.post(config["url"], headers=config["headers"], json=payload)
                                if r.status_code == 200:
                                    res_json = r.json()
                                    if "result" in res_json:
                                        content_data = res_json["result"].get("content", [])
                                        return SimpleNamespace(content=[SimpleNamespace(text=c.get("text", str(c))) for c in content_data])
                                raise Exception(f"麦当劳工具调用失败: {r.text}")

                        async def mcd_list():
                            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                                r = await client.post(config["url"], headers=config["headers"], json={
                                    "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1
                                })
                                if r.status_code == 200:
                                    tools_raw = r.json().get("result", {}).get("tools", [])
                                    return SimpleNamespace(tools=[
                                        SimpleNamespace(
                                            name=t["name"], 
                                            description=t.get("description", ""), 
                                            inputSchema=t.get("inputSchema", {"type": "object", "properties": {}})
                                        ) for t in tools_raw
                                    ])
                                raise Exception(f"获取麦当劳工具列表失败: {r.status_code}")

                        mcp_tools = await mcd_list()
                        session = SimpleNamespace(
                            call_tool=mcd_call,
                            list_tools=lambda: mcp_tools,
                            initialize=lambda: asyncio.sleep(0)
                        )
                    else:
                        # 标准 SSE
                        read, write = await self.stack.enter_async_context(sse_client(url=config["url"], headers=config.get("headers")))
                        session = await self.stack.enter_async_context(ClientSession(read, write))
                        await session.initialize()
                        mcp_tools = await session.list_tools()
                else:
                    # 默认 stdio
                    server_params = StdioServerParameters(
                        command=config["command"],
                        args=config["args"],
                        env=config.get("env", os.environ.copy())
                    )
                    read, write = await self.stack.enter_async_context(stdio_client(server_params))
                    session = await self.stack.enter_async_context(ClientSession(read, write))
                    await session.initialize()
                    mcp_tools = await session.list_tools()

                if session and mcp_tools:
                    self.sessions[server_name] = session
                    for t in mcp_tools.tools:
                        self.tool_to_session_map[t.name] = server_name
                        self.all_tools_for_llm.append({
                            "type": "function",
                            "function": {
                                "name": t.name,
                                "description": t.description,
                                "parameters": t.inputSchema
                            }
                        })
                    print(f" ✅ {server_name} 已成功连接，加载了 {len(mcp_tools.tools)} 个工具")
            except Exception as e:
                import traceback
                print(f" ❌ {server_name} 失败: {str(e)}")
                print(f" 🔍 详细堆栈: {traceback.format_exc()}")
        
        if self.all_tools_for_llm:
            self.llm_with_tools = model.bind_tools(self.all_tools_for_llm)
        else:
            self.llm_with_tools = model

    async def cleanup(self):
        print("🛑 正在关闭 MCP 会话...")
        await self.stack.__aexit__(None, None, None)

    async def chat_stream(self, user_input: str, websocket: WebSocket):
        try:
            history = self.memory_manager.load_memory()
            chat_history = [self.system_message] + history
            chat_history.append(HumanMessage(content=user_input))
            
            while True:
                full_response_content = ""
                current_ai_msg = None
                
                # 流式输出
                async for chunk in self.llm_with_tools.astream(chat_history):
                    if chunk.content:
                        full_response_content += chunk.content
                        await websocket.send_json({"type": "content", "data": chunk.content})
                    if not current_ai_msg:
                        current_ai_msg = chunk
                    else:
                        current_ai_msg += chunk
                
                chat_history.append(current_ai_msg)
                
                # 如果没有工具调用，结束
                if not current_ai_msg.tool_calls:
                    break
                
                # 处理工具调用
                await websocket.send_json({"type": "status", "data": "正在调用工具..."})
                for tool_call in current_ai_msg.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']
                    
                    await websocket.send_json({"type": "tool_call", "name": tool_name, "args": tool_args})
                    
                    session_name = self.tool_to_session_map.get(tool_name)
                    if not session_name:
                        res = f"Error: Tool {tool_name} not found"
                    else:
                        try:
                            result = await self.sessions[session_name].call_tool(tool_name, tool_args)
                            res = ""
                            # 处理 TextContent 和 ImageContent
                            for c in result.content:
                                # 兼容不同类型的content对象
                                if hasattr(c, 'type'):
                                    if c.type == "text":
                                        res += c.text if hasattr(c, 'text') else str(c)
                                    elif c.type == "image":
                                        await websocket.send_json({
                                            "type": "image", 
                                            "data": c.data if hasattr(c, 'data') else "", 
                                            "mimeType": c.mimeType if hasattr(c, 'mimeType') else "image/png"
                                        })
                                        res += "\n[图片已生成并发送]"
                                else:
                                    # 处理没有type属性的情况（如SimpleNamespace）
                                    if hasattr(c, 'text'):
                                        res += c.text
                                    else:
                                        res += str(c)
                        except Exception as e:
                            res = f"Error: {str(e)}"
                    
                    await websocket.send_json({"type": "tool_result", "data": res[:500] + "..." if len(res)>500 else res})
                    chat_history.append(ToolMessage(content=res, tool_call_id=tool_id))
            
            self.memory_manager.save_memory(chat_history)
        except Exception as e:
            print(f"❌ chat_stream 出错: {e}")
            await websocket.send_json({"type": "error", "data": str(e)})

agent_backend = AgentBackend()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    local_ollama_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ollama"))
    os.environ["OLLAMA_MODELS"] = local_ollama_path
    await agent_backend.initialize()
    yield
    # 停止时
    await agent_backend.cleanup()

app = FastAPI(lifespan=lifespan)

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

@app.get("/")
async def get_index():
    try:
        with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(content=f"Error loading index.html: {e}", status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"🔌 WebSocket 连接已开启: {websocket.client}")
    
    # 发送初始化数据
    try:
        mcp_servers = []
        for name in SERVERS_CONFIG.keys():
            status = "已连接" if name in agent_backend.sessions else "未连接"
            mcp_servers.append({"name": name, "status": status})

        skills_list = []
        for name, server in agent_backend.tool_to_session_map.items():
            for t in agent_backend.all_tools_for_llm:
                if t["function"]["name"] == name:
                    skills_list.append({
                        "name": name,
                        "description": t["function"]["description"],
                        "server": server
                    })
                    break
        
        await websocket.send_json({
            "type": "init_data", 
            "mcp_servers": mcp_servers,
            "skills": skills_list
        })
    except Exception as e:
        print(f"⚠️ 发送初始化数据失败: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            user_msg = json.loads(data)
            print(f"📩 收到消息: {user_msg}")
            
            if user_msg.get("content") == "/clear":
                agent_backend.memory_manager.clear_memory()
                await websocket.send_json({"type": "status", "data": "记忆已清除"})
            else:
                await websocket.send_json({"type": "start_typing"})
                await agent_backend.chat_stream(user_msg["content"], websocket)
            
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        print("🔌 WebSocket 连接已断开")
    except Exception as e:
        print(f"❌ WebSocket 发生错误: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
