import pdfplumber
import pandas as pd
import re

def extract_bear_data(pdf_path):
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if len(table) > 1 and '番号' in str(table[0]):
                    for row in table[1:]:  # ヘッダーをスキップ
                        if len(row) >= 7:
                            no = row[0] if row[0] else ''
                            date_str = row[1] if row[1] else ''
                            time_str = row[2] if row[2] else ''
                            area = row[3] if row[3] else ''
                            location = row[4] if row[4] else ''
                            category = row[5] if row[5] else ''
                            detail = row[6] if row[6] else ''
                            # 日付をYYYY/MM/DD形式に変換
                            if date_str and '月' in date_str and '日' in date_str:
                                try:
                                    parts = date_str.replace('月', '/').replace('日', '').split('/')
                                    month = int(parts[0])
                                    day = int(parts[1])
                                    full_date = f"2025/{month:02d}/{day:02d}"
                                except:
                                    full_date = date_str
                            else:
                                full_date = date_str
                            data.append({
                                'no': no,
                                'date': full_date,
                                'time': time_str,
                                'area': area,
                                'location': location,
                                'category': category,
                                'detail': detail
                            })
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = extract_bear_data('data/bear_sightings.pdf')
    print(df.head(10))
    df.to_csv('data/bear_sightings.csv', index=False)