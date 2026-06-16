import cv2
from cvzone.FaceMeshModule import FaceMeshDetector
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import config
import utils

# 初始化疲勞計數器
CLOSED_FRAME_COUNTER = 0
YAWN_FRAME_COUNTER = 0

# 校正狀態控制
calibration_ear_logs = []
EAR_THRESHOLD = 0.22
is_calibrated = False

# 初始化 Pandas 資料列表
data_logs = []

# 初始化攝影機與偵測器
cap = cv2.VideoCapture(0)
detector = FaceMeshDetector(maxFaces=1)

print("系統啟動！請在畫面亮起後「正常直視鏡頭」進行 5 秒鐘的動態校正...")

while True:
    success, img = cap.read()
    if not success:
        break

    img, faces = detector.findFaceMesh(img, draw=True)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    status_eye = "Normal"
    status_mouth = "Normal"

    if faces:
        face = faces[0]

        # 抓取特徵點座標
        left_up, left_down, left_left, left_right = face[159][:2], face[145][:2], face[33][:2], face[133][:2]
        right_up, right_down, right_left, right_right = face[386][:2], face[374][:2], face[362][:2], face[263][:2]
        mouth_up, mouth_down, mouth_left, mouth_right = face[13][:2], face[14][:2], face[78][:2], face[308][:2]

        # 計算 EAR 與 MAR
        avg_EAR = (utils.calculate_ratio(left_up, left_down, left_left, left_right) +
                   utils.calculate_ratio(right_up, right_down, right_left, right_right)) / 2.0
        MAR = utils.calculate_ratio(mouth_up, mouth_down, mouth_left, mouth_right)

        # --- NumPy 動態基準校正邏輯 ---
        if not is_calibrated:
            calibration_ear_logs.append(avg_EAR)
            current_count = len(calibration_ear_logs)

            cv2.putText(img, f"CALIBRATING... ({current_count}/{config.CALIBRATION_FRAMES})",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

            if current_count >= config.CALIBRATION_FRAMES:
                ear_mean, ear_std, EAR_THRESHOLD = utils.run_numpy_calibration(calibration_ear_logs)
                is_calibrated = True

                print(f"\n[校正完成] 您的正常視線平均 EAR: {ear_mean:.2f}, 標準差: {ear_std:.4f}")
                print(f"👉 系統為您量身打造的專屬閉眼門檻值為: {EAR_THRESHOLD}")

                # ✨ 聲音優化點 1：校正完成，播放 5 秒直視後的「叮」聲
                utils.play_sound("ding.mp3")
                utils.send_telegram_message(f"🚀 DMS系統校正完成！\n您的專屬疲勞門檻值已設為: {EAR_THRESHOLD}")

            cv2.imshow("Driver Monitor System", img)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            continue

        # --- 校正完成後的正常監控邏輯 ---
        if avg_EAR < EAR_THRESHOLD:
            CLOSED_FRAME_COUNTER += 1
            status_eye = "Closed"
            if CLOSED_FRAME_COUNTER == config.CLOSED_FRAME_LIMIT:
                # ✨ 聲音優化點 2：連續閉眼滿 3 秒，發出「逼」警報聲 [cite: 24, 44]
                utils.play_sound("beep.mp3")
                utils.send_telegram_message(
                    f"⚠️ 警告！駕駛連續閉眼超過3秒！\n時間: {current_time}\n當前EAR: {avg_EAR:.2f} (門檻: {EAR_THRESHOLD})")
        else:
            CLOSED_FRAME_COUNTER = 0

        if MAR > config.MAR_THRESHOLD:
            YAWN_FRAME_COUNTER += 1
            status_mouth = "Yawning"
            if YAWN_FRAME_COUNTER == config.YAWN_FRAME_LIMIT:
                # ✨ 聲音優化點 3：連續打哈欠滿 3 秒，發出「逼」警報聲 [cite: 24, 44]
                utils.play_sound("beep.mp3")
                utils.send_telegram_message(f"🥱 提醒：偵測到駕駛連續打哈欠滿3秒。\n時間: {current_time}")
        else:
            YAWN_FRAME_COUNTER = 0

        # 儲存歷史數據到列表
        data_logs.append({
            "Timestamp": current_time,
            "EAR": round(avg_EAR, 4),
            "MAR": round(MAR, 4),
            "Eye_Status": status_eye,
            "Mouth_Status": status_mouth,
            "Eye_Counter": CLOSED_FRAME_COUNTER,
            "Mouth_Counter": YAWN_FRAME_COUNTER
        })

        # 畫面資訊顯示
        cv2.putText(img, f"EAR: {avg_EAR:.2f} | Threshold: {EAR_THRESHOLD:.2f}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2)
        cv2.putText(img, f"MAR: {MAR:.2f} | Count: {YAWN_FRAME_COUNTER}/{config.YAWN_FRAME_LIMIT}", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        if CLOSED_FRAME_COUNTER >= config.CLOSED_FRAME_LIMIT:
            cv2.putText(img, "DANGER: SLEEPING!!!", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        elif CLOSED_FRAME_COUNTER > 0:
            cv2.putText(img, f"Eyes Closed: {CLOSED_FRAME_COUNTER}", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 165, 255), 2)

        if YAWN_FRAME_COUNTER >= config.YAWN_FRAME_LIMIT:
            cv2.putText(img, "WARNING: YAWNING!!!", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

    cv2.imshow("Driver Monitor System", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
#  程式結束
if data_logs:
    print("\n正在生成駕駛專注度數據報告...")
    df = pd.DataFrame(data_logs)

    df.to_csv("driver_log.csv", index=False, encoding="utf-8-sig")
    print("歷史數據已儲存至 driver_log.csv")

    total_sleep_events = len(df[df["Eye_Counter"] == config.CLOSED_FRAME_LIMIT])
    total_yawn_events = len(df[df["Mouth_Counter"] == config.YAWN_FRAME_LIMIT])

    total_frames = len(df)
    closed_frames = len(df[df["Eye_Status"] == "Closed"])
    yawn_frames = len(df[df["Mouth_Status"] == "Yawning"])

    report_text = (
        f"📊 ===== 駕駛專注度數據報告 =====\n"
        f"總監控時間幀數: {total_frames} 幀\n"
        f"------------------------------\n"
        f"🚨 嚴重閉眼打瞌睡 (≥3秒): {total_sleep_events} 次\n"
        f"🥱 嚴重連續打哈欠 (≥3秒): {total_yawn_events} 次\n"
        f"------------------------------\n"
        f"累積閉眼總幀數: {closed_frames} 幀 (佔比: {closed_frames / total_frames * 100:.1f}%)\n"
        f"累積哈欠總幀數: {yawn_frames} 幀 (佔比: {yawn_frames / total_frames * 100:.1f}%)\n"
        f"=============================="
    )
    print("\n" + report_text)

    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False

    print("正在繪製疲疲勞趨勢圖...")
    plt.figure(figsize=(10, 5))

    x_indices = np.arange(len(df))
    step = max(1, len(df) // 10)

    plt.plot(df["EAR"], label="眼睛長寬比 (EAR)", color="blue", linewidth=1.5)
    plt.plot(df["MAR"], label="嘴巴長寬比 (MAR)", color="orange", linewidth=1.5)
    plt.axhline(y=EAR_THRESHOLD, color="red", linestyle="--", label=f"個人化閉眼門檻值 ({EAR_THRESHOLD})")

    plt.title("駕駛疲勞度觀測變化趨勢圖", fontsize=14)
    plt.xlabel("監控時間軸 (幀數)", fontsize=12)
    plt.ylabel("特徵比值 (Ratio)", fontsize=12)

    plt.xticks(x_indices[::step], df["Timestamp"].iloc[::step], rotation=30, fontsize=8)
    plt.ylim(0, 1.0)
    plt.legend(loc="upper right")
    plt.tight_layout()

    image_name = "fatigue_trend.png"
    plt.savefig(image_name, dpi=150)
    plt.close()

    utils.send_telegram_photo(image_name, caption_text=report_text)

else:
    print("未偵測到任何數據。")