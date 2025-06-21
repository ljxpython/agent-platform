#!/usr/bin/env python3
"""
Midscene 智能体系统 - 前端服务器启动脚本
简单的HTTP服务器，用于提供前端静态文件服务
"""

import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，添加CORS支持"""

    def end_headers(self):
        # 添加CORS头，允许跨域请求
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"[{self.log_date_time_string()}] {format % args}")


def check_backend_status():
    """检查后端服务状态"""
    try:
        import json
        import urllib.request

        response = urllib.request.urlopen("http://localhost:8001/", timeout=5)
        data = json.loads(response.read().decode())

        if data.get("message") == "Midscene Test Generator API":
            return True
    except:
        pass

    return False


def main():
    # 设置工作目录为脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # 配置
    PORT = 8080
    HOST = "localhost"

    print("🤖 Midscene 智能体系统 - 前端服务器")
    print("=" * 50)

    # 检查后端服务状态
    print("🔍 检查后端服务状态...")
    if check_backend_status():
        print("✅ 后端服务运行正常 (http://localhost:8001)")
    else:
        print("⚠️  后端服务未启动或无法访问")
        print("💡 请先启动后端服务：")
        print("   cd backend/examples")
        print("   python midscene_agents.py")
        print()

    # 检查文件是否存在
    required_files = ["index.html", "styles.css", "app.js"]
    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        sys.exit(1)

    print(f"📁 工作目录: {script_dir}")
    print(f"🌐 启动HTTP服务器...")
    print(f"   地址: http://{HOST}:{PORT}")
    print(f"   演示页面: http://{HOST}:{PORT}/demo.html")
    print()

    try:
        # 创建服务器
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ 服务器启动成功！")
            print(f"🚀 正在自动打开浏览器...")
            print()
            print("📋 可用页面:")
            print(f"   主应用: http://{HOST}:{PORT}/")
            print(f"   演示页面: http://{HOST}:{PORT}/demo.html")
            print()
            print("⏹️  按 Ctrl+C 停止服务器")
            print("-" * 50)

            # 自动打开浏览器
            try:
                webbrowser.open(f"http://{HOST}:{PORT}/demo.html")
            except:
                print("⚠️  无法自动打开浏览器，请手动访问上述地址")

            # 启动服务器
            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用")
            print("💡 请尝试以下解决方案:")
            print(f"   1. 使用其他端口: python start_server.py --port 8081")
            print(f"   2. 停止占用端口的进程")
        else:
            print(f"❌ 启动服务器失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 简单的命令行参数处理
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print("Midscene 前端服务器启动脚本")
            print()
            print("用法:")
            print("  python start_server.py [选项]")
            print()
            print("选项:")
            print("  -h, --help     显示帮助信息")
            print("  --port PORT    指定端口号 (默认: 8080)")
            print()
            print("示例:")
            print("  python start_server.py")
            print("  python start_server.py --port 8081")
            sys.exit(0)

        # 处理端口参数
        if "--port" in sys.argv:
            try:
                port_index = sys.argv.index("--port") + 1
                if port_index < len(sys.argv):
                    PORT = int(sys.argv[port_index])
                    print(f"🔧 使用自定义端口: {PORT}")
            except (ValueError, IndexError):
                print("❌ 无效的端口号")
                sys.exit(1)

    main()
