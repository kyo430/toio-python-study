import asyncio
import math
import time
from toio import *

# --- 1. 設定パラメータ ---
# ★ START_POS の設定は削除しました（自動取得します） ★

GOAL_POS = (350, 350)  # ゴール地点
REACH_THRESHOLD = 20   # 到達判定の半径

# 仮想障害物の設定
OBSTACLE_POS = (250, 250) # 障害物の中心
OBSTACLE_RADIUS = 30      # 障害物の半径(mm)

# 距離制御用のPIDゲイン
DIST_KP = 0.8
DIST_KI = 0.0
DIST_KD = 0.05

# 角度制御用のPIDゲイン
ANGLE_KP = 0.5
ANGLE_KI = 0.0
ANGLE_KD = 0.01

# --- 2. グローバル変数 ---
current_x = 0
current_y = 0
current_angle = 0
is_position_received = False 

# 回避制御の状態管理
avoid_state = {
    "is_active": False,
    "target_x": 0,
    "target_y": 0
}

# --- 3. クラス・関数定義 ---

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

def get_angle_diff(target, current):
    diff = target - current
    while diff <= -180: diff += 360
    while diff > 180: diff -= 360
    return diff

def is_path_blocked(curr_x, curr_y, goal_x, goal_y, obs_x, obs_y, safe_radius):
    ax, ay = curr_x, curr_y
    bx, by = goal_x, goal_y
    cx, cy = obs_x, obs_y
    ab_x, ab_y = bx - ax, by - ay
    ac_x, ac_y = cx - ax, cy - ay
    ab_len2 = ab_x**2 + ab_y**2
    if ab_len2 == 0: return False
    t = (ac_x * ab_x + ac_y * ab_y) / ab_len2
    if t < 0: nearest_dist = math.sqrt(ac_x**2 + ac_y**2)
    elif t > 1: nearest_dist = math.sqrt((cx - bx)**2 + (cy - by)**2)
    else:
        nearest_x = ax + t * ab_x
        nearest_y = ay + t * ab_y
        nearest_dist = math.sqrt((cx - nearest_x)**2 + (cy - nearest_y)**2)
    return nearest_dist < safe_radius

def calculate_target(curr_x, curr_y, goal_x, goal_y):
    global avoid_state
    
    # --- ★修正ポイント：攻めた設定に変更 ---
    
    # 1. 危険判定（Entry）: +20mm (80mm) → +15mm (75mm)
    # 本当にギリギリまで反応しないようにします
    DETECT_RADIUS = OBSTACLE_RADIUS + 15

    # 2. 経由地（Waypoint）: +90mm (150mm) → +45mm (105mm)
    # 障害物のスレスレ（半径+4.5cm）を狙って通過させます
    # これが「コンパクトさ」の決め手です
    WAYPOINT_RADIUS = OBSTACLE_RADIUS + 45
    
    # 3. 安全確認（Clear）: +40mm (100mm) → +30mm (90mm)
    # 経由地(105mm)より少し内側。このラインを越えていればOKとします
    CLEAR_RADIUS = OBSTACLE_RADIUS + 30

    # （以下、ロジック部分は変更なし）
    if not avoid_state["is_active"]:
        # ゴールへの道が塞がれているかチェック
        is_blocked = is_path_blocked(curr_x, curr_y, goal_x, goal_y, 
                                     OBSTACLE_POS[0], OBSTACLE_POS[1], DETECT_RADIUS)
        
        dist_to_obs = math.sqrt((curr_x - OBSTACLE_POS[0])**2 + (curr_y - OBSTACLE_POS[1])**2)
        
        if is_blocked and dist_to_obs < (DETECT_RADIUS + 100):
            print(">>> 障害物検知！コンパクトに回避します。")
            avoid_state["is_active"] = True
            
            vx = goal_x - OBSTACLE_POS[0]
            vy = goal_y - OBSTACLE_POS[1]
            v_len = math.sqrt(vx**2 + vy**2)
            if v_len == 0: v_len = 1
            ux, uy = vx/v_len, vy/v_len
            
            # 左右の候補点（WAYPOINT_RADIUS を使用）
            p1_x = OBSTACLE_POS[0] - uy * WAYPOINT_RADIUS
            p1_y = OBSTACLE_POS[1] + ux * WAYPOINT_RADIUS
            p2_x = OBSTACLE_POS[0] + uy * WAYPOINT_RADIUS
            p2_y = OBSTACLE_POS[1] - ux * WAYPOINT_RADIUS
            
            d1 = (p1_x - curr_x)**2 + (p1_y - curr_y)**2
            d2 = (p2_x - curr_x)**2 + (p2_y - curr_y)**2
            
            if d1 < d2:
                avoid_state["target_x"], avoid_state["target_y"] = p1_x, p1_y
                print(f"-> 左ルート: ({int(p1_x)}, {int(p1_y)})へ")
            else:
                avoid_state["target_x"], avoid_state["target_y"] = p2_x, p2_y
                print(f"-> 右ルート: ({int(p2_x)}, {int(p2_y)})へ")
            return avoid_state["target_x"], avoid_state["target_y"], True
        else:
            return goal_x, goal_y, False

    else:
        tx = avoid_state["target_x"]
        ty = avoid_state["target_y"]
        d_to_wp = math.sqrt((tx - curr_x)**2 + (ty - curr_y)**2)
        
        # 安全確認（CLEAR_RADIUS を使用）
        path_clear = not is_path_blocked(curr_x, curr_y, goal_x, goal_y, 
                                         OBSTACLE_POS[0], OBSTACLE_POS[1], CLEAR_RADIUS)
        
        if d_to_wp < 30 or path_clear:
            print("<<< 回避完了！")
            avoid_state["is_active"] = False
            return goal_x, goal_y, False
        return tx, ty, True

# --- 4. toioハンドラ ---
def position_handler(id_info):
    global current_x, current_y, current_angle, is_position_received
    if id_info and isinstance(id_info, PositionId):
        current_x = id_info.center.point.x
        current_y = id_info.center.point.y
        current_angle = id_info.center.angle
        is_position_received = True

def notification_handler(payload):
    id_info = IdInformation.is_my_data(payload)
    position_handler(id_info)


# --- 5. メイン処理 ---
async def main():
    print("toioに接続します...")
    async with ToioCoreCube() as cube:
        print("接続完了！")
        await cube.api.id_information.register_notification_handler(notification_handler)
        
        pid_dist = PIDController(DIST_KP, DIST_KI, DIST_KD)
        pid_angle = PIDController(ANGLE_KP, ANGLE_KI, ANGLE_KD)
        
        # ★ここを変更しました★
        print("toioの現在地を取得しています... 好きな場所に置いてください")
        while not is_position_received:
            await asyncio.sleep(0.1)
        
        # 現在地を表示してスタート
        print(f"現在地 ({current_x}, {current_y}) からスタートします！")
        
        # 準備のためのウェイト
        await asyncio.sleep(1)
        print("Go!")

        try:
            while True:
                target_x, target_y, is_avoiding = calculate_target(
                    current_x, current_y, GOAL_POS[0], GOAL_POS[1]
                )

                dx = target_x - current_x
                dy = target_y - current_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                target_rad = math.atan2(dy, dx)
                target_deg = math.degrees(target_rad)
                angle_diff = get_angle_diff(target_deg, current_angle)

                real_dist = math.sqrt((GOAL_POS[0]-current_x)**2 + (GOAL_POS[1]-current_y)**2)
                if real_dist < REACH_THRESHOLD:
                    print("🏆 ゴールに到達しました！")
                    await cube.api.motor.motor_control(0, 0)
                    break

                speed_out = pid_dist.update(distance)
                turn_out = pid_angle.update(angle_diff)

                max_spd = 50 if is_avoiding else 70
                base_speed = max(min(speed_out, max_spd), -max_spd)
                turn_speed = max(min(turn_out, 50), -50)

                left = int(base_speed + turn_speed)
                right = int(base_speed - turn_speed)
                left = max(min(left, 100), -100)
                right = max(min(right, 100), -100)
                
                await cube.api.motor.motor_control(left, right)
                await asyncio.sleep(0.05)

        except KeyboardInterrupt:
            print("停止します")
        finally:
            await cube.api.motor.motor_control(0, 0)
            await cube.api.id_information.unregister_notification_handler(notification_handler)

if __name__ == '__main__':
    asyncio.run(main())