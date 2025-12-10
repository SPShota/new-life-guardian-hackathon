"""
長野市の熊出没情報PDFを解析して構造化データに変換
"""
import pdfplumber
import json
import re
from typing import List, Dict
from datetime import datetime

def parse_nagano_bear_pdf(pdf_path: str) -> List[Dict]:
    """
    PDFから熊出没情報を抽出
    
    注意: 実際のPDFの構造に応じて調整が必要です
    ここではモックデータ生成のためのヘルパー関数を提供
    """
    sightings = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # PDFのテキストを解析（実際のPDF構造に応じて調整）
                    # ここでは簡易的なパターンマッチングの例を示す
                    lines = text.split('\n')
                    for line in lines:
                        # 日付パターンを探す（例: 2025/10/31）
                        date_match = re.search(r'(\d{4})[/年](\d{1,2})[/月](\d{1,2})', line)
                        if date_match:
                            # 位置情報を探す（実際のPDFに応じて調整）
                            # ここではモックデータ生成のためのプレースホルダー
                            pass
    except Exception as e:
        print(f"PDF解析エラー: {e}")
    
    return sightings

def generate_mock_sightings() -> List[Dict]:
    """
    モックデータを生成（実際のPDFが利用できない場合）
    長野市の熊出没情報のサンプルデータ
    """
    return [
        {
            "id": "1",
            "date": "2025-10-31",
            "location": "長野市若里1丁目付近",
            "latitude": 36.6513,
            "longitude": 138.1810,
            "description": "クマ1頭を目撃。人への危害なし。"
        },
        {
            "id": "2",
            "date": "2025-10-28",
            "location": "長野市権堂町付近",
            "latitude": 36.6580,
            "longitude": 138.1920,
            "description": "クマの足跡を確認。"
        },
        {
            "id": "3",
            "date": "2025-10-25",
            "location": "長野市南長野付近",
            "latitude": 36.6400,
            "longitude": 138.1750,
            "description": "クマ1頭を目撃。追い払い実施。"
        },
        {
            "id": "4",
            "date": "2025-10-20",
            "location": "長野市鶴賀付近",
            "latitude": 36.6650,
            "longitude": 138.1900,
            "description": "クマの目撃情報。"
        },
        {
            "id": "5",
            "date": "2025-10-15",
            "location": "長野市新田町付近",
            "latitude": 36.6450,
            "longitude": 138.1850,
            "description": "クマ1頭を目撃。人への危害なし。"
        }
    ]

if __name__ == "__main__":
    # モックデータを生成して保存
    import os
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    sightings = generate_mock_sightings()
    output_path = os.path.join(data_dir, "bear_sightings.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sightings, f, ensure_ascii=False, indent=2)
    
    print(f"モックデータを生成しました: {output_path}")
    print(f"件数: {len(sightings)}")
