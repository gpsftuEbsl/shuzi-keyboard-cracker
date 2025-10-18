# Version 2 - 改進版
# (整合 auto_clicker_fast 功能) 
# auto_clicker_0_to_9_fast_repeat_only.py
import json
import threading
import time
from pathlib import Path
from itertools import product

import pyautogui
from pynput import keyboard

POSITIONS_FILE = Path("positions.json")
PROGRESS_FILE = Path("progress.json")
LOCK = threading.Lock()

interval = 0.001         # 點擊間隔
clicks_each = 1          # 每個位置點擊次數
loop_forever = True      # 是否無限循環
start_stop_key = keyboard.Key.f8
exit_key = keyboard.Key.esc

running = False
terminate = False
current_index = 0        # 當前執行到第幾組（從0開始）

# === 位置資料 ===
def load_positions():
    if POSITIONS_FILE.exists():
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    # 新增 enter 位置欄位
    base = {str(i): None for i in range(10)}
    base["enter"] = None
    return base

def save_positions(positions):
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

positions = load_positions()

# === 進度紀錄 ===
def save_progress(idx):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"index": idx}, f)

def load_progress():
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
            return int(data.get("index", 0))
        except Exception:
            pass
    return 0

# === 點擊 ===
def fast_click(x, y, times=1):
    pyautogui.moveTo(x, y)
    for _ in range(times):
        pyautogui.click()
        if interval > 0:
            time.sleep(interval)

# === 點擊 Enter 位置 ===
def click_enter_position():
    pos = positions.get("enter")
    if pos:
        x, y = pos
        fast_click(x, y, clicks_each)

# === 主執行函數 ===
def click_sequence():
    global running, terminate, current_index

    digits = '0123456789'
    # 生成所有四位數，保留至少有重複數字的組合
    all_codes = [''.join(p) for p in product(digits, repeat=4) if len(set(p)) < 4]
    total = len(all_codes)

    print(f"[INFO] 共有 {total} 組至少有重複數字的密碼組合。")

    current_index = load_progress()
    if current_index >= total:
        current_index = 0
    print(f"[INFO] 從第 {current_index}/{total} 組開始。")

    while not terminate:
        if not running:
            time.sleep(0.05)
            continue

        for idx in range(current_index, total):
            if not running or terminate:
                break

            s = all_codes[idx]

            # 點擊4個數字
            for key in s:
                pos = positions.get(key)
                if not pos:
                    continue
                x, y = pos
                fast_click(x, y, clicks_each)

            # 點擊 Enter
            click_enter_position()

            current_index = idx + 1
            if idx % 500 == 0:
                print(f"[進度] 已完成 {idx}/{total}")

        if current_index >= total:
            print("[INFO] 已嘗試所有組合。")
            if loop_forever:
                current_index = 0
                print("[INFO] 重新開始。")
            else:
                running = False

        save_progress(current_index)
        time.sleep(0.05)

# === 鍵盤監聽 ===
def on_press(key):
    global running, terminate, positions

    try:
        # 0~9 記錄數字位置
        if hasattr(key, 'char') and key.char in "0123456789":
            idx = key.char
            x, y = pyautogui.position()
            with LOCK:
                positions[idx] = (x, y)
                save_positions(positions)
            print(f"已儲存位置 {idx} -> ({x}, {y})")
            return

        # e 鍵記錄 Enter 位置
        if hasattr(key, 'char') and key.char.lower() == 'e':
            x, y = pyautogui.position()
            with LOCK:
                positions["enter"] = (x, y)
                save_positions(positions)
            print(f"已儲存 Enter 位置 -> ({x}, {y})")
            return

    except AttributeError:
        pass

    if key == start_stop_key:
        running = not running
        print("▶️ 開始執行" if running else "⏸ 已暫停")
    elif key == exit_key:
        terminate = True
        save_progress(current_index)
        print("🟥 結束程式並保存進度")

def print_help():
    print("--- 自動連點器 0-9（至少重複+續跑+自訂Enter位置+超快點擊）---")
    print("操作說明：")
    print("  按 0~9 -> 儲存目前滑鼠位置到對應編號 (會覆寫)")
    print("  按 E   -> 設定 Enter 點擊位置")
    print("  按 F8  -> 開始 / 暫停 (會從上次中斷點繼續)")
    print("  按 ESC -> 儲存進度並退出程式")
    print()
    print("目前已載入的位置：")
    for i in range(10):
        print(f"  {i}: {positions.get(str(i))}")
    print(f"  Enter: {positions.get('enter')}")
    print(f"目前進度檔: {PROGRESS_FILE if PROGRESS_FILE.exists() else '無'}")
    print(f"設定: interval={interval}s, clicks_each={clicks_each}, loop_forever={loop_forever}")
    print("----------------------------------------")

def main():
    global positions
    with LOCK:
        p = load_positions()
        if "enter" not in p:
            p["enter"] = None
        for i in range(10):
            if str(i) not in p:
                p[str(i)] = None
        positions = p
        save_positions(positions)

    print_help()

    t = threading.Thread(target=click_sequence, daemon=True)
    t.start()

    with keyboard.Listener(on_press=on_press) as listener:
        while not terminate:
            time.sleep(0.05)
        listener.stop()

    print("程式已結束。")

if __name__ == "__main__":
    main()
