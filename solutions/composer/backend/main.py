"""
BearGuardian Backend API
長野市の熊出没情報を管理し、リアルタイム監視を提供するAPI
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict
import json
import os
from datetime import datetime
from pydantic import BaseModel

app = FastAPI(title="BearGuardian API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# データモデル
class BearSighting(BaseModel):
    id: str
    date: str
    location: str
    latitude: float
    longitude: float
    description: str
    distance_from_home: float = None

class FamilyMember(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    timestamp: str

# データファイルのパス
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BEAR_SIGHTINGS_FILE = os.path.join(DATA_DIR, "bear_sightings.json")
FAMILY_LOCATIONS_FILE = os.path.join(DATA_DIR, "family_locations.json")

def load_bear_sightings() -> List[Dict]:
    """熊出没情報を読み込む"""
    if os.path.exists(BEAR_SIGHTINGS_FILE):
        with open(BEAR_SIGHTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_bear_sightings(sightings: List[Dict]):
    """熊出没情報を保存する"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BEAR_SIGHTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(sightings, f, ensure_ascii=False, indent=2)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の距離を計算（km）"""
    from math import radians, cos, sin, asin, sqrt
    R = 6371  # 地球の半径（km）
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# 新居の位置（長野市、例として設定）
HOME_LATITUDE = 36.6513
HOME_LONGITUDE = 138.1810

@app.get("/")
async def root():
    return {"message": "BearGuardian API", "version": "1.0.0"}

@app.get("/api/bear-sightings")
async def get_bear_sightings():
    """熊出没情報一覧を取得"""
    sightings = load_bear_sightings()
    # 新居からの距離を計算
    for sighting in sightings:
        dist = calculate_distance(
            HOME_LATITUDE, HOME_LONGITUDE,
            sighting["latitude"], sighting["longitude"]
        )
        sighting["distance_from_home"] = round(dist, 2)
    return {"sightings": sightings}

@app.post("/api/bear-sightings")
async def add_bear_sighting(sighting: BearSighting):
    """新しい熊出没情報を追加"""
    sightings = load_bear_sightings()
    sighting_dict = sighting.dict()
    sightings.append(sighting_dict)
    save_bear_sightings(sightings)
    
    # WebSocketで通知
    await manager.broadcast({
        "type": "new_sighting",
        "data": sighting_dict
    })
    
    return {"message": "Sighting added", "sighting": sighting_dict}

@app.get("/api/family-locations")
async def get_family_locations():
    """家族の位置情報を取得"""
    if os.path.exists(FAMILY_LOCATIONS_FILE):
        with open(FAMILY_LOCATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"members": []}

@app.post("/api/family-locations")
async def update_family_location(member: FamilyMember):
    """家族の位置情報を更新"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 既存の位置情報を読み込む
    if os.path.exists(FAMILY_LOCATIONS_FILE):
        with open(FAMILY_LOCATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            members = data.get("members", [])
    else:
        members = []
    
    # 既存のメンバーを更新または追加
    found = False
    for i, m in enumerate(members):
        if m["id"] == member.id:
            members[i] = member.dict()
            found = True
            break
    if not found:
        members.append(member.dict())
    
    # 保存
    with open(FAMILY_LOCATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"members": members}, f, ensure_ascii=False, indent=2)
    
    # 危険エリアチェック
    sightings = load_bear_sightings()
    warnings = []
    for sighting in sightings:
        dist = calculate_distance(
            member.latitude, member.longitude,
            sighting["latitude"], sighting["longitude"]
        )
        if dist < 0.5:  # 500m以内
            warnings.append({
                "sighting": sighting,
                "distance": round(dist, 2),
                "member": member.name
            })
    
    # WebSocketで通知
    await manager.broadcast({
        "type": "location_update",
        "data": member.dict(),
        "warnings": warnings
    })
    
    return {
        "message": "Location updated",
        "member": member.dict(),
        "warnings": warnings
    }

@app.get("/api/danger-zones")
async def get_danger_zones():
    """危険エリア（熊出没情報周辺）を取得"""
    sightings = load_bear_sightings()
    danger_zones = []
    for sighting in sightings:
        danger_zones.append({
            "center": {
                "lat": sighting["latitude"],
                "lng": sighting["longitude"]
            },
            "radius": 0.5,  # 500m半径
            "sighting": sighting
        })
    return {"zones": danger_zones}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket接続"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # クライアントからのメッセージ処理（必要に応じて）
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
