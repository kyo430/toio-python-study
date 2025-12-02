# toio-gemini

toioをPythonで操作するための学習用プロジェクトです。`toio-py`ライブラリを使用して、toioコアキューブとの基本的な通信を実装しています。将来的にはGoogleのGemini AIと連携し、より高度な自律制御を目指しています。

## 機能

- **接続テスト (`connect_test.py`)**
  - toioコアキューブのスキャンとBluetooth接続
  - 接続成功時にLEDを赤色に3秒間点灯

- **位置・角度取得 (`1_position.py`)**
  - プレイマット上のtoioコアキューブの位置(x, y)と角度(angle)をリアルタイムで取得し、コンソールに表示します。

- **P制御による移動 (`2_p_control.py`)**
  - 指定した目標座標（例：x=200, y=200）に向かって、P制御（比例制御）を用いてtoioコアキューBブを自動で移動させます。

## 動作環境

- Python 3.11 以上
- toio プレイマット
- toio-py

## 準備

1. toioコアキューブの電源を入れます。
2. PCのBluetoothを有効にします。
3. 必要なライブラリをインストールします。
   ```bash
   uv sync
   ```

## 実行方法

### 接続テスト

```bash
uv run python connect_test.py
```
スキャンと接続が成功すると、キューブのLEDが赤く点灯します。

### 位置・角度取得

```bash
uv run python 1_position.py
```
キューブをプレイマット上に置くと、位置と角度がコンソールに表示されます。

### P制御による移動

```bash
uv run python 2_p_control.py
```
キューブが目標座標に向かって自動で移動します。


## ライセンス

このプロジェクトはMITライセンスです。