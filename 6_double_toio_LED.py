import asyncio
from toio import *

# --- 個々のtoioの動きを定義する関数 ---
async def spin_task(cube, name, color):
    """ 指定した色に光って、3回回転するタスク """
    print(f"[{name}] タスク開始")
    
    # LEDを点灯（時間指定0msでずっと点灯）
    await cube.api.indicator.turn_on(
        IndicatorParam(duration_ms=0, color=color)
    )
    
    try:
        for i in range(3):
            print(f"[{name}] 回転 {i+1}/3")
            # 50の速度で2秒間、逆方向に回してその場で回転
            await cube.api.motor.motor_control(50, -50)
            await asyncio.sleep(2)
            
            # 1秒停止
            await cube.api.motor.motor_control(0, 0)
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"[{name}] エラー: {e}")

# --- メイン処理 ---
async def main():
    print("2台のtoioを探して接続します...(電源を入れて待機してください)")

    # ★ここがポイント！
    # cubes=2 を指定することで、2台見つかるまでスキャン・接続を自動で行います。
    # 接続されたキューブはリスト形式 (cubes[0], cubes[1]) で受け取れます。
    async with MultipleToioCoreCubes(cubes=2) as cubes:
        print("2台接続完了！")
        
        # asyncio.gather を使って、2つのタスクを「同時に」実行します
        # これを使わないと、1台目が終わってから2台目が動くことになってしまいます
        await asyncio.gather(
            spin_task(cubes[0], "No.1", Color(255, 0, 0)), # 赤
            spin_task(cubes[1], "No.2", Color(0, 0, 255))  # 青
        )
        
    print("切断しました")

if __name__ == "__main__":
    asyncio.run(main())