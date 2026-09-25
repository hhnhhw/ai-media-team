"""
一键启动所有服务（开发用）
- 文案AI服务 → http://127.0.0.1:8001
- 配图AI服务 → http://127.0.0.1:8002
- Streamlit主界面 → http://127.0.0.1:8501
"""
import subprocess, sys, time, os, socket

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def _kill_port(port: int):
    if _port_in_use(port):
        print(f"  ⚠️  端口 {port} 被占用，尝试释放...")
        if sys.platform == "win32":
            os.system(f'netstat -ano | findstr ":{port} " > nul && for /f "tokens=5" %a in (\'netstat -ano ^| findstr ":{port} "\') do taskkill /F /PID %a > nul 2>&1')
        time.sleep(1)


def main():
    # 先释放被占用的端口
    for port in [8001, 8002, 8501]:
        _kill_port(port)

    print("=" * 60)
    print("  🤖 AI新媒体小编团队 — 启动中...")
    print("=" * 60)
    print(f"  ✍️  文案AI服务  → http://127.0.0.1:8001")
    print(f"  🎨 配图AI服务  → http://127.0.0.1:8002")
    print(f"  📰 主编界面    → http://127.0.0.1:8501")
    print("=" * 60)

    processes = []

    for name, script in [("文案AI", "services/copywriter_service.py"),
                          ("配图AI", "services/illustrator_service.py")]:
        p = subprocess.Popen([sys.executable, os.path.join(BASE_DIR, script)])
        processes.append((name, p))

    print("\n⏳ 等待后端服务就绪...")
    time.sleep(4)

    # 检查后端是否都启动成功
    for svc_name, p in processes[:2]:
        if p.poll() is not None:
            print(f"\n❌ [{svc_name}] 启动失败 (code={p.returncode})，请检查端口是否被占用")
            for _, proc in processes:
                proc.terminate()
            return

    p3 = subprocess.Popen([sys.executable, "-m", "streamlit", "run", os.path.join(BASE_DIR, "main.py")])
    processes.append(("Streamlit", p3))

    print("\n✅ 所有服务已启动！浏览器打开 http://127.0.0.1:8501")
    print("   按 Ctrl+C 停止所有服务\n")

    try:
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    print(f"\n⚠️  [{name}] 退出 (code={p.returncode})，停止所有服务...")
                    for _, proc in processes:
                        proc.terminate()
                    return
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止...")
        for _, p in processes:
            p.kill()
        print("✅ 已停止")


if __name__ == "__main__":
    main()
