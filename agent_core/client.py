import asyncio
import sys
import os
import json
import io

# 强制设置标准输入输出为 UTF-8 (解决 Windows 控制台中文乱码及输入问题)
if sys.platform.startswith('win'):
    # 对于 Windows，直接重置 stdin/stdout 的编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # 注意：重置 stdin 可能会影响交互式输入，但在某些终端下是必须的
    # 如果遇到 EOFError，可以尝试移除下面这行
    try:
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    except Exception:
        pass

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
try:
    from memory import MemoryManager
except ImportError:
    # 如果作为模块运行，尝试相对导入
    try:
        from .memory import MemoryManager
    except ImportError:
        # Fallback provided for direct execution
        import sys
        sys.path.append(os.path.dirname(__file__))
        from memory import MemoryManager

# 定义多个 MCP Server 配置
SERVERS_CONFIG = {
    "local_skills": {
        "type": "stdio",
        "command": sys.executable if sys.executable else "python",
        "args": [os.path.join(os.path.dirname(__file__), "..", "skills_server", "skill_server.py")],
        "env": os.environ.copy()
    },
    # GitHub MCP
    "github": {
        "type": "stdio",
        "command": "npx.cmd",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": "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"} 
    },
    # McDonald's MCP (Remote SSE)
    "mcd-mcp": {
        "type": "sse",
        "url": "https://mcp.mcd.cn",
        "headers": {
            "Authorization": "Bearer 2hez4lKA1OCBpMnFf7YaP8qVg5aR0ubY"
        }
    }
}

# 初始化 Ollama 模型
# 确保您已经运行 `ollama pull qwen3:4b` 或其他模型
model = ChatOllama(
    model="qwen3:4b", 
    base_url="http://localhost:11434",
    temperature=0,
    num_ctx=8192 # 增加上下文窗口以容纳大量工具定义
)

async def run_agent():
    print("\n🚀 === MCP Agent (Ollama + Local Skills) 启动中... ===")
    
    async with AsyncExitStack() as stack:
        sessions = {}
        tool_to_session_map = {}
        all_tools_for_llm = []
        
        # 1. 连接所有配置的 MCP Server
        print("🔌 正在连接 MCP Servers...")
        for server_name, config in SERVERS_CONFIG.items():
            try:
                print(f"  Attempting to connect to {server_name}...", end="", flush=True)
                
                if config.get("type") == "sse":
                    # SSE 远程连接
                    read, write = await stack.enter_async_context(sse_client(
                        url=config["url"],
                        headers=config.get("headers")
                    ))
                else:
                    # 默认 stdio 本地连接
                    server_params = StdioServerParameters(
                        command=config["command"],
                        args=config["args"],
                        env=config.get("env", os.environ.copy())
                    )
                    read, write = await stack.enter_async_context(stdio_client(server_params))
                
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                sessions[server_name] = session
                
                # 获取并注册工具
                mcp_tools = await session.list_tools()
                print(f" ✅ 成功! 加载了 {len(mcp_tools.tools)} 个工具")
                
                for t in mcp_tools.tools:
                    # 记录工具所属的 Session
                    tool_to_session_map[t.name] = server_name
                    
                    # 转换为 LangChain 格式
                    all_tools_for_llm.append({
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        }
                    })
            except Exception as e:
                print(f" ❌ 失败: {e}")

        if not all_tools_for_llm:
            print("⚠️  警告: 未能加载任何工具。Agent 将仅作为纯聊天机器人运行。")
            llm_with_tools = model
        else:
            print(f"🛠️  总计可用工具: {len(all_tools_for_llm)}")
            llm_with_tools = model.bind_tools(all_tools_for_llm)
        
        # 2. 对话循环
        print("\n💬 交互模式已就绪。输入 'exit', 'quit' 或 Ctrl+C 退出。")
        print("💡 输入 '/clear' 可清除对话记忆。")
        print("-" * 50)
        
        system_content = """你是一个强大的智能助手，可以调用本地工具来完成任务。

**核心要求：思考与行动**
1. **全程中文**：你的所有思考过程、工具参数解释、以及最终回复都**必须**使用中文。
2. **思考先行**：在执行任何操作或调用工具之前，你**必须**先输出你的思考过程。
   - **格式要求**：你的思考过程**必须**包裹在 `<thought>` 和 `</thought>` 标签中。
   - **内容要求**：包含“分析”、“思考”、“行动”三个步骤。
3. **最终回复**：在 `</thought>` 标签之后，给出给用户的最终回答。

通过 `<thought>` 标签展示你的推理过程，这有助于确保任务执行的准确性。前端会自动解析并折叠这段内容。

**关于 Web 设计与开发的重要规则**：
1. **必须使用 Design Tool**：如果用户要求设计网页、UI、APP 或组件，你**必须**首先调用 `consult_frontend_design_guidelines` 工具获取设计指导。不要直接开始写代码。
2. **不要乱用 knowledge_web**：`generate_knowledge_web_page` 工具仅用于将**现有的 JSON 知识文章**转换为网页。如果用户只是让你设计一个新网页，**千万不要**使用这个工具，因为它需要一个已存在的 JSON 文件。
3. **正确流程**：
   - 如果用户要设计网页：先调用 `consult_frontend_design_guidelines` -> 然后思考设计方案 -> 最后使用文件操作工具（如 write_file/run_command，注意：目前你可能需要提示用户你准备生成代码，或者如果支持文件操作工具则直接生成）来创建 HTML/CSS/JS 文件。
   - 既然你现在主要拥有 `local_skills` 和 `github` 工具，如果需要创建文件，请检查是否有名为 `write_file` 或类似的工具。如果没有，请直接在回复中输出完整的代码，并提示用户保存。
   - **注意**：你的 local_skills 中可能包含 `docx` (文档处理), `imagen` (图片生成) 等工具。请只在相关时调用。

**关于错误处理**：
- 如果工具调用失败（例如文件不存在），请不要假装什么都没发生。请明确告诉用户错误原因，并尝试提供替代方案（例如询问用户是否要先创建该文件，或者自己生成内容）。
"""
        
        system_message = SystemMessage(content=system_content)
        
        # 初始化记忆管理器
        memory_manager = MemoryManager()
        loaded_history = memory_manager.load_memory()
        
        if loaded_history:
            print(f"📖 已加载 {len(loaded_history)} 条历史消息")
            chat_history = [system_message] + loaded_history
        else:
            chat_history = [system_message]
        
        while True:
            try:
                user_input = input("\n👤 User: ").strip()
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.lower() in ["exit", "quit"]:
                    print("👋 再见！")
                    break
                
                if user_input.lower() == "/clear":
                    memory_manager.clear_memory()
                    chat_history = [system_message]
                    print("🧹 记忆已清除，开始新会话。")
                    continue
                
                chat_history.append(HumanMessage(content=user_input))
                
                # 循环处理工具调用，直到 AI 不再调用工具为止
                while True:
                    # 调用模型 (使用流式输出以显示思考过程)
                    print("🤖 AI: ", end="", flush=True)
                    
                    full_response = None
                    async for chunk in llm_with_tools.astream(chat_history):
                        if not full_response:
                            full_response = chunk
                        else:
                            full_response += chunk
                        
                        if chunk.content:
                            print(chunk.content, end="", flush=True)
                            
                    print() # 换行
                    
                    ai_msg = full_response
                    chat_history.append(ai_msg)
                    
                    # 如果没有工具调用，说明是最终回复，跳出循环
                    if not ai_msg.tool_calls:
                        if not ai_msg.content:
                            print("🤖 AI: (无内容返回，可能是模型思考过程未被捕获，请尝试重新提问)")
                        else:
                            print(f"🤖 AI: {ai_msg.content}")
                        break
                    
                    # 检查是否有格式错误的工具调用
                    if hasattr(ai_msg, 'invalid_tool_calls') and ai_msg.invalid_tool_calls:
                        print(f"  ⚠️  检测到格式错误的工具调用: {ai_msg.invalid_tool_calls}")
                    
                    # 处理工具调用
                    if not ai_msg.content:
                         print("(准备调用工具...)")
                    
                    for tool_call in ai_msg.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        tool_id = tool_call['id']
                        
                        print(f"\n  ⚙️  [调用工具] {tool_name}")
                        print(f"  📝 [参数] {json.dumps(tool_args, ensure_ascii=False)}")
                        
                        session_name = tool_to_session_map.get(tool_name)
                        if not session_name or session_name not in sessions:
                            error_msg = f"Error: Tool '{tool_name}' not found in any connected session."
                            print(f"  ❌ {error_msg}")
                            chat_history.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
                            continue
                            
                        session = sessions[session_name]
                        try:
                            # 执行 MCP 工具调用
                            result = await session.call_tool(tool_name, tool_args)
                            
                            # 提取文本结果
                            tool_output = ""
                            if result.content:
                                for content in result.content:
                                    if hasattr(content, 'text'):
                                        tool_output += content.text
                                    elif hasattr(content, 'data'):
                                        tool_output += f"[Binary Data: {content.mimeType}]"
                                    else:
                                        tool_output += str(content)
                            else:
                                tool_output = "Success (No content returned)"
                                
                            print(f"  ✅ [结果] {tool_output[:200]}..." if len(tool_output) > 200 else f"  ✅ [结果] {tool_output}")
                            
                            chat_history.append(ToolMessage(content=tool_output, tool_call_id=tool_id))
                            
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            print(f"  ❌ {error_msg}")
                            chat_history.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
                    
                    # 循环继续，再次调用 ainvoke，将 ToolMessage 传入，模型会决定是继续调用工具还是输出回复
                
                # 保存记忆
                memory_manager.save_memory(chat_history)

            except KeyboardInterrupt:
                print("\n👋 用户中断。")
                break
            except Exception as e:
                print(f"\n❌ 发生意外错误: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        pass
