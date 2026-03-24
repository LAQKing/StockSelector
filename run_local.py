"""
本地运行脚本 - 读取配置，按间隔执行并自动推送到 Git
用法：python run_local.py [--once]
       --once 只运行一次，不循环
"""
import json
import os
import sys
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = [
        "python", "main.py",
        "--top", str(cfg.get("top", 10)),
        "--min-score", str(cfg.get("min_score", 40)),
        "--tech-weight", str(cfg.get("tech_weight", 0.6)),
        "--fund-weight", str(cfg.get("fund_weight", 0.4)),
        "--auto-retry",
    ]
    print(f"\n{'='*60}")
    print(f"  Executing stock selection  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8", errors="replace", cwd=script_dir)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    return result.returncode == 0


def generate_html():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        ["python", "generate_html.py"], 
        capture_output=True, text=True, env=env, encoding="utf-8", errors="replace",
        cwd=script_dir
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def git_push(cfg):
    if not cfg.get("github", {}).get("auto_commit", True):
        return
    msg = cfg.get("github", {}).get("commit_message", "Auto update stock selection results")
    try:
        html_file = "index.html"
        
        if os.path.exists(html_file):
            subprocess.run(["git", "add", html_file], check=False)
            
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", f"{msg} {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=False)
            
            # Retry push up to 5 times
            for attempt in range(5):
                result = subprocess.run(["git", "push"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Pushed to GitHub")
                    break
                print(f"Push failed, retrying ({attempt + 1}/5)...")
                time.sleep(5)
            else:
                print("Push failed after 5 attempts")
        else:
            print("No changes to push")
    except Exception as e:
        print(f"Git error: {e}")


def main():
    cfg = load_config()
    interval = cfg.get("interval_minutes", 60) * 60
    
    run_once = "--once" in sys.argv
    
    print(f"Config loaded")
    print(f"   Interval: {cfg.get('interval_minutes', 60)} minutes")
    print(f"   Auto push: {cfg.get('github', {}).get('auto_commit', True)}")
    print(f"   Mode: {'Run once' if run_once else 'Loop'}")
    print(f"   Press Ctrl+C to stop\n")

    if run_once:
        success = run_selection(cfg)
        if success:
            generate_html()
            git_push(cfg)
        else:
            print("No stocks selected, skipping update")
    else:
        while True:
            success = run_selection(cfg)
            if success:
                generate_html()
                git_push(cfg)
            else:
                print("No stocks selected, skipping update")
            print(f"\nWaiting {cfg.get('interval_minutes', 60)} minutes...")
            time.sleep(interval)


if __name__ == "__main__":
    main()
