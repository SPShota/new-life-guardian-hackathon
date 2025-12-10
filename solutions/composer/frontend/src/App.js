import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import MapView from './components/MapView';
import Sidebar from './components/Sidebar';
import NotificationPanel from './components/NotificationPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { API_BASE_URL } from './config';

function App() {
  const [bearSightings, setBearSightings] = useState([]);
  const [familyMembers, setFamilyMembers] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [selectedSighting, setSelectedSighting] = useState(null);
  
  const ws = useWebSocket(`${API_BASE_URL.replace('http', 'ws')}/ws`);

  // 熊出没情報を取得
  const fetchBearSightings = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/bear-sightings`);
      const data = await response.json();
      setBearSightings(data.sightings || []);
    } catch (error) {
      console.error('熊出没情報の取得に失敗しました:', error);
    }
  }, []);

  // 家族の位置情報を取得
  const fetchFamilyLocations = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/family-locations`);
      const data = await response.json();
      setFamilyMembers(data.members || []);
    } catch (error) {
      console.error('家族の位置情報の取得に失敗しました:', error);
    }
  }, []);

  // WebSocketメッセージの処理
  useEffect(() => {
    if (ws) {
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'new_sighting') {
          setBearSightings(prev => [...prev, message.data]);
          setNotifications(prev => [{
            id: Date.now(),
            type: 'warning',
            title: '新しい熊出没情報',
            message: `${message.data.location}で熊が目撃されました`,
            timestamp: new Date().toISOString()
          }, ...prev]);
        }
        
        if (message.type === 'location_update') {
          setFamilyMembers(prev => {
            const updated = prev.filter(m => m.id !== message.data.id);
            return [...updated, message.data];
          });
          
          if (message.warnings && message.warnings.length > 0) {
            message.warnings.forEach(warning => {
              setNotifications(prev => [{
                id: Date.now(),
                type: 'danger',
                title: '⚠️ 危険エリア接近',
                message: `${warning.member}が${warning.sighting.location}から${warning.distance}kmの位置にいます`,
                timestamp: new Date().toISOString()
              }, ...prev]);
            });
          }
        }
      };
    }
  }, [ws]);

  // 初回データ取得
  useEffect(() => {
    fetchBearSightings();
    fetchFamilyLocations();
    
    // 定期的にデータを更新
    const interval = setInterval(() => {
      fetchBearSightings();
      fetchFamilyLocations();
    }, 30000); // 30秒ごと
    
    return () => clearInterval(interval);
  }, [fetchBearSightings, fetchFamilyLocations]);

  // 家族の位置情報を更新（モック）
  const updateFamilyLocation = async (memberId, name, lat, lng) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/family-locations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: memberId,
          name: name,
          latitude: lat,
          longitude: lng,
          timestamp: new Date().toISOString()
        })
      });
      const data = await response.json();
      if (data.member) {
        setFamilyMembers(prev => {
          const updated = prev.filter(m => m.id !== memberId);
          return [...updated, data.member];
        });
      }
    } catch (error) {
      console.error('位置情報の更新に失敗しました:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🐻 BearGuardian</h1>
        <p>家族の安全を守る熊出没情報監視システム</p>
      </header>
      <div className="App-content">
        <Sidebar
          bearSightings={bearSightings}
          familyMembers={familyMembers}
          selectedSighting={selectedSighting}
          onSelectSighting={setSelectedSighting}
          onUpdateLocation={updateFamilyLocation}
        />
        <div className="Map-container">
          <MapView
            bearSightings={bearSightings}
            familyMembers={familyMembers}
            selectedSighting={selectedSighting}
            onSelectSighting={setSelectedSighting}
          />
          <NotificationPanel
            notifications={notifications}
            onDismiss={(id) => setNotifications(prev => prev.filter(n => n.id !== id))}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
