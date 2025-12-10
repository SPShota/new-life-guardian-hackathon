# Bear Guardian (gpt-5.1-codex-max)

在宅の夫が、外出する家族の安全を「共存」を前提に見守るための軽量MVPです。長野市公開PDFの目撃情報を取り込み、地図・テキストで共有できる形にまとめます。

## 主要コンポーネント
- PDF/モックデータ取り込み: 長野市公開PDFをダウンロードし、表形式を抽出。失敗時はバンドルしたモックCSVにフォールバック。
- 構造化/可視化: CSV化した目撃情報を folium で地図HTML化、テキストダイジェストで家族と即共有。
- 共存アクション: 鈴/ライトなど「近づかない・近づけない」ための推奨をダイジェストに常時付記。

## Prerequisites
- Python 3.10+
- ネットワーク接続（PDF取得時のみ）

## セットアップ
```bash
pip install -r requirements.txt
```

## データパイプライン
1. PDF取得: `python pipeline.py fetch`
2. 構造化CSV生成: `python pipeline.py parse`
3. 地図HTML生成: `python pipeline.py map`
4. まとめて実行: `python pipeline.py pipeline`  
   - `--no-fetch` 既存PDFを使用
   - `--no-map` 地図生成スキップ
   - `--no-digest` ダイジェスト生成スキップ

出力物:
- `data/processed/sightings.csv`: 構造化された目撃リスト
- `outputs/sightings_map.html`: 目撃ポイントの地図（ローカルで開く）
- `outputs/digest.txt`: 最新目撃・頻出エリアと共存アクションのテキスト

## 使い方（最短ルート）
```bash
# 1. 依存インストール
pip install -r requirements.txt

# 2. 一括パイプライン
python pipeline.py pipeline

# 3. 結果を確認
open outputs/sightings_map.html  # macOS例
cat outputs/digest.txt
```

## データ更新フロー
- 長野市が新しいPDFを公開 → `pipeline.py fetch` で取得
- 解析失敗や形式が違う場合 → `data/sample_sightings.csv` を編集/更新して使う
- 緯度経度が無い場合 → サンプル同様に手動で補完すれば地図生成可能

## 運用/拡張のヒント
- 通知: digest.txt を Slack/LINE webhook へ送るシェル/簡易Pythonを追加
- 安全ルート: `sightings.csv` を Google Maps API や OpenRouteService へ渡し、回避ルート算出
- アラートポリシー: 時間帯×エリアで閾値を決め、早朝/夕方の外出時のみ通知

## 共存・倫理の考慮
- 「避ける」「存在を知らせる」を優先し、威嚇や駆除を前提とした処理は行わない。
- 目撃データは家族内共有を基本とし、誤報拡散を避けるため外部SNSへの自動投稿はデフォルト無効。
