import os
import subprocess
import sys
import time
import webbrowser

def check_ollama():
    """检查 Ollama 是否正在运行，并设置模型路径"""
    try:
        # 设置本地模型路径环境变量 (适配用户搬迁后的位置)
        local_ollama_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ollama"))
        os.environ["OLLAMA_MODELS"] = local_ollama_path
        print(f"📍 设置 Ollama 模型路径: {local_ollama_path}")

        # 在 Windows 上检查进程
        output = subprocess.check_output('tasklist /fi "imagename eq ollama.exe"', shell=True).decode('gbk')
        if "ollama.exe" in output:
            print("✅ Ollama 服务已在运行。")
            return True
        else:
            print("⚠️  Ollama 服务未启动，尝试启动中...")
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(5)
            return True
    except Exception as e:
        print(f"❌ 无法启动 Ollama: {e}")
        return False

def check_model():
    """检查 qwen3:4b 模型是否存在"""
    try:
        output = subprocess.check_output(["ollama", "list"]).decode('utf-8')
        if "qwen3:4b" in output:
            print("✅ 模型 qwen3:4b 已就绪。")
            return True
        else:
            print("📥 正在下载模型 qwen3:4b...")
            subprocess.run(["ollama", "pull", "qwen3:4b"])
            return True
    except Exception as e:
        print(f"❌ 无法检查模型状态: {e}")
        return False

def start_web_server():
    """启动 Web 服务器"""
    print("🚀 正在启动 Web 智能体后端服务...")
    print("🌐 访问地址: http://localhost:8001")
    
    # 自动打开浏览器
    webbrowser.open("http://localhost:8001")
    
    # 启动 web_server.py
    try:
        web_server_path = os.path.join(os.path.dirname(__file__), "..", "agent_core", "web_server.py")
        subprocess.run([sys.executable, web_server_path])
    except KeyboardInterrupt:
        print("\n👋 智能体已正常停止。")
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")

if __name__ == "__main__":
    print("===================================================")
    print("🚀 MCP Agent 全自动启动器")
    print("===================================================\n")
    
    # 检查并创建必要的目录
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 已创建 data 目录。")
    
    # 依次执行检查
    if check_ollama():
        if check_model():
            start_web_server()
    
    input("\n按回车键退出...")
