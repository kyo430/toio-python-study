import asyncio
import math
from toio import *

# --- 設定 ---
# 目標地点の座標（マットの中央付近）
TARGET_X = 250
TARGET_Y = 250
# ゴールとみなす範囲（半径）
GOAL_RADIUS = 20

# 現在地を保持する変数（グローバル変数として扱う）
current_x = 0
current_y = 0
current_angle = 0
is_position_received = False # 座標を一度でも受信したかフラグ

# --- 1. 座標を受け取るハンドラ ---
def position_handler(id_info):
    global current_x, current_y, current_angle, is_position_received
    if id_info and isinstance(id_info, PositionId):
        # 最新の座標を変数に更新
        current_x = id_info.center.point.x
        current_y = id_info.center.point.y
        current_angle = id_info.center.angle
        is_position_received = True

def notification_handler(payload: bytearray):
    id_info = IdInformation.is_my_data(payload)
    position_handler(id_info)

# --- 2. 角度の差分を計算する便利関数 ---
# -180度〜+180度の範囲で、どちらにどれだけ回ればいいかを計算
def get_angle_diff(target_deg, current_deg):
    diff = target_deg - current_deg
    while diff <= -180: diff += 360
    while diff > 180: diff -= 360
    return diff

# --- 3. メイン処理 ---
async def main():
    print("toioに接続します...")
    async with ToioCoreCube() as cube:
        print("接続完了！")
        await cube.api.id_information.register_notification_handler(notification_handler)
        
        print("マットに置いてください。目標に向かって走り出します！")
        # 最初の座標を受信するまで待つ
        while not is_position_received:
            await asyncio.sleep(0.1)

        # --- 制御ループ ---
        try:
            while True:
                # A. ゴールまでの差分を計算（距離と角度）
                dx = TARGET_X - current_x
                dy = TARGET_Y - current_y
                distance = math.sqrt(dx*dx + dy*dy) # 三平方の定理で距離を計算

                # B. ゴール判定
                if distance < GOAL_RADIUS:
                    print("ゴールに到達しました！")
                    await cube.api.motor.motor_control(0, 0) # 停止
                    break # ループを抜ける

                # C. 目標角度の計算 (atan2を使用)
                # math.atan2の結果はラジアンなので、度に変換する
                target_rad = math.atan2(dy, dx)
                target_deg = math.degrees(target_rad)
                
                # 現在の向きとの差分を計算
                angle_diff = get_angle_diff(target_deg, current_angle)

                # D. モーター速度の決定（シンプルなP制御）
                # 基本速度（距離が遠いほど速く、最大80）
                base_speed = min(int(distance * 0.5), 80)
                # 旋回成分（角度のズレが大きいほど強く曲がる）
                turn_speed = int(angle_diff * 0.8) # 係数1.5は調整が必要

                # 左右のモーター速度を計算
                left_speed = base_speed + turn_speed
                right_speed = base_speed - turn_speed

                # 速度制限（toioの仕様上 -100〜100の範囲に収める）
                left_speed = max(min(left_speed, 100), -100)
                right_speed = max(min(right_speed, 100), -100)

                # モーター指令を送信
                await cube.api.motor.motor_control(left_speed, right_speed)
                
                print(f"Dist:{distance:.1f}, AngleDiff:{angle_diff:.1f}, L:{left_speed}, R:{right_speed}")

                # 制御周期（この時間を短くすると滑らかになるが負荷が増える）
                await asyncio.sleep(0.05) # 50msごとに計算

        except KeyboardInterrupt:
            print("\n停止します。")
        finally:
            await cube.api.motor.motor_control(0, 0) # 安全のため最後に必ず停止
            await cube.api.id_information.unregister_notification_handler(notification_handler)
            print("切断しました。")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass