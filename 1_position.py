import asyncio
from toio import *

# --- 1. 通知を受け取る「受付係」の関数（ハンドラ） ---
def position_handler(id_info):
    # id_infoが None の場合は何もしない
    if id_info is None:
        return

    # 1. 座標情報 (PositionId) の場合
    if isinstance(id_info, PositionId):
        # 修正ポイント: center の中にある point や angle を参照します
        x = id_info.center.point.x
        y = id_info.center.point.y
        angle = id_info.center.angle
        
        print(f"現在位置: X={x:4d}, Y={y:4d}, 角度={angle:3d}度")

    # 2. スタンダードID (StandardId) の場合
    elif isinstance(id_info, StandardId):
        print(f"Standard IDを検知: {id_info.value}")
    
    # 3. 読み取りミス (PositionIdMissed) の場合
    elif isinstance(id_info, PositionIdMissed):
        print("マットから外れました (読み取りエラー)")


# toioから送られてくる生データ(payload)を受け取り、解析してposition_handlerに渡す関数
def notification_handler(payload: bytearray):
    # 生データを解析してオブジェクトにする
    id_info = IdInformation.is_my_data(payload)
    
    # 解析結果を処理用の関数に渡す
    position_handler(id_info)


# --- 2. メイン処理 ---
async def main():
    print("toioに接続します...")
    async with ToioCoreCube() as cube:
        print("接続完了！toioをマットの上に置いてください。")
        print("手で動かすと、座標がリアルタイムで表示されます。")
        print("(Ctrl+C で終了します)")

        # ハンドラを登録
        await cube.api.id_information.register_notification_handler(notification_handler)

        try:
            # プログラムが終了しないように待機し続ける
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n終了操作を検知しました。")
        finally:
            # ハンドラの登録解除
            await cube.api.id_information.unregister_notification_handler(notification_handler)
            print("接続を切断します。")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass