import pandas as pd
from geopy.geocoders import Nominatim
import time
import os

def geocode_bear_data():
    """熊出没データを事前にジオコーディングして保存"""
    csv_path = 'data/bear_sightings.csv'
    geocoded_csv_path = 'data/bear_sightings_geocoded.csv'

    # 既にジオコーディング済みのファイルが存在する場合はスキップ
    if os.path.exists(geocoded_csv_path):
        print("ジオコーディング済みファイルが存在します。")
        return pd.read_csv(geocoded_csv_path)

    df = pd.read_csv(csv_path)
    geolocator = Nominatim(user_agent="bear_guardian")

    print(f"{len(df)}件のデータをジオコーディング中...")

    # ジオコーディング済みのデータを確認
    if 'lat' not in df.columns:
        df['lat'] = None
    if 'lon' not in df.columns:
        df['lon'] = None

    success_count = 0
    for idx, row in df.iterrows():
        # 既にジオコーディング済みの場合はスキップ
        if pd.notna(row.get('lat')) and pd.notna(row.get('lon')):
            success_count += 1
            continue

        try:
            # 長野市内の場所をジオコーディング
            location_str = f"{row['area']} {row['location']}, 長野市, 日本"
            print(f"ジオコーディング中: {location_str}")
            location = geolocator.geocode(location_str, timeout=10)
            if location:
                df.at[idx, 'lat'] = location.latitude
                df.at[idx, 'lon'] = location.longitude
                success_count += 1
                print(f"✓ 成功: {location.latitude}, {location.longitude}")
            else:
                print(f"✗ 失敗: 位置が見つかりません")
        except Exception as e:
            print(f"✗ エラー: {e}")

        # API制限を避けるため少し待機
        time.sleep(1)

        # 進捗表示
        if (idx + 1) % 10 == 0:
            print(f"進捗: {idx + 1}/{len(df)} 件処理済み")

    # 結果を保存
    df.to_csv(geocoded_csv_path, index=False)
    print(f"ジオコーディング完了。{success_count}/{len(df)}件の位置情報を取得しました。")
    print(f"結果を {geocoded_csv_path} に保存しました。")

    return df

if __name__ == "__main__":
    geocode_bear_data()