# BearGuardian - 家族の安全を守る熊出没情報監視システム

## 概要

BearGuardianは、長野市の熊出没情報をリアルタイムで監視し、外出する家族の安全を守るためのWebアプリケーションです。在宅でリモートワークをする夫が、外出する家族の位置情報と熊出没情報を一元管理し、危険エリアへの接近を検知して通知します。

## 主な機能

- 🗺️ **地図上での熊出没情報の可視化**: 長野市の熊出没情報を地図上に表示
- 📍 **家族の位置情報追跡**: 家族の現在位置をリアルタイムで表示
- ⚠️ **危険エリア接近通知**: 家族が熊出没エリア（500m半径）に近づいた際に自動通知
- 🔄 **リアルタイム更新**: WebSocketを使用したリアルタイム情報更新
- 📊 **距離計算**: 新居からの距離を自動計算して表示

## Prerequisites

### 必要なランタイム

#### 方法1: Dockerを使用する場合（推奨）
- **Docker** (version 20.10以上)
- **Docker Compose** (version 2.0以上)

#### 方法2: ローカル環境で実行する場合
- **Python** 3.11以上
- **Node.js** 18以上
- **npm** (Node.jsに含まれる)

### APIキー等

本プロトタイプでは**外部APIキーは不要**です。
- 地図表示: OpenStreetMapを使用（APIキー不要）
- データソース: 長野市の熊出没情報PDF（公開データ）

## Setup & Installation

### 方法1: Docker Composeを使用（推奨）

1. リポジトリをクローンまたはダウンロードします。

2. `solutions/composer` ディレクトリに移動します：
```bash
cd solutions/composer
```

3. Docker Composeで起動します：
```bash
docker-compose up --build
```

4. ブラウザで以下のURLにアクセスします：
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000
   - APIドキュメント: http://localhost:8000/docs

### 方法2: ローカル環境で実行

#### バックエンドのセットアップ

1. バックエンドディレクトリに移動：
```bash
cd solutions/composer/backend
```

2. 仮想環境を作成（推奨）：
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 依存関係をインストール：
```bash
pip install -r requirements.txt
```

4. モックデータを生成：
```bash
python3 pdf_parser.py
```

5. サーバーを起動：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### フロントエンドのセットアップ

1. 新しいターミナルでフロントエンドディレクトリに移動：
```bash
cd solutions/composer/frontend
```

2. 依存関係をインストール：
```bash
npm install
```

3. 開発サーバーを起動：
```bash
npm start
```

4. ブラウザで http://localhost:3000 にアクセスします。

## Data Pipeline

### 熊出没情報の取り込み

1. **PDFからのデータ抽出**:
   - 長野市の熊出没情報PDF（[リンク](https://www.city.nagano.nagano.jp/documents/3071/kuma20251031.pdf)）をダウンロード
   - `backend/pdf_parser.py` を使用してPDFを解析（実際のPDF構造に応じて調整が必要）
   - 構造化データ（JSON）として `data/bear_sightings.json` に保存

2. **モックデータの使用**:
   - 現在は `pdf_parser.py` がモックデータを生成します
   - 実際のPDFが利用可能になったら、`parse_nagano_bear_pdf()` 関数を実装してください

3. **データ更新手順**:
   ```bash
   # バックエンドディレクトリで実行
   python3 pdf_parser.py
   ```
   - または、API経由で新しい情報を追加：
   ```bash
   curl -X POST http://localhost:8000/api/bear-sightings \
     -H "Content-Type: application/json" \
     -d '{
       "id": "6",
       "date": "2025-11-01",
       "location": "長野市新居付近",
       "latitude": 36.6513,
       "longitude": 138.1810,
       "description": "クマ1頭を目撃"
     }'
   ```

### 家族の位置情報

- 現在はモックデータとして実装されています
- 実際の運用では、スマートフォンアプリから位置情報を送信する必要があります
- APIエンドポイント: `POST /api/family-locations`

## Usage

### 基本的な使い方

1. **アプリケーションを起動**後、ブラウザで http://localhost:3000 にアクセス

2. **地図の操作**:
   - 地図上で🐻マーカーをクリックすると、熊出没情報の詳細が表示されます
   - 赤い円は500mの危険エリアを示します
   - 🏠マーカーは新居の位置です
   - 🟢マーカーは家族の現在位置です

3. **サイドバーの使用**:
   - 「熊出没情報」タブ: すべての目撃情報を一覧表示
   - 「家族の位置」タブ: 家族の位置情報を管理
   - デモ用に「位置情報シミュレーション」を有効にすると、5秒ごとに位置が更新されます

4. **通知の確認**:
   - 家族が危険エリアに近づくと、右上に通知が表示されます
   - 通知をクリックすると閉じることができます

### APIの使用

#### 熊出没情報の取得
```bash
GET http://localhost:8000/api/bear-sightings
```

#### 新しい熊出没情報の追加
```bash
POST http://localhost:8000/api/bear-sightings
Content-Type: application/json

{
  "id": "7",
  "date": "2025-11-02",
  "location": "長野市権堂町",
  "latitude": 36.6580,
  "longitude": 138.1920,
  "description": "クマの足跡を確認"
}
```

#### 家族の位置情報の更新
```bash
POST http://localhost:8000/api/family-locations
Content-Type: application/json

{
  "id": "1",
  "name": "妻",
  "latitude": 36.6550,
  "longitude": 138.1850,
  "timestamp": "2025-11-01T10:00:00Z"
}
```

#### WebSocket接続
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('受信:', message);
};
```

## アーキテクチャ

```
BearGuardian
├── backend/          # FastAPI バックエンド
│   ├── main.py       # APIサーバー
│   ├── pdf_parser.py # PDF解析ツール
│   └── requirements.txt
├── frontend/         # React フロントエンド
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   ├── MapView.js
│   │   │   ├── Sidebar.js
│   │   │   └── NotificationPanel.js
│   │   └── hooks/
│   │       └── useWebSocket.js
│   └── package.json
├── data/             # データファイル
│   └── bear_sightings.json
└── docker-compose.yml
```

## トラブルシューティング

### ポートが既に使用されている場合

- バックエンドのポート（8000）を変更する場合:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8001
  ```
  その後、`frontend/src/config.js` の `API_BASE_URL` を更新してください。

- フロントエンドのポート（3000）を変更する場合:
  ```bash
  PORT=3001 npm start
  ```

### Dockerで起動しない場合

- DockerとDocker Composeが正しくインストールされているか確認:
  ```bash
  docker --version
  docker-compose --version
  ```

- ログを確認:
  ```bash
  docker-compose logs
  ```

### 地図が表示されない場合

- ブラウザのコンソールでエラーを確認
- LeafletのCSSが正しく読み込まれているか確認
- インターネット接続を確認（OpenStreetMapのタイルが必要）

## 開発者向け情報

### テスト

- バックエンドAPIのテスト:
  ```bash
  curl http://localhost:8000/api/bear-sightings
  ```

- APIドキュメント:
  http://localhost:8000/docs でSwagger UIが利用可能

### コードの構造

- **バックエンド**: FastAPIを使用したRESTful API + WebSocket
- **フロントエンド**: React + Leaflet（地図ライブラリ）
- **データストレージ**: JSONファイル（プロトタイプ段階）

## ライセンス

このプロジェクトはハッカソン用のプロトタイプです。

## お問い合わせ

問題や質問がある場合は、GitHubのIssuesで報告してください。
