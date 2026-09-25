"""
容器内进程监管器
=================
在一个容器里按顺序拉起三个进程，对外只暴露 Streamlit（8501）：

    ✍️ 文案AI   services/copywriter_service.py   → 127.0.0.1:8001
    🎨 配图AI   services/illustrator_service.py  → 127.0.0.1:8002
    📰 主编界面  streamlit run main.py            → 0.0.0.0:8501

职责划分：
- 后端服务（8001/8002）若异常退出会被**自动重启**，因为它们是无状态的计算服务。
- Streamlit 是面向用户的入口，它退出即认为容器失效 → 整个容器退出，
  交给 Kubernetes / Sealos 的 restartPolicy 重建 Pod（避免"进程活着但页面打不开"）。

信号处理：收到 SIGTERM/SIGINT 时先通知所有子进程，超时后强制结束，
确保滚动更新时能快速、干净地退出。
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

PY = sys.executable

# (名称, 命令, 退出后是否重启, 就绪探测地址)
SERVICES = [
    (
        "copywriter",
        [PY, "services/copywriter_service.py"],
        True,
        "http://127.0.0.1:8001/health",
    ),
    (
        "illustrator",
        [PY, "services/illustrator_service.py"],
        True,
        "http://127.0.0.1:8002/health",
    ),
    (
        "streamlit",
        [
            PY, "-m", "streamlit", "run", "main.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            "--browser.gatherUsageStats=false",
        ],
        False,  # 入口进程：退出即终止容器
        "http://127.0.0.1:8501/_stcore/health",
    ),
]

LOCAL_HEALTH_TIMEOUT = 3


def log(msg: str) -> None:
    print(f"[supervisor] {msg}", flush=True)


def wait_healthy(url: str, name: str, timeout: float = 90.0) -> bool:
    """轮询就绪探测地址，直到成功或超时。仅用于记录启动顺序，不阻塞启动。"""
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=LOCAL_HEALTH_TIMEOUT) as resp:
                if resp.status == 200:
                    log(f"{name} 就绪 ✓")
                    return True
        except Exception:
            pass
        time.sleep(1.0)
    log(f"{name} 在 {timeout:.0f}s 内未就绪（继续运行，由其自身重试）")
    return False


def main() -> int:
    log("AI 新媒体小编团队 — 启动中")
    for name, cmd, _, _ in SERVICES:
        log(f"  准备启动 {name}: {' '.join(cmd)}")

    procs: dict[str, subprocess.Popen] = {}
    restart_counts: dict[str, int] = {name: 0 for name, _, _, _ in SERVICES}
    stopping = False

    def spawn(name: str, cmd: list[str]) -> subprocess.Popen:
        return subprocess.Popen(cmd, cwd="/app" if os.path.isdir("/app") else None)

    def shutdown(signum=None, frame=None):
        nonlocal stopping
        if stopping:
            return
        stopping = True
        log(f"收到信号 {signum}，正在停止所有子进程…")
        for name, proc in procs.items():
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        deadline = time.time() + 15
        for name, proc in procs.items():
            remaining = max(0.0, deadline - time.time())
            try:
                proc.wait(timeout=remaining)
            except Exception:
                log(f"{name} 未在期限内退出，强制结束")
                try:
                    proc.kill()
                except Exception:
                    pass
        log("已停止")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # 先启动两个后端，再做一次就绪等待，最后启动前端
    for name, cmd, restart, health in SERVICES:
        procs[name] = spawn(name, cmd)
        if restart:  # 后端：等服务起来再继续
            wait_healthy(health, name)

    log("全部进程已拉起，进入监管循环")

    while True:
        time.sleep(1.0)

        for name, cmd, restart, _health in SERVICES:
            proc = procs.get(name)
            if proc is None or proc.poll() is None:
                continue

            code = proc.returncode
            if not restart:
                log(f"⚠️  入口进程 {name} 退出 (code={code})，终止容器以便平台重建")
                shutdown()

            restart_counts[name] += 1
            if restart_counts[name] > 20:
                log(f"⚠️  {name} 重启超过 20 次，放弃并终止容器")
                shutdown()

            log(f"⚠️  {name} 退出 (code={code})，第 {restart_counts[name]} 次重启")
            procs[name] = spawn(name, cmd)


if __name__ == "__main__":
    raise SystemExit(main())
