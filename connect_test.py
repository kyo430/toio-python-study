import asyncio
from toio import *

# 接続したいtoioのBluetoothアドレスを指定します。
# 未指定の場合、最初に見つかったtoioに接続します。
TOIO_ADDRESS = None 

async def main():
    print("toioコアキューブをスキャン中...")
    try:
        # toioを探して接続します
        async with ToioCoreCube() as cube:

            # 接続が成功したら、LEDを赤く点灯させます
            await cube.api.indicator.turn_on(
                IndicatorParam(duration_ms=3000, color=Color(r=255, g=0, b=0))
                )
            print("LEDを赤色に点灯させました。")

            await asyncio.sleep(1)

    except Exception as e:
        print(f"接続エラーが発生しました: {e}")
        print("toioの電源が入っているか、BluetoothがONになっているか確認してください。")

if __name__ == '__main__':
    # toio-pyはasyncioを使用します
    asyncio.run(main())