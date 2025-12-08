import asyncio
import math
import time
import pandas as pd
import matplotlib.pyplot as plt
from toio import *

# --- 設定パラメータ ---
WAYPOINTS = [(180, 180), (350, 150), (350, 350), (150, 350), (180, 180)]
REACH_THRESHOLD = 20 
# 距離制御用のPIDゲイン
DIST_KP = 0.8
DIST_KI = 0.0
DIST_KD = 0.05

# 角度制御用のPIDゲイン
ANGLE_KP = 0.5
ANGLE_KI = 0.0
ANGLE_KD = 0.01

# --- PIDクラス (省略なし) ---
class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp; self.ki = ki; self.kd = kd
        self.prev_error = 0.0; self.integral = 0.0; self.last_time = None
    def update(self, error):
        current_time = time.time()
        if self.last_time is None:
            self.last_time = current_time; return error * self.kp
        dt = current_time - self.last_time
        self.last_time = current_time
        if dt <= 0: return 0
        p_term = error * self.kp
        self.integral += error * dt
        i_term = self.integral * self.ki
        derivative = (error - self.prev_error) / dt
        d_term = derivative * self.kd
        self.prev_error = error
        return p_term + i_term + d_term

# --- グローバル変数 ---
current_x, current_y, current_angle = 0, 0, 0
is_position_received = False 
log_data = [] # ★データ記録用リスト

# --- ハンドラ ---
def position_handler(id_info):
    global current_x, current_y, current_angle, is_position_received
    if id_info and isinstance(id_info, PositionId):
        current_x = id_info.center.point.x
        current_y = id_info.center.point.y
        current_angle = id_info.center.angle
        is_position_received = True

def notification_handler(payload: bytearray):
    id_info = IdInformation.is_my_data(payload)
    position_handler(id_info)

def get_angle_diff(target_deg, current_deg):
    diff = target_deg - current_deg
    while diff <= -180: diff += 360
    while diff > 180: diff -= 360
    return diff

# --- グラフ描画関数 ---
def plot_data():
    if not log_data:
        print("データがありません")
        return
    
    df = pd.DataFrame(log_data)
    # 時間を0スタートに補正
    df['time'] = df['time'] - df['time'][0]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # 1. 距離
    ax1.plot(df['time'], df['distance'], label='Target Distance', color='blue')
    ax1.set_ylabel('Distance (mm)')
    ax1.grid(True); ax1.legend()

    # 2. 角度
    ax2.plot(df['time'], df['target_angle'], label='Target Angle', color='green', linestyle='--')
    ax2.plot(df['time'], df['current_angle'], label='Current Angle', color='orange')
    ax2.set_ylabel('Angle (deg)')
    ax2.grid(True); ax2.legend()

    # 3. モーター出力
    ax3.plot(df['time'], df['left_speed'], label='Left', color='red', alpha=0.7)
    ax3.plot(df['time'], df['right_speed'], label='Right', color='blue', alpha=0.7)
    ax3.set_ylabel('Speed')
    ax3.set_xlabel('Time (s)')
    ax3.grid(True); ax3.legend()

    plt.tight_layout()
    plt.savefig('log_graph.png') # 画像保存
    print("グラフを 'log_graph.png' に保存しました。")
    # plt.show() # 画面表示する場合はコメントアウトを外す

# --- メイン処理 ---
async def main():
    print("toioに接続します...")
    async with ToioCoreCube() as cube:
        print("接続完了！")
        await cube.api.id_information.register_notification_handler(notification_handler)
        
        pid_dist = PIDController(DIST_KP, DIST_KI, DIST_KD)
        pid_angle = PIDController(ANGLE_KP, ANGLE_KI, ANGLE_KD)
        current_wp_index = 0
        
        while not is_position_received:
            await asyncio.sleep(0.1)
        
        start_time = time.time()

        try:
            while True:
                target_x, target_y = WAYPOINTS[current_wp_index]
                
                # 計算
                dx = target_x - current_x
                dy = target_y - current_y
                distance = math.sqrt(dx*dx + dy*dy)
                target_rad = math.atan2(dy, dx)
                target_deg = math.degrees(target_rad)
                angle_diff = get_angle_diff(target_deg, current_angle)

                # 終了判定
                if distance < REACH_THRESHOLD:
                    print(f"ポイント[{current_wp_index}]到達")
                    current_wp_index += 1
                    if current_wp_index >= len(WAYPOINTS):
                        break
                    # PIDリセット
                    pid_dist = PIDController(DIST_KP, DIST_KI, DIST_KD)
                    pid_angle = PIDController(ANGLE_KP, ANGLE_KI, ANGLE_KD)
                    continue

                # PID制御
                speed_output = pid_dist.update(distance)
                turn_output = pid_angle.update(angle_diff)

                base_speed = max(min(speed_output, 70), -70)
                turn_speed = max(min(turn_output, 50), -50)
                left = max(min(int(base_speed + turn_speed), 100), -100)
                right = max(min(int(base_speed - turn_speed), 100), -100)

                await cube.api.motor.motor_control(left, right)

                # ★データを記録
                log_data.append({
                    'time': time.time(),
                    'distance': distance,
                    'current_angle': current_angle,
                    'target_angle': target_deg,
                    'left_speed': left,
                    'right_speed': right
                })

                await asyncio.sleep(0.05)

        except KeyboardInterrupt:
            pass
        finally:
            await cube.api.motor.motor_control(0, 0)
            await cube.api.id_information.unregister_notification_handler(notification_handler)
            print("終了しました。グラフを描画します...")
            plot_data() # ★グラフ描画実行

if __name__ == '__main__':
    asyncio.run(main())