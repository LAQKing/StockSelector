"""
本地运行脚本 - 读取配置，按间隔执行并自动推送到 Git
用法：python run_local.py
"""
import json
import os
import time
import subprocess
from datetime import datetime

CONFIG_FILE = "config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "top": 10,
            "min_score": 0,
            "tech_weight": 0.6,
            "fund_weight": 0.4,
            "interval_minutes": 60,
            "github": {"auto_commit": True, "commit_message": "Auto update stock selection results"}
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_selection(cfg):
    cmd = [
        "python", "main.py",
        "--top", str(cfg.get("top", 10)),
        "--min-score", str(cfg.get("min_score", 0)),
        "--tech-weight", str(cfg.get("tech_weight", 0.6)),
        "--fund-weight", str(cfg.get("fund_weight", 0.4)),
    ]
    print(f"\n{'='*60}")
    print(f"  执行选股  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def generate_html():
    result = subprocess.run(["python", "generate_html.py"], capture_output=True, text=True)
    print(result.stdout)
    return result.returncode == 0


def git_push(cfg):
    if not cfg.get("github", {}).get("auto_commit", True):
        return
    msg = cfg.get("github", {}).get("commit_message", "Auto update stock selection results")
    try:
        subprocess.run(["git", "add", "result_*.csv", "index.html"], check=False)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", f"{msg} {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=False)
            subprocess.run(["git", "push"], check=False)
            print("✅ 已推送到 GitHub")
        else:
            print("没有变更需要推送")
    except Exception as e:
        print(f"Git 操作失败: {e}")


def main():
    cfg = load_config()
    interval = cfg.get("interval_minutes", 60) * 60
    print(f"📅 配置加载完成")
    print(f"   间隔时间: {cfg.get('interval_minutes', 60)} 分钟")
    print(f"   自动推送: {cfg.get('github', {}).get('auto_commit', True)}")
    print(f"   按 Ctrl+C 停止\n")

    while True:
        run_selection(cfg)
        generate_html()
        git_push(cfg)
        print(f"\n⏰ 等待 {cfg.get('interval_minutes', 60)} 分钟后继续...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
