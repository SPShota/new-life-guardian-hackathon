#!/usr/bin/env python3
"""
KumaSafe - PDF熊出没情報抽出スクリプト

長野市が公開している熊目撃情報PDFからデータを抽出し、
JSON形式に変換するスクリプト

使用方法:
    python extract_pdf_data.py --pdf <PDFファイルパス> --output <出力JSONパス>
    
    または、URLから直接ダウンロードして処理:
    python extract_pdf_data.py --url <PDFのURL> --output <出力JSONパス>
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import pdfplumber
    import requests
except ImportError:
    print("必要なライブラリをインストールしてください:")
    print("  pip install pdfplumber requests")
    sys.exit(1)


# 長野市内の主要地域と概算座標（ジオコーディングの代替）
NAGANO_LOCATIONS = {
    "篠ノ井": (36.5823, 138.1456),
    "松代": (36.5612, 138.2034),
    "若穂": (36.6234, 138.2345),
    "川中島": (36.5956, 138.1623),
    "信更": (36.5345, 138.0876),
    "戸隠": (36.7523, 138.0654),
    "七二会": (36.6012, 138.0234),
    "信州新町": (36.5234, 138.0123),
    "中条": (36.5456, 138.0345),
    "豊野": (36.6845, 138.2567),
    "大岡": (36.4523, 138.0234),
    "芋井": (36.6734, 138.1456),
    "鬼無里": (36.6234, 137.9567),
    "安茂里": (36.6345, 138.1567),
    "長野駅": (36.6433, 138.1889),
    "善光寺": (36.6589, 138.1831),
    "飯綱": (36.7234, 138.1345),
    "牟礼": (36.7456, 138.1567),
    "小川": (36.6123, 138.0345),
    "浅川": (36.6734, 138.1789),
    "三輪": (36.6512, 138.2012),
    "柳原": (36.6645, 138.2234),
    "古里": (36.6756, 138.2456),
    "稲田": (36.6534, 138.1234),
    "小松原": (36.5734, 138.1234),
    "布施": (36.5789, 138.1345),
    "更北": (36.5867, 138.1567),
    # デフォルト（長野市中心部）
    "default": (36.6513, 138.1810)
}


def download_pdf(url: str, output_path: str) -> str:
    """PDFをダウンロード"""
    print(f"PDFをダウンロード中: {url}")
    response = requests.get(url)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    print(f"ダウンロード完了: {output_path}")
    return output_path


def get_coordinates(location: str) -> tuple[float, float]:
    """地名から概算座標を取得"""
    for key, coords in NAGANO_LOCATIONS.items():
        if key in location:
            return coords
    return NAGANO_LOCATIONS["default"]


def estimate_danger_level(text: str, sighting_type: str) -> int:
    """危険度を推定"""
    danger = 3  # デフォルト
    
    if sighting_type == "痕跡":
        danger = 2
    
    # 危険度を上げる要因
    if "親子" in text or "子熊" in text:
        danger = min(5, danger + 1)  # 親子連れは危険
    if "住宅" in text or "通学" in text or "学校" in text:
        danger = min(5, danger + 1)  # 人が多い場所
    if "成獣" in text and "複数" in text:
        danger = min(5, danger + 1)  # 複数頭
        
    return danger


def extract_data_from_pdf(pdf_path: str) -> list[dict]:
    """PDFからデータを抽出"""
    sightings = []
    
    print(f"PDFを解析中: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # テーブルデータの抽出を試みる
            tables = page.extract_tables()
            
            for table in tables:
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    
                    # 行データの解析（PDFのフォーマットに依存）
                    try:
                        # 日付パターンを検索
                        date_pattern = r'(\d{1,2})[/月](\d{1,2})'
                        time_pattern = r'(\d{1,2}):(\d{2})'
                        
                        row_text = " ".join(str(cell) for cell in row if cell)
                        
                        date_match = re.search(date_pattern, row_text)
                        time_match = re.search(time_pattern, row_text)
                        
                        if date_match:
                            month, day = date_match.groups()
                            year = datetime.now().year
                            date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                            
                            time_str = "12:00"  # デフォルト
                            if time_match:
                                hour, minute = time_match.groups()
                                time_str = f"{int(hour):02d}:{minute}"
                            
                            # 場所の抽出
                            location = "長野市"
                            for cell in row:
                                if cell and "長野" in str(cell):
                                    location = str(cell).strip()
                                    break
                            
                            # 種類の判定
                            sighting_type = "目撃"
                            if "痕跡" in row_text or "足跡" in row_text or "糞" in row_text:
                                sighting_type = "痕跡"
                            
                            lat, lng = get_coordinates(location)
                            
                            sighting = {
                                "id": len(sightings) + 1,
                                "date": date_str,
                                "time": time_str,
                                "location": location,
                                "lat": lat,
                                "lng": lng,
                                "type": sighting_type,
                                "description": row_text[:100],
                                "danger_level": estimate_danger_level(row_text, sighting_type)
                            }
                            sightings.append(sighting)
                            
                    except Exception as e:
                        print(f"行の解析エラー: {e}")
                        continue
            
            # テーブルが取得できない場合はテキストから抽出
            if not tables:
                lines = text.split("\n")
                for line in lines:
                    date_pattern = r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})'
                    match = re.search(date_pattern, line)
                    if match:
                        year, month, day = match.groups()
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                        
                        lat, lng = get_coordinates(line)
                        sighting_type = "痕跡" if "痕跡" in line else "目撃"
                        
                        sighting = {
                            "id": len(sightings) + 1,
                            "date": date_str,
                            "time": "12:00",
                            "location": line[:50],
                            "lat": lat,
                            "lng": lng,
                            "type": sighting_type,
                            "description": line,
                            "danger_level": estimate_danger_level(line, sighting_type)
                        }
                        sightings.append(sighting)
    
    print(f"抽出完了: {len(sightings)}件のデータを取得")
    return sightings


def save_to_json(sightings: list[dict], output_path: str):
    """JSONファイルとして保存"""
    data = {
        "metadata": {
            "source": "長野市 クマ目撃等情報",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "description": "長野市内における熊の目撃・痕跡情報",
            "extraction_date": datetime.now().isoformat()
        },
        "sightings": sightings
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSONファイルを保存しました: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="長野市熊出没情報PDFからデータを抽出"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="入力PDFファイルのパス"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.city.nagano.nagano.jp/documents/3071/kuma20251031.pdf",
        help="PDFのURL（デフォルト: 長野市公式）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/bear_sightings.json",
        help="出力JSONファイルのパス"
    )
    
    args = parser.parse_args()
    
    # 出力ディレクトリを作成
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # PDFファイルの準備
    if args.pdf:
        pdf_path = args.pdf
    else:
        # URLからダウンロード
        pdf_path = str(output_path.parent / "temp_bear_data.pdf")
        try:
            download_pdf(args.url, pdf_path)
        except Exception as e:
            print(f"PDFのダウンロードに失敗しました: {e}")
            print("サンプルデータを使用します")
            return
    
    # データ抽出
    try:
        sightings = extract_data_from_pdf(pdf_path)
        
        if sightings:
            save_to_json(sightings, str(output_path))
        else:
            print("データを抽出できませんでした。PDFのフォーマットを確認してください。")
            print("サンプルデータを使用することを推奨します。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("サンプルデータを使用してください。")


if __name__ == "__main__":
    main()
