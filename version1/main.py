# Version 1 - 基本版主程式(包含設定鍵盤位置、調整輸入速度等)
# auto_clicker_0_to_9.py
# 使用說明:
# 1) 執行腳本後，按 0-9 任一數字鍵可儲存當前滑鼠位置到 positions.json (覆寫該編號)
# 2) 按 F8 開始/暫停依序點擊已儲存的位置 (從 0 到 9)
# 3) 按 ESC 結束程序
#
# pip install pyautogui pynput

import json
import threading
import time
import os
from pathlib import Path

import pyautogui
from pynput import keyboard

POSITIONS_FILE = Path("positions.json")
LOCK = threading.Lock()

# 預設設定
interval = 0.1       # 每次點擊間隔 (秒) 不能太快
clicks_each = 1      # 每個位置點擊次數（1 表示每到一個位址點一次）
loop_forever = True  # True 表示持續重複 0-9；False 表示只做一次通過
start_stop_key = keyboard.Key.f8
exit_key = keyboard.Key.esc

running = False
terminate = False

def load_positions():
    if POSITIONS_FILE.exists():
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    # 初始化為 None 的 0-9
    return {str(i): None for i in range(10)}

def save_positions(positions):
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

positions = load_positions()

def click_sequence():
    global running, terminate
    while not terminate:
        if not running:
            time.sleep(0.1)
            continue

        # 做一次從 9999->0000 的通過（或持續循環）
        for i in range(9400,-1,-1):
            if not running or terminate:
                break
            s = f"{i:04d}"  # 保證長度 4
            print(f"點擊序列: {s}")
            for j in range(4):
                key = s[j]
                pos = positions.get(key)
                if not pos:
                    continue  # 沒錄就跳過
                x, y = pos
                for _ in range(clicks_each):
                    pyautogui.click(x, y)
                    time.sleep(interval)
        if not loop_forever:
            running = False


def on_press(key):
    global running, terminate, positions
    try:
        # 按數字鍵錄製位置 —— 支援主鍵盤區與小鍵盤數字
        if hasattr(key, 'char') and key.char in "0123456789":
            idx = key.char
            x, y = pyautogui.position()
            with LOCK:
                positions[idx] = (x, y)
                save_positions(positions)
            print(f"已儲存位置 {idx} -> ({x}, {y})")
            return
    except AttributeError:
        pass

    # 功能鍵: F8 開/關，ESC 結束
    if key == start_stop_key:
        running = not running
        print("開始執行" if running else "已暫停")
    elif key == exit_key:
        terminate = True
        print("終止程式（正在結束）")
        # 停止運作 flag，實際 listener 會在主程式關閉

def print_help():
    print("--- 自動連點器 (0-9) ---")
    print("操作說明：")
    print("  按 0~9 -> 儲存目前滑鼠位置到對應編號 (會覆寫)")
    print("  按 F8  -> 開始 / 暫停 依序點擊 0->9")
    print("  按 ESC -> 退出程式")
    print()
    print("目前已載入的位置：")
    for i in range(10):
        v = positions.get(str(i))
        print(f"  {i}: {v}")
    print()
    print(f"設定: interval={interval}s, clicks_each={clicks_each}, loop_forever={loop_forever}")
    print("--------------------------")

def main():
    global positions
    # 確保 positions 有 0-9 的欄位
    with LOCK:
        p = load_positions()
        # merge to ensure all keys exist
        for i in range(10):
            if str(i) not in p:
                p[str(i)] = None
        positions = p
        save_positions(positions)

    print_help()

    # 啟動點擊執行緒
    t = threading.Thread(target=click_sequence, daemon=True)
    t.start()

    # 鍵盤監聽（阻塞在 with 裡直到 terminate）
    with keyboard.Listener(on_press=on_press) as listener:
        while not terminate:
            time.sleep(0.1)
        listener.stop()

    print("程式已結束。")

if __name__ == "__main__":
    main()
