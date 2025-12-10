import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Types
interface BearSighting {
  id: number;
  date: string;
  time: string;
  location: string;
  lat: number;
  lng: number;
  type: string;
  description: string;
  danger_level: number;
}

interface SafetyResult {
  is_safe: boolean;
  risk_level: string;
  nearby_sightings: (BearSighting & { distance_km: number })[];
  recommendations: string[];
  time_warning: string | null;
}

interface Statistics {
  total: number;
  by_type: { 目撃: number; 痕跡: number };
  by_month: Record<string, number>;
  by_time: Record<string, number>;
  avg_danger_level: number;
  last_updated: string;
}

interface CoexistenceTip {
  title: string;
  description: string;
  icon: string;
}

// API Base URL
const API_BASE = '/api';

// descriptionから地域名を抽出するヘルパー関数
const extractAreaName = (description: string, fallbackLocation: string): string => {
  // descriptionの形式: "1 4月5日 17時00分 七二会 七二会乙地籍内 目撃 ..."
  // または詳細な地名を含む文字列
  
  // 長野市の主要地域リスト
  const areas = [
    '篠ノ井', '松代', '若穂', '川中島', '信更', '戸隠', '七二会', 
    '信州新町', '中条', '豊野', '大岡', '芋井', '鬼無里', '安茂里',
    '飯綱', '牟礼', '小川', '浅川', '三輪', '柳原', '古里', '稀田',
    '小松原', '布施', '更北', '犀川', '朝陽', '長沼', '古牧', '吉田',
    '稲里', '青木島', '真島', '御厨', '今井', '塩崎', '西寺尾', '東和田'
  ];
  
  for (const area of areas) {
    if (description.includes(area)) {
      return `長野市${area}`;
    }
  }
  
  // 地域名が見つからない場合、descriptionから場所らしき部分を抽出
  const match = description.match(/\d+時\d+分\s+(\S+)\s+/);
  if (match && match[1]) {
    return `長野市${match[1]}`;
  }
  
  return fallbackLocation;
};

// Custom Icons
const bearIcon = new L.DivIcon({
  html: '<div style="font-size: 24px;">🐻</div>',
  className: 'bear-marker',
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

const traceIcon = new L.DivIcon({
  html: '<div style="font-size: 20px;">🐾</div>',
  className: 'trace-marker',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const userIcon = new L.DivIcon({
  html: '<div style="font-size: 24px;">📍</div>',
  className: 'user-marker',
  iconSize: [30, 30],
  iconAnchor: [15, 30],
});

// Map Center Component
function MapCenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 12);
  }, [center, map]);
  return null;
}

// Current Location Button Component
function LocationButton({ onLocation }: { onLocation: (lat: number, lng: number) => void }) {
  const map = useMap();
  
  const handleClick = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          map.setView([latitude, longitude], 14);
          onLocation(latitude, longitude);
        },
        (error) => {
          console.error('位置情報の取得に失敗しました:', error);
          alert('位置情報を取得できませんでした。ブラウザの設定を確認してください。');
        }
      );
    } else {
      alert('このブラウザは位置情報をサポートしていません。');
    }
  };
  
  return (
    <button className="location-button" onClick={handleClick} title="現在地を取得">
      📍
    </button>
  );
}

function App() {
  // State
  const [sightings, setSightings] = useState<BearSighting[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [tips, setTips] = useState<{ prevention: CoexistenceTip[]; encounter: CoexistenceTip[]; coexistence_philosophy: string } | null>(null);
  const [safetyResult, setSafetyResult] = useState<SafetyResult | null>(null);
  const [checkLat, setCheckLat] = useState<string>('36.6513');
  const [checkLng, setCheckLng] = useState<string>('138.1810');
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [activeTab, setActiveTab] = useState<'map' | 'tips'>('map');
  const [lineToken, setLineToken] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [mapCenter] = useState<[number, number]>([36.6513, 138.1810]); // 長野市中心

  // Fetch Data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sightingsRes, statsRes, tipsRes] = await Promise.all([
          fetch(`${API_BASE}/sightings`),
          fetch(`${API_BASE}/statistics`),
          fetch(`${API_BASE}/coexistence-tips`),
        ]);
        
        if (sightingsRes.ok) setSightings(await sightingsRes.json());
        if (statsRes.ok) setStatistics(await statsRes.json());
        if (tipsRes.ok) setTips(await tipsRes.json());
      } catch (error) {
        console.error('データの取得に失敗しました:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Safety Check
  const handleSafetyCheck = async () => {
    const lat = parseFloat(checkLat);
    const lng = parseFloat(checkLng);
    
    if (isNaN(lat) || isNaN(lng)) {
      alert('有効な緯度・経度を入力してください');
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/safety-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lng, radius_km: 2.0 }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setSafetyResult(result);
        setUserLocation([lat, lng]);
      }
    } catch (error) {
      console.error('安全チェックに失敗しました:', error);
    }
  };

  // LINE Notify
  const handleLineNotify = async () => {
    if (!lineToken) {
      alert('LINE Notifyトークンを入力してください');
      return;
    }
    
    const message = `\n🐻 KumaSafe 定期通知\n\n📊 累計目撃情報: ${statistics?.total || 0}件\n⚠️ 平均危険度: ${statistics?.avg_danger_level || '-'}\n\n最新情報はKumaSafeアプリでご確認ください。`;
    
    try {
      const response = await fetch(`${API_BASE}/notify/line`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: lineToken, message }),
      });
      
      const result = await response.json();
      if (result.success) {
        alert('LINE通知を送信しました');
      } else {
        alert('通知の送信に失敗しました: ' + result.error);
      }
    } catch (error) {
      console.error('LINE通知エラー:', error);
    }
  };

  // Handle user location from map
  const handleUserLocation = (lat: number, lng: number) => {
    setCheckLat(lat.toFixed(4));
    setCheckLng(lng.toFixed(4));
    setUserLocation([lat, lng]);
  };

  // Get risk color
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return '#28a745';
      case 'medium': return '#ffc107';
      case 'high': return '#dc3545';
      default: return '#6c757d';
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">🐻</span>
            <div>
              <div>KumaSafe</div>
              <div className="tagline">熊出没回避・共存システム</div>
            </div>
          </div>
          <div className="tagline">「熊を傷つけない、出会わない」</div>
        </div>
      </header>

      {/* Philosophy Banner */}
      <div className="philosophy-banner">
        🌲 私たちは熊との共存を目指します。このシステムは駆除ではなく「回避」に特化しています 🌲
      </div>

      {/* Main Content */}
      <main className="main-content">
        {/* Map */}
        <div className="map-container">
          <MapContainer
            center={mapCenter}
            zoom={11}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapCenter center={mapCenter} />
            <LocationButton onLocation={handleUserLocation} />
            
            {/* Bear Sightings */}
            {sightings.map((sighting) => (
              <Marker
                key={sighting.id}
                position={[sighting.lat, sighting.lng]}
                icon={sighting.type === '目撃' ? bearIcon : traceIcon}
              >
                <Popup>
                  <div className="popup-content">
                    <h3>{sighting.type === '目撃' ? '🐻 熊目撃情報' : '🐾 痕跡情報'}</h3>
                    <p><strong>日時:</strong> {sighting.date} {sighting.time}</p>
                    <p><strong>場所:</strong> {extractAreaName(sighting.description, sighting.location)}</p>
                    <p><strong>詳細:</strong> {sighting.description}</p>
                    <p>
                      <strong>危険度:</strong>{' '}
                      <span className={`danger-badge level-${sighting.danger_level}`}>
                        {'⚠️'.repeat(sighting.danger_level)}
                      </span>
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}
            
            {/* User Location */}
            {userLocation && (
              <>
                <Marker position={userLocation} icon={userIcon}>
                  <Popup>現在地/チェック地点</Popup>
                </Marker>
                <Circle
                  center={userLocation}
                  radius={2000}
                  pathOptions={{
                    color: safetyResult ? getRiskColor(safetyResult.risk_level) : '#666',
                    fillColor: safetyResult ? getRiskColor(safetyResult.risk_level) : '#666',
                    fillOpacity: 0.1,
                  }}
                />
              </>
            )}
          </MapContainer>
        </div>

        {/* Sidebar */}
        <div className="sidebar">
          {/* Tabs */}
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'map' ? 'active' : ''}`}
              onClick={() => setActiveTab('map')}
            >
              🗺️ マップ情報
            </button>
            <button
              className={`tab ${activeTab === 'tips' ? 'active' : ''}`}
              onClick={() => setActiveTab('tips')}
            >
              📚 共存ガイド
            </button>
          </div>

          {activeTab === 'map' ? (
            <>
              {/* Safety Check */}
              <div className="card">
                <h2 className="card-title">🔍 安全チェック</h2>
                <div className="safety-check">
                  <div className="safety-input-group">
                    <input
                      type="text"
                      placeholder="緯度 (例: 36.6513)"
                      value={checkLat}
                      onChange={(e) => setCheckLat(e.target.value)}
                    />
                    <input
                      type="text"
                      placeholder="経度 (例: 138.1810)"
                      value={checkLng}
                      onChange={(e) => setCheckLng(e.target.value)}
                    />
                  </div>
                  <button className="check-button" onClick={handleSafetyCheck}>
                    🔍 この地点をチェック
                  </button>
                </div>

                {safetyResult && (
                  <div className={`safety-result ${safetyResult.risk_level === 'low' ? 'safe' : safetyResult.risk_level === 'medium' ? 'medium' : 'danger'}`}>
                    {safetyResult.time_warning && (
                      <div className="time-warning">{safetyResult.time_warning}</div>
                    )}
                    <div className="safety-status">
                      {safetyResult.is_safe ? '✅ 比較的安全' : '⚠️ 注意が必要'}
                    </div>
                    <p>半径2km以内の目撃情報: {safetyResult.nearby_sightings.length}件</p>
                    <ul className="safety-recommendations">
                      {safetyResult.recommendations.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Statistics */}
              {statistics && (
                <div className="card">
                  <h2 className="card-title">📊 統計情報</h2>
                  <div className="statistics">
                    <div className="stat-item">
                      <div className="stat-value">{statistics.total ?? 0}</div>
                      <div className="stat-label">累計報告件数</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">{statistics.by_type?.目撃 ?? 0}</div>
                      <div className="stat-label">目撃情報</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">{statistics.by_type?.痕跡 ?? 0}</div>
                      <div className="stat-label">痕跡情報</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">{statistics.avg_danger_level ?? '-'}</div>
                      <div className="stat-label">平均危険度</div>
                    </div>
                  </div>
                  <p style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#666' }}>
                    最終更新: {statistics.last_updated ?? '不明'}
                  </p>
                </div>
              )}

              {/* Recent Sightings */}
              <div className="card">
                <h2 className="card-title">🐻 最近の目撃情報</h2>
                <div className="sighting-list">
                  {sightings.slice(0, 5).map((sighting) => (
                    <div
                      key={sighting.id}
                      className="sighting-item"
                      onClick={() => {
                        setCheckLat(sighting.lat.toString());
                        setCheckLng(sighting.lng.toString());
                      }}
                    >
                      <div className={`sighting-icon ${sighting.type === '目撃' ? 'sighting' : 'trace'}`}>
                        {sighting.type === '目撃' ? '🐻' : '🐾'}
                      </div>
                      <div className="sighting-info">
                        <div className="sighting-location">
                          {extractAreaName(sighting.description, sighting.location)}
                        </div>
                        <div className="sighting-date">{sighting.date} {sighting.time}</div>
                      </div>
                      <span className={`danger-badge level-${sighting.danger_level}`}>
                        Lv.{sighting.danger_level}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* LINE Notify */}
              <div className="card">
                <h2 className="card-title">📱 LINE通知設定</h2>
                <div className="line-notify">
                  <input
                    type="password"
                    placeholder="LINE Notifyトークン"
                    value={lineToken}
                    onChange={(e) => setLineToken(e.target.value)}
                  />
                  <button className="line-button" onClick={handleLineNotify}>
                    📤 テスト通知を送信
                  </button>
                  <p style={{ fontSize: '0.75rem', color: '#666' }}>
                    <a href="https://notify-bot.line.me/my/" target="_blank" rel="noopener noreferrer">
                      LINE Notifyトークンを取得
                    </a>
                  </p>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Coexistence Tips */}
              {tips && (
                <>
                  <div className="card">
                    <h2 className="card-title">🛡️ 遭遇を防ぐために</h2>
                    <div className="tips-section">
                      {tips.prevention.map((tip, i) => (
                        <div key={i} className="tip-item">
                          <span className="tip-icon">{tip.icon}</span>
                          <div className="tip-content">
                            <h4>{tip.title}</h4>
                            <p>{tip.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="card">
                    <h2 className="card-title">🆘 もし遭遇したら</h2>
                    <div className="tips-section">
                      {tips.encounter.map((tip, i) => (
                        <div key={i} className="tip-item">
                          <span className="tip-icon">{tip.icon}</span>
                          <div className="tip-content">
                            <h4>{tip.title}</h4>
                            <p>{tip.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="card">
                    <h2 className="card-title">🌲 共存の哲学</h2>
                    <p style={{ lineHeight: 1.8 }}>{tips.coexistence_philosophy}</p>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
