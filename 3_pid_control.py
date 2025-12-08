import asyncio
import math
import time
from toio import *

# --- 設定パラメータ (チューニングの肝！) ---
# 距離制御用のPIDゲイン
DIST_KP = 1.2  # 遠いときのパワー
DIST_KI = 0.05 # 最後のひと押し
DIST_KD = 0.04  # ブレーキ性能

# 角度制御用のPIDゲイン
ANGLE_KP = 0.6 # 向き直りの強さ
ANGLE_KI = 0.0
ANGLE_KD = 0.01 # 首振りの抑制

TARGET_X = 250
TARGET_Y = 250
GOAL_RADIUS = 10

# --- PIDコントローラークラス ---
class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = None

    def update(self, error):
        current_time = time.time()
        
        # 初回呼び出し時の処理
        if self.last_time is None:
            self.last_time = current_time
            return error * self.kp

        # 経過時間(dt)の計算
        dt = current_time - self.last_time
        self.last_time = current_time
        
        if dt <= 0: return 0

        # P項
        p_term = error * self.kp
        
        # I項（積分の計算）
        self.integral += error * dt
        i_term = self.integral * self.ki
        
        # D項（微分の計算：前回の偏差との差）
        derivative = (error - self.prev_error) / dt
        d_term = derivative * self.kd
        
        # 次回のために保存
        self.prev_error = error

        return p_term + i_term + d_term

# --- グローバル変数 ---
current_x = 0
current_y = 0
current_angle = 0
is_position_received = False 

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

# --- メイン処理 ---
async def main():
    print("toioに接続します...")
    async with ToioCoreCube() as cube:
        print("接続完了！")
        await cube.api.id_information.register_notification_handler(notification_handler)
        
        # PIDコントローラーのインスタンス作成
        pid_dist = PIDController(DIST_KP, DIST_KI, DIST_KD)
        pid_angle = PIDController(ANGLE_KP, ANGLE_KI, ANGLE_KD)

        print("目標に向かってスタート！")
        while not is_position_received:
            await asyncio.sleep(0.1)

        try:
            while True:
                # 1. 偏差の計算
                dx = TARGET_X - current_x
                dy = TARGET_Y - current_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < GOAL_RADIUS:
                    print("ゴール！！")
                    await cube.api.motor.motor_control(0, 0)
                    break 

                target_rad = math.atan2(dy, dx)
                target_deg = math.degrees(target_rad)
                angle_diff = get_angle_diff(target_deg, current_angle)

                # 2. PID計算（ここがスッキリ！）
                # 距離に対するPID操作量
                speed_output = pid_dist.update(distance)
                
                # 角度に対するPID操作量
                turn_output = pid_angle.update(angle_diff)

                # 3. リミッターと左右配分
                base_speed = max(min(speed_output, 80), -80) # 最大速度制限
                turn_speed = max(min(turn_output, 50), -50)  # 旋回速度制限

                left = int(base_speed + turn_speed)
                right = int(base_speed - turn_speed)

                # toioの入力限界(-100〜100)に収める
                left = max(min(left, 100), -100)
                right = max(min(right, 100), -100)

                await cube.api.motor.motor_control(left, right)
                await asyncio.sleep(0.05) 

        except KeyboardInterrupt:
            pass
        finally:
            await cube.api.motor.motor_control(0, 0)
            await cube.api.id_information.unregister_notification_handler(notification_handler)

if __name__ == '__main__':
    asyncio.run(main())