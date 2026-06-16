import numpy as np
import requests
import config
import pygame  # 新增：引入音效套件

# 初始化 Pygame 的混音器 (指定頻率與雙聲道，確保音效流暢)
pygame.mixer.init()


def play_sound(sound_path):
    """新增：非同步播放音效函式，不會卡住 OpenCV 影像畫面"""
    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.play()
    except Exception as e:
        print(f"🎵 音效播放失敗 ({sound_path}):", e)


def send_telegram_message(msg):
    """發送文字訊息到 Telegram Bot"""
    url = f"https://api.telegram.org/bot{config.TG_TOKEN}/sendMessage"
    payload = {"chat_id": config.TG_CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram 文字發送失敗:", e)


def send_telegram_photo(photo_path, caption_text):
    """發送本地圖片與統計報告到 Telegram Bot"""
    url = f"https://api.telegram.org/bot{config.TG_TOKEN}/sendPhoto"
    payload = {"chat_id": config.TG_CHAT_ID, "caption": caption_text}
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            response = requests.post(url, data=payload, files=files, timeout=10)
            if response.status_code == 200:
                print("📊 疲勞趨勢圖與統計報告已成功發送到您的 Telegram！")
            else:
                print("圖片發送失敗，錯誤碼:", response.status_code)
    except Exception as e:
        print("發送圖片時發生網路錯誤:", e)


def calculate_ratio(p1, p2, p3, p4):
    """利用 NumPy 計算兩點垂直與水平距離的比值"""
    pt1, pt2, pt3, pt4 = np.array(p1), np.array(p2), np.array(p3), np.array(p4)
    vertical_dist = np.linalg.norm(pt1 - pt2)
    horizontal_dist = np.linalg.norm(pt3 - pt4)
    return vertical_dist / horizontal_dist if horizontal_dist != 0 else 0


def run_numpy_calibration(ear_logs):
    """利用 NumPy 計算個人化閉眼門檻值 (含唱歌雙重安全鎖)"""
    ear_array = np.array(ear_logs)
    ear_mean = np.mean(ear_array)
    ear_std = np.std(ear_array)

    threshold = round(ear_mean - (4.5 * ear_std), 4)

    if threshold < 0.15: threshold = 0.18
    if threshold > 0.22: threshold = 0.20

    return ear_mean, ear_std, threshold