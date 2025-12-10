"""
KumaSafe - 熊出没回避・共存システム
バックエンドAPI

「熊を傷つけない、出会わない」をモットーに、
情報の力で家族を守るシステム
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time
import json
import os
import httpx

app = FastAPI(
    title="KumaSafe API",
    description="熊出没情報を提供し、家族の安全を守るAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データファイルパス
# Docker環境: /app/data, ローカル環境: ../data (backend/から見て)
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data"))
# Docker環境用のフォールバック
if not os.path.exists(DATA_DIR):
    DATA_DIR = "/app/data"
SIGHTINGS_FILE = os.path.join(DATA_DIR, "bear_sightings.json")

# 起動時のログ
print(f"[KumaSafe] DATA_DIR: {DATA_DIR}")
print(f"[KumaSafe] SIGHTINGS_FILE: {SIGHTINGS_FILE}")
print(f"[KumaSafe] File exists: {os.path.exists(SIGHTINGS_FILE)}")


# モデル定義
class BearSighting(BaseModel):
    id: int
    date: str
    time: str
    location: str
    lat: float
    lng: float
    type: str  # "目撃" or "痕跡"
    description: str
    danger_level: int  # 1-5


class SafetyCheck(BaseModel):
    lat: float
    lng: float
    radius_km: float = 2.0


class SafetyResponse(BaseModel):
    is_safe: bool
    risk_level: str  # "low", "medium", "high"
    nearby_sightings: list
    recommendations: list[str]
    time_warning: Optional[str] = None


class LineNotifyRequest(BaseModel):
    token: str
    message: str


# ヘルパー関数
def load_sightings() -> dict:
    """熊出没データを読み込む"""
    try:
        with open(SIGHTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"metadata": {}, "sightings": []}


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2点間の距離を計算（km）- ハバーサイン公式の簡易版"""
    import math
    R = 6371  # 地球の半径（km）
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def get_time_risk_level() -> tuple[str, Optional[str]]:
    """現在時刻に基づくリスクレベルを判定"""
    current_hour = datetime.now().hour
    
    # 熊の活動が活発な時間帯
    if 5 <= current_hour <= 7:
        return "high", "⚠️ 早朝は熊の活動が最も活発な時間帯です。外出を控えるか、十分注意してください。"
    elif 17 <= current_hour <= 19:
        return "high", "⚠️ 夕方は熊の活動が活発になる時間帯です。日没前に帰宅することをお勧めします。"
    elif 8 <= current_hour <= 16:
        return "low", None
    else:
        return "medium", "🌙 夜間の外出は視界が悪く、熊との遭遇リスクが高まります。"


# エンドポイント
@app.get("/")
async def root():
    return {
        "message": "KumaSafe API - 熊出没回避・共存システム",
        "version": "1.0.0",
        "philosophy": "熊を傷つけない、出会わない"
    }


@app.get("/api/sightings", response_model=list[BearSighting])
async def get_sightings(
    days: Optional[int] = Query(None, description="過去N日間のデータに絞り込む"),
    danger_level: Optional[int] = Query(None, ge=1, le=5, description="危険度でフィルタ")
):
    """熊出没情報一覧を取得（日付・時刻の新しい順）"""
    data = load_sightings()
    sightings = data.get("sightings", [])
    
    if days:
        cutoff_date = datetime.now().date()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        sightings = [
            s for s in sightings 
            if datetime.strptime(s["date"], "%Y-%m-%d").date() >= cutoff_date
        ]
    
    if danger_level:
        sightings = [s for s in sightings if s["danger_level"] >= danger_level]
    
    # 日付・時刻の新しい順にソート
    sightings = sorted(
        sightings,
        key=lambda x: (x["date"], x["time"]),
        reverse=True  # 降順（新しい順）
    )
    
    return sightings


@app.get("/api/sightings/{sighting_id}", response_model=BearSighting)
async def get_sighting(sighting_id: int):
    """特定の目撃情報を取得"""
    data = load_sightings()
    for sighting in data.get("sightings", []):
        if sighting["id"] == sighting_id:
            return sighting
    raise HTTPException(status_code=404, detail="Sighting not found")


@app.post("/api/safety-check", response_model=SafetyResponse)
async def check_safety(check: SafetyCheck):
    """指定地点の安全性をチェック"""
    data = load_sightings()
    sightings = data.get("sightings", [])
    
    # 近隣の目撃情報を検索
    nearby = []
    for s in sightings:
        distance = calculate_distance(check.lat, check.lng, s["lat"], s["lng"])
        if distance <= check.radius_km:
            nearby.append({
                **s,
                "distance_km": round(distance, 2)
            })
    
    # 時間帯リスク
    time_risk, time_warning = get_time_risk_level()
    
    # 総合リスク評価
    if len(nearby) == 0:
        risk_level = "low" if time_risk == "low" else time_risk
        is_safe = True
    elif len(nearby) <= 2:
        risk_level = "medium"
        is_safe = time_risk != "high"
    else:
        risk_level = "high"
        is_safe = False
    
    # 最高危険度の目撃情報があれば調整
    if nearby and max(s["danger_level"] for s in nearby) >= 4:
        risk_level = "high"
        is_safe = False
    
    # 推奨事項
    recommendations = []
    if risk_level == "high":
        recommendations = [
            "🔴 この地域での外出は極力控えてください",
            "🔔 熊鈴やホイッスルを必ず携帯してください",
            "👥 単独行動は避け、複数人で行動してください",
            "📱 家族に行き先と帰宅予定時刻を伝えてください"
        ]
    elif risk_level == "medium":
        recommendations = [
            "🟡 周囲に注意しながら行動してください",
            "🔔 熊鈴の携帯を推奨します",
            "⏰ 早朝・夕方の時間帯は特に注意してください"
        ]
    else:
        recommendations = [
            "🟢 比較的安全ですが、基本的な注意は怠らないでください",
            "🔔 念のため熊鈴を携帯すると安心です"
        ]
    
    return SafetyResponse(
        is_safe=is_safe,
        risk_level=risk_level,
        nearby_sightings=sorted(nearby, key=lambda x: x["distance_km"]),
        recommendations=recommendations,
        time_warning=time_warning
    )


@app.get("/api/heatmap-data")
async def get_heatmap_data():
    """ヒートマップ用のデータを取得"""
    data = load_sightings()
    sightings = data.get("sightings", [])
    
    # [lat, lng, intensity] 形式で返す
    heatmap_points = []
    for s in sightings:
        intensity = s["danger_level"] / 5.0  # 0-1に正規化
        heatmap_points.append([s["lat"], s["lng"], intensity])
    
    return heatmap_points


@app.get("/api/statistics")
async def get_statistics():
    """統計情報を取得"""
    data = load_sightings()
    sightings = data.get("sightings", [])
    
    if not sightings:
        return {"total": 0}
    
    # 月別集計
    monthly = {}
    for s in sightings:
        month = s["date"][:7]
        monthly[month] = monthly.get(month, 0) + 1
    
    # 時間帯別集計
    hourly = {"早朝(5-8時)": 0, "日中(8-17時)": 0, "夕方(17-20時)": 0, "夜間(20-5時)": 0}
    for s in sightings:
        hour = int(s["time"].split(":")[0])
        if 5 <= hour < 8:
            hourly["早朝(5-8時)"] += 1
        elif 8 <= hour < 17:
            hourly["日中(8-17時)"] += 1
        elif 17 <= hour < 20:
            hourly["夕方(17-20時)"] += 1
        else:
            hourly["夜間(20-5時)"] += 1
    
    return {
        "total": len(sightings),
        "by_type": {
            "目撃": len([s for s in sightings if s["type"] == "目撃"]),
            "痕跡": len([s for s in sightings if s["type"] == "痕跡"])
        },
        "by_month": monthly,
        "by_time": hourly,
        "avg_danger_level": round(sum(s["danger_level"] for s in sightings) / len(sightings), 1),
        "last_updated": data.get("metadata", {}).get("last_updated", "不明")
    }


@app.get("/api/coexistence-tips")
async def get_coexistence_tips():
    """熊との共存のためのヒントを取得"""
    return {
        "prevention": [
            {
                "title": "熊鈴・ホイッスルの携帯",
                "description": "音を出すことで熊に人間の存在を知らせ、遭遇を防ぎます",
                "icon": "🔔"
            },
            {
                "title": "早朝・夕方の外出を控える",
                "description": "熊の活動が活発な時間帯（5-8時、17-20時）の外出は最小限に",
                "icon": "⏰"
            },
            {
                "title": "ゴミの適切な管理",
                "description": "生ゴミの臭いは熊を誘引します。密閉容器で保管してください",
                "icon": "🗑️"
            },
            {
                "title": "複数人での行動",
                "description": "単独行動より複数人での行動が安全です",
                "icon": "👥"
            }
        ],
        "encounter": [
            {
                "title": "慌てず、静かに後退",
                "description": "熊を刺激せず、ゆっくりと後ずさりしてその場を離れてください",
                "icon": "🚶"
            },
            {
                "title": "目を合わせ続けない",
                "description": "熊の目を直視し続けることは威嚇と捉えられる可能性があります",
                "icon": "👀"
            },
            {
                "title": "絶対に走って逃げない",
                "description": "走ると熊の追跡本能を刺激します。熊は時速50kmで走れます",
                "icon": "🏃"
            },
            {
                "title": "食べ物を投げない",
                "description": "食べ物を投げると熊が人間から餌をもらえると学習してしまいます",
                "icon": "🍎"
            }
        ],
        "coexistence_philosophy": "熊は本来、人間を避けて生活しています。私たちが熊の生態を理解し、適切な距離を保つことで、互いに傷つけ合うことなく共存できます。"
    }


@app.post("/api/notify/line")
async def send_line_notification(request: LineNotifyRequest):
    """LINE Notifyで通知を送信"""
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {request.token}"
    }
    data = {
        "message": request.message
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, data=data)
            if response.status_code == 200:
                return {"success": True, "message": "通知を送信しました"}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
