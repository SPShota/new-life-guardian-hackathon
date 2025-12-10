import React, { useState, useEffect } from 'react';
import './Sidebar.css';

function Sidebar({ bearSightings, familyMembers, selectedSighting, onSelectSighting, onUpdateLocation }) {
  const [activeTab, setActiveTab] = useState('sightings');
  const [simulateMode, setSimulateMode] = useState(false);

  // 位置情報シミュレーション（デモ用）
  const simulateLocation = (memberId, name) => {
    if (!simulateMode) return;
    
    // ランダムな位置を生成（長野市周辺）
    const baseLat = 36.6513;
    const baseLng = 138.1810;
    const offset = 0.01; // 約1km
    
    const lat = baseLat + (Math.random() - 0.5) * offset * 2;
    const lng = baseLng + (Math.random() - 0.5) * offset * 2;
    
    onUpdateLocation(memberId, name, lat, lng);
  };

  useEffect(() => {
    if (simulateMode) {
      const interval = setInterval(() => {
        familyMembers.forEach(member => {
          simulateLocation(member.id, member.name);
        });
      }, 5000); // 5秒ごとに更新
      
      return () => clearInterval(interval);
    }
  }, [simulateMode, familyMembers]);

  return (
    <div className="Sidebar">
      <div className="Sidebar-tabs">
        <button
          className={activeTab === 'sightings' ? 'active' : ''}
          onClick={() => setActiveTab('sightings')}
        >
          熊出没情報 ({bearSightings.length})
        </button>
        <button
          className={activeTab === 'family' ? 'active' : ''}
          onClick={() => setActiveTab('family')}
        >
          家族の位置 ({familyMembers.length})
        </button>
      </div>

      <div className="Sidebar-content">
        {activeTab === 'sightings' && (
          <div className="Sightings-list">
            <div className="Section-header">
              <h3>🐻 熊出没情報</h3>
              <span className="Badge">{bearSightings.length}件</span>
            </div>
            {bearSightings.length === 0 ? (
              <p className="Empty-message">データがありません</p>
            ) : (
              <ul>
                {bearSightings.map((sighting) => (
                  <li
                    key={sighting.id}
                    className={`Sighting-item ${selectedSighting?.id === sighting.id ? 'selected' : ''}`}
                    onClick={() => onSelectSighting(sighting)}
                  >
                    <div className="Sighting-header">
                      <strong>{sighting.location}</strong>
                      {sighting.distance_from_home && (
                        <span className="Distance-badge">
                          {sighting.distance_from_home}km
                        </span>
                      )}
                    </div>
                    <div className="Sighting-date">{sighting.date}</div>
                    <div className="Sighting-description">{sighting.description}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {activeTab === 'family' && (
          <div className="Family-list">
            <div className="Section-header">
              <h3>👨‍👩‍👧 家族の位置</h3>
            </div>
            <div className="Simulate-controls">
              <label>
                <input
                  type="checkbox"
                  checked={simulateMode}
                  onChange={(e) => setSimulateMode(e.target.checked)}
                />
                位置情報シミュレーション（デモ用）
              </label>
            </div>
            {familyMembers.length === 0 ? (
              <div className="Empty-message">
                <p>家族の位置情報がありません</p>
                <button
                  className="Add-member-btn"
                  onClick={() => {
                    const members = [
                      { id: '1', name: '夫（在宅）', lat: 36.6513, lng: 138.1810 },
                      { id: '2', name: '妻', lat: 36.6550, lng: 138.1850 },
                      { id: '3', name: '子供', lat: 36.6550, lng: 138.1850 }
                    ];
                    members.forEach(m => {
                      onUpdateLocation(m.id, m.name, m.lat, m.lng);
                    });
                  }}
                >
                  サンプルデータを追加
                </button>
              </div>
            ) : (
              <ul>
                {familyMembers.map((member) => (
                  <li key={member.id} className="Family-item">
                    <div className="Family-header">
                      <strong>{member.name}</strong>
                    </div>
                    <div className="Family-location">
                      緯度: {member.latitude.toFixed(4)}, 経度: {member.longitude.toFixed(4)}
                    </div>
                    <div className="Family-timestamp">
                      {new Date(member.timestamp).toLocaleString('ja-JP')}
                    </div>
                    {simulateMode && (
                      <button
                        className="Simulate-btn"
                        onClick={() => simulateLocation(member.id, member.name)}
                      >
                        位置を更新
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="Sidebar-footer">
        <div className="Info-box">
          <h4>ℹ️ 使い方</h4>
          <ul>
            <li>地図上の🐻マーカーをクリックして詳細を確認</li>
            <li>赤い円は500mの危険エリアを示します</li>
            <li>家族が危険エリアに近づくと通知が表示されます</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
