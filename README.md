# toio-gemini

toioをPythonで操作するための学習用プロジェクトです。`toio-py`ライブラリを使用して、toioコアキューブとの基本的な通信を実装しています。将来的にはGoogleのGemini AIと連携し、より高度な自律制御を目指しています。

## 機能

- **[接続テスト](https://note.com/fp_en_takeshi/n/nd077ec88223d?magazine_key=m3ac3c561928b) (`connect_test.py`)**
  - toioコアキューブのスキャンとBluetooth接続
  - 接続成功時にLEDを赤色に3秒間点灯

- **[位置・角度取得](https://note.com/fp_en_takeshi/n/n4470b3e34b89?magazine_key=m3ac3c561928b) (`1_position.py`)**
  - プレイマット上のtoioコアキューブの位置(x, y)と角度(angle)をリアルタイムで取得し、コンソールに表示します。

- **[P制御による移動](https://note.com/fp_en_takeshi/n/n26f92ca79240?magazine_key=m3ac3c561928b) (`2_p_control.py`)**
  - 指定した目標座標（例：x=200, y=200）に向かって、P制御（比例制御）を用いてtoioコアキューBブを自動で移動させます。

- **[PID制御による移動](https://note.com/fp_en_takeshi/n/nba386874c280?magazine_key=m3ac3c561928b) (`3_pid_control.py`)**
  - 指定した目標座標に向かって、PID制御を用いてtoioコアキューブを自動で移動させます。P制御よりもスムーズな動作が期待できます。

- **[巡回移動](https://note.com/fp_en_takeshi/n/n36b95a49bda7?magazine_key=m3ac3c561928b) (`4_traveling.py`)**
  - 指定した複数の目標座標を順番に巡回します。すべての座標を訪れると停止します。

- **[障害物回避](https://note.com/fp_en_takeshi/n/nbc239d56fa4e?magazine_key=m3ac3c561928b) (`5_obstacle.py`)**
  - 指定した目標座標に向かう途中に仮想的な障害物を検知すると、それを自動で回避してゴールを目指します。

- **[2台同時制御](https://note.com/fp_en_takeshi/n/n2784c121ce6c?magazine_key=m3ac3c561928b) (`6_double_toio_LED.py`)**
  - 2台のtoioコアキューブに同時に接続し、それぞれを異なる色で光らせながら回転させます。`MultipleToioCoreCubes`クラスの使用例です。

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

### PID制御による移動

```bash
uv run python 3_pid_control.py
```
キューブが目標座標に向かって自動で移動します。

### 巡回移動

```bash
uv run python 4_traveling.py
```
キューブが指定された座標を順番に巡回します。

### 障害物回避

```bash
uv run python 5_obstacle.py
```
キューブが障害物を回避しながら目標座標に移動します。

### 2台同時制御

```bash
uv run python 6_double_toio_LED.py
```
2台のキューブがそれぞれ赤と青に光りながら回転します。

## その他

このリポジトリに含まれる`log_graph.png`は、PID制御の挙動を可視化したグラフの一例です。

![PID制御のロググラフ](log_graph.png)

## ライセンス

このプロジェクトはMITライセンスです。