import asyncio
import os
import sys
import subprocess
import time
import webbrowser
import platform

def setup_ollama_env():
    """设置本地模型路径环境变量 (适配用户搬迁后的位置)"""
    local_ollama_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ollama"))
    os.environ["OLLAMA_MODELS"] = local_ollama_path
    print(f"📍 Ollama 模型路径已设置为: {local_ollama_path}")
    return local_ollama_path

def is_ollama_running():
    """检查 Ollama 进程是否正在运行"""
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output('tasklist /fi "imagename eq ollama.exe"', shell=True).decode('gbk')
            return "ollama.exe" in output
        else:
            # 简单适配其他系统
            subprocess.check_output(["pgrep", "ollama"])
            return True
    except:
        return False

async def ensure_ollama_service():
    """确保 Ollama 服务已启动且模型就绪"""
    if not is_ollama_running():
        print("⚠️  Ollama 服务未启动，正在后台启动...")
        if platform.system() == "Windows":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待启动
        print("⏳ 等待 Ollama 初始化 (5秒)...")
        await asyncio.sleep(5)
    else:
        print("✅ Ollama 服务已在运行。")

    # 检查模型
    try:
        output = subprocess.check_output(["ollama", "list"]).decode('utf-8')
        if "qwen3:4b" not in output:
            print("📥 正在拉取模型 qwen3:4b (这可能需要一些时间)...")
            subprocess.run(["ollama", "pull", "qwen3:4b"])
        else:
            print("✅ 模型 qwen3:4b 已就绪。")
    except Exception as e:
        print(f"❌ 检查模型时出错: {e}")

def start_web_backend():
    """启动 Web 后端服务"""
    print("🚀 启动智能体 Web 后端 (Port: 8002)...")
    web_server_path = os.path.join(os.path.dirname(__file__), "..", "agent_core", "web_server.py")
    
    # 使用当前解释器启动
    return subprocess.Popen([sys.executable, web_server_path])

async def main():
    print("===================================================")
    print("🚀 MCP Agent 全自动启动器 (run.py)")
    print("===================================================\n")

    # 1. 环境准备
    setup_ollama_env()
    
    # 2. 确保数据目录
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"📁 已创建数据目录: {data_dir}")

    # 3. 启动/检查 Ollama
    await ensure_ollama_service()

    # 4. 启动后端
    backend_proc = start_web_backend()

    # 5. 打开浏览器
    print("🌐 正在打开 Web 界面: http://localhost:8002")
    time.sleep(2) # 给后端一点点启动时间
    webbrowser.open("http://localhost:8002")

    print("\n💡 智能体已全量启动。")
    print("👉 请在浏览器中进行对话。")
    print("⌨️  按 Ctrl+C 停止所有服务。")

    try:
        # 持续运行直到手动停止
        while True:
            await asyncio.sleep(1)
            if backend_proc.poll() is not None:
                print("❌ 后端服务已意外停止。")
                break
    except KeyboardInterrupt:
        print("\n👋 正在关闭所有服务...")
        backend_proc.terminate()
        print("✅ 已停止。")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
