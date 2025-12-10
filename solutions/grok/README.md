# Bear Guardian 🐻

長野市内の熊出没情報をリアルタイムに可視化し、家族の安全を守るWebアプリケーションです。
在宅のITエンジニアが、外出する家族の位置を把握し、熊出没エリアとの重なりを監視できます。

## Prerequisites

- Python 3.8+
- Internet connection (for geocoding services)

## Setup & Installation

1. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **熊出没データの準備**
   ```bash
   python extract_bear_data.py
   ```

3. **アプリケーションの起動**
   ```bash
   streamlit run app.py
   ```

## Data Pipeline

熊出没情報の更新手順：

1. 長野市公式サイトから最新のPDFをダウンロード
2. `data/bear_sightings.pdf` を更新
3. `python extract_bear_data.py` を実行してデータを更新
4. アプリケーションを再起動

## Usage

1. ブラウザで http://localhost:8501 にアクセス
2. サイドバーに現在地を入力（例: "長野市中央通り"）
3. "位置を検索"ボタンをクリック
4. マップ上で熊出没地点を確認
5. 右側の安全情報で注意喚起を確認

## Features

- 🗺️ 熊出没地点の地図表示
- 📍 現在位置との距離計算
- ⚠️ 危険エリアの自動通知
- 📊 出没統計の表示
- 🛡️ 熊遭遇時の安全ガイド

## Architecture

```
solutions/grok/
├── app.py                 # メインStreamlitアプリケーション
├── extract_bear_data.py   # PDFデータ抽出スクリプト
├── requirements.txt       # Python依存関係
├── data/
│   ├── bear_sightings.pdf # 公式熊出没情報PDF
│   └── bear_sightings.csv # 抽出済みデータ
└── README.md             # このファイル
```

## Security Notes

- 位置情報はブラウザ上で処理され、外部サーバーに送信されません
- ジオコーディングはOpenStreetMapのNominatimサービスを使用
- APIレート制限のため、連続使用時は適切な待機時間を設けてください