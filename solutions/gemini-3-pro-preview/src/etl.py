import json
import random
from datetime import datetime

# NOTE: 実運用では pdfplumber や tabula-py を使用してPDFからテキストを抽出します。
# import pdfplumber

def extract_data_from_pdf(pdf_path):
    """
    長野市の熊出没情報PDFからデータを抽出する関数のモック
    実際には正規表現等で日付、場所、内容をパースし、
    Google Geocoding API等を用いて住所から緯度経度へ変換する処理が入ります。
    """
    print(f"Processing {pdf_path}...")
    
    # 抽出されたデータのイメージ
    extracted_data = [
        {
            "id": 101,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "10:00",
            "location": "長野市大字長野（善光寺北側）",
            "lat": 36.6600 + (random.random() - 0.5) * 0.01,
            "lng": 138.1900 + (random.random() - 0.5) * 0.01,
            "details": "目撃情報あり。注意してください。",
            "status": "warning"
        }
    ]
    return extracted_data

def save_to_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {output_path}")

if __name__ == "__main__":
    # PDFパス（ダミー）
    pdf_path = "kuma_20251031.pdf"
    
    # データの生成
    data = extract_data_from_pdf(pdf_path)
    
    # モックデータとマージしたり、DBに入れたりする処理がここにきます
    # 今回はサンプルとして標準出力のみ
    print(json.dumps(data, indent=2, ensure_ascii=False))
