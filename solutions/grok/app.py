import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

# ページ設定
st.set_page_config(page_title="Bear Guardian", page_icon="🐻", layout="wide")

# データ読み込み
@st.cache_data
def load_bear_data():
    df = pd.read_csv('data/bear_sightings.csv')
    # ジオコーディング（住所を緯度経度に変換）
    geolocator = Nominatim(user_agent="bear_guardian")
    df['lat'] = None
    df['lon'] = None

    for idx, row in df.iterrows():
        try:
            # 長野市内の場所をジオコーディング
            location_str = f"{row['area']} {row['location']}, 長野市, 日本"
            location = geolocator.geocode(location_str, timeout=10)
            if location:
                df.at[idx, 'lat'] = location.latitude
                df.at[idx, 'lon'] = location.longitude
            time.sleep(1)  # API制限回避
        except:
            pass

    return df

def create_map(bear_data, user_lat=None, user_lon=None):
    # 長野市の中心座標
    center_lat, center_lon = 36.6513, 138.1811

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # 熊出没地点をマーカーで表示
    for _, row in bear_data.iterrows():
        if pd.notna(row['lat']) and pd.notna(row['lon']):
            popup_text = f"""
            <b>日付:</b> {row['date']}<br>
            <b>時間:</b> {row['time']}<br>
            <b>地区:</b> {row['area']}<br>
            <b>場所:</b> {row['location']}<br>
            <b>詳細:</b> {row['detail']}
            """
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=popup_text,
                icon=folium.Icon(color='red', icon='warning-sign')
            ).add_to(m)

    # ユーザーの位置を表示
    if user_lat and user_lon:
        folium.Marker(
            location=[user_lat, user_lon],
            popup="あなたの位置",
            icon=folium.Icon(color='blue', icon='user')
        ).add_to(m)

        # 危険エリアとの距離を計算して通知
        danger_zones = []
        for _, row in bear_data.iterrows():
            if pd.notna(row['lat']) and pd.notna(row['lon']):
                distance = geodesic((user_lat, user_lon), (row['lat'], row['lon'])).kilometers
                if distance < 1.0:  # 1km以内の場合
                    danger_zones.append({
                        'location': row['location'],
                        'distance': distance,
                        'date': row['date']
                    })

        return m, danger_zones

    return m, []

def main():
    st.title("🐻 Bear Guardian - 家族の安全を守る")
    st.markdown("長野市内の熊出没情報を地図で確認し、家族の安全を確保しましょう")

    # データ読み込み
    bear_data = load_bear_data()

    # サイドバー
    st.sidebar.header("設定")
    user_location = st.sidebar.text_input("現在地を入力（例: 長野市中央通り）", "")

    if st.sidebar.button("位置を検索"):
        if user_location:
            geolocator = Nominatim(user_agent="bear_guardian")
            try:
                location = geolocator.geocode(f"{user_location}, 長野市, 日本")
                if location:
                    st.session_state.user_lat = location.latitude
                    st.session_state.user_lon = location.longitude
                    st.sidebar.success("位置を特定しました")
                else:
                    st.sidebar.error("位置が見つかりません")
            except:
                st.sidebar.error("位置検索エラー")
        else:
            st.sidebar.error("位置を入力してください")

    # メインコンテンツ
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("熊出没マップ")
        user_lat = st.session_state.get('user_lat')
        user_lon = st.session_state.get('user_lon')

        m, danger_zones = create_map(bear_data, user_lat, user_lon)
        st_folium(m, width=700, height=500)

    with col2:
        st.subheader("安全情報")

        if danger_zones:
            st.error("⚠️ 注意: 近くに熊出没地点があります！")
            for zone in danger_zones:
                st.warning(f"📍 {zone['location']} ({zone['distance']:.1f}km) - {zone['date']}")
        else:
            st.success("✅ 現在位置周辺は安全です")

        st.subheader("熊遭遇時の対応")
        st.info("""
        **共存を前提とした安全対策:**
        - 大きな声を出して存在をアピール
        - 後ずさりしながらゆっくり離れる
        - 走って逃げない（襲われる原因に）
        - 鈴やラジオで音を出す
        """)

        st.subheader("統計情報")
        total_sightings = len(bear_data)
        recent_sightings = len(bear_data[pd.to_datetime(bear_data['date'], errors='coerce') > pd.Timestamp.now() - pd.DateOffset(months=1)])

        st.metric("総出没件数", total_sightings)
        st.metric("最近1ヶ月の出没", recent_sightings)

if __name__ == "__main__":
    main()