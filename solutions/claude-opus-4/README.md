# 🐻 KumaSafe - 熊出没回避・共存システム

**「熊を傷つけない、出会わない」**

KumaSafeは、長野市における熊の出没情報を可視化し、家族の安全を守るためのシステムです。
駆除ではなく「回避」に特化し、熊との共存を前提としたソリューションを提供します。

![コンセプト](https://img.shields.io/badge/concept-共存-green)
![ライセンス](https://img.shields.io/badge/license-MIT-blue)

## 📋 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Data Pipeline](#data-pipeline)
- [Usage](#usage)
- [API Reference](#api-reference)

## 概要

2週間後に長野市への引越しを控えた家族のために開発された、熊出没情報の可視化・警告システムです。
リモートワークの夫が自宅から、外出する妻と子供の安全を見守ることができます。

### 設計思想

- **回避優先**: 熊を傷つけるのではなく、出会わないことを最優先
- **情報の力**: 正確な情報提供により、適切な判断を支援
- **共存の哲学**: 熊の生態を理解し、互いの領域を尊重

## 主な機能

### 🗺️ 熊出没マップ
- 長野市内の熊目撃・痕跡情報をマップ上に表示
- 危険度に応じたアイコン表示（🐻目撃 / 🐾痕跡）
- 時系列での情報確認

### 🔍 安全チェック機能
- 任意の地点（緯度・経度）の安全性を評価
- 半径2km以内の目撃情報を検索
- リスクレベル（低/中/高）の判定
- 時間帯に応じた追加警告（早朝・夕方は危険）

### 📱 LINE通知連携
- 新規目撃情報をLINE Notifyで即座に通知
- 家族全員でリアルタイムに情報共有

### 📚 共存ガイド
- 熊との遭遇を防ぐためのヒント
- 万が一遭遇した場合の対処法
- 共存の哲学と生態理解

## Prerequisites

### 必須
- Python 3.11以上
- Node.js 18以上
- npm または yarn

### オプション
- Docker & Docker Compose（コンテナ実行時）
- LINE Notifyトークン（通知機能使用時）

## Setup & Installation

### 方法1: ローカル実行（推奨）

```bash
# リポジトリのクローン
cd solutions/claude-opus-4

# バックエンドのセットアップ
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# バックエンド起動
uvicorn app.main:app --reload --port 8000
```

別のターミナルで:

```bash
# フロントエンドのセットアップ
cd frontend
npm install

# フロントエンド起動
npm run dev
```

### 方法2: Docker Compose

```bash
cd solutions/claude-opus-4
docker-compose up --build
```

### アクセス

- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

## Data Pipeline

### データソース

長野市が公開している熊目撃情報PDF:
https://www.city.nagano.nagano.jp/documents/3071/kuma20251031.pdf

### データ更新手順

#### 1. PDFからの自動抽出（推奨）

```bash
cd scripts
python extract_pdf_data.py --url "https://www.city.nagano.nagano.jp/documents/3071/kuma20251031.pdf" --output ../data/bear_sightings.json
```

#### 2. 手動でPDFを指定

```bash
python extract_pdf_data.py --pdf /path/to/downloaded.pdf --output ../data/bear_sightings.json
```

#### 3. データ形式

`data/bear_sightings.json`:

```json
{
  "metadata": {
    "source": "長野市 クマ目撃等情報",
    "last_updated": "2025-10-31"
  },
  "sightings": [
    {
      "id": 1,
      "date": "2025-04-15",
      "time": "06:30",
      "location": "長野市篠ノ井布施高田",
      "lat": 36.5823,
      "lng": 138.1456,
      "type": "目撃",
      "description": "成獣1頭、山林から農地へ移動",
      "danger_level": 3
    }
  ]
}
```

### 定期更新の自動化（オプション）

crontabで定期実行を設定:

```bash
# 毎日午前6時にデータを更新
0 6 * * * cd /path/to/kumasafe/scripts && python extract_pdf_data.py
```

## Usage

### 1. マップ確認

1. ブラウザで http://localhost:3000 にアクセス
2. マップ上の🐻（目撃）や🐾（痕跡）アイコンをクリックして詳細を確認
3. 📍ボタンで現在地を取得

### 2. 安全チェック

1. サイドバーの「安全チェック」に緯度・経度を入力
2. 「この地点をチェック」をクリック
3. リスクレベルと推奨事項を確認

### 3. LINE通知設定

1. [LINE Notify](https://notify-bot.line.me/my/) でトークンを取得
2. サイドバーの「LINE通知設定」にトークンを入力
3. 「テスト通知を送信」で動作確認

### 4. 共存ガイド

1. 「共存ガイド」タブをクリック
2. 遭遇防止のヒント、対処法を確認

## API Reference

### GET /api/sightings
熊出没情報一覧を取得

**Query Parameters:**
- `days` (optional): 過去N日間に絞り込む
- `danger_level` (optional): 最小危険度でフィルタ

### POST /api/safety-check
指定地点の安全性をチェック

**Request Body:**
```json
{
  "lat": 36.6513,
  "lng": 138.1810,
  "radius_km": 2.0
}
```

### GET /api/statistics
統計情報を取得

### GET /api/coexistence-tips
共存ガイドを取得

### POST /api/notify/line
LINE通知を送信

**Request Body:**
```json
{
  "token": "YOUR_LINE_NOTIFY_TOKEN",
  "message": "通知メッセージ"
}
```

## 技術スタック

| レイヤー | 技術 | 選定理由 |
|---------|------|----------|
| Frontend | React + TypeScript + Vite | 高速開発、型安全性 |
| Map | Leaflet + react-leaflet | 軽量、OSS、カスタマイズ性 |
| Backend | FastAPI | 高速、自動ドキュメント生成 |
| Data | JSON + SQLite | 軽量、ローカル運用可能 |
| Notification | LINE Notify | 日本で普及、無料 |
| Container | Docker | 環境再現性 |

## ライセンス

MIT License

---

🐻 **熊との共存を目指して** 🌲

このシステムは、熊を害獣として排除するのではなく、
適切な距離を保ちながら共存することを目指しています。
