// マップの初期設定（長野市役所付近）
const map = L.map('map').setView([36.6485, 138.1942], 13);

// 地図タイルの読み込み（OpenStreetMap）
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// ユーザーの位置情報マーカー
let userMarker = null;
let userCircle = null;

// 熊アイコンの定義
const bearIcon = L.divIcon({
    className: 'custom-bear-icon',
    html: '<div style="font-size: 24px;">🐻</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
});

// データの読み込みと表示
async function loadData() {
    try {
        const response = await fetch('data/kuma_data.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        renderSightings(data);
    } catch (error) {
        console.error('Failed to load data:', error);
        // フォールバックデータ（ローカルサーバーなしで開いた場合など）
        const fallbackData = [
            {
                "id": 1,
                "date": "2025-10-30",
                "time": "15:30",
                "location": "長野市大字長野（デモデータ）",
                "lat": 36.6575,
                "lng": 138.1985,
                "details": "成獣1頭の目撃。山林へ立ち去る。",
                "status": "warning"
            }
        ];
        renderSightings(fallbackData);
        alert('データの読み込みに失敗しました。デモデータを表示します。（ローカルサーバー経由でアクセスしてください）');
    }
}

// 目撃情報の描画
let sightings = []; // 距離計算用に保持

function renderSightings(data) {
    sightings = data;
    const listEl = document.getElementById('sighting-list');
    listEl.innerHTML = '';

    data.forEach(item => {
        // マーカー追加
        const marker = L.marker([item.lat, item.lng], { icon: bearIcon })
            .addTo(map)
            .bindPopup(`
                <strong>${item.date} ${item.time}</strong><br>
                ${item.location}<br>
                <small>${item.details}</small>
            `);

        // リスト追加
        const li = document.createElement('li');
        li.className = 'sighting-item';
        li.innerHTML = `
            <div class="sighting-date">${item.date} ${item.time}</div>
            <div class="sighting-loc">${item.location}</div>
            <div class="sighting-details">${item.details}</div>
        `;
        // クリックで地図移動
        li.addEventListener('click', () => {
            map.flyTo([item.lat, item.lng], 15);
            marker.openPopup();
        });
        listEl.appendChild(li);
    });
}

// 現在地取得とアラート判定
function onLocationFound(e) {
    const radius = e.accuracy / 2;

    if (userMarker) {
        map.removeLayer(userMarker);
        map.removeLayer(userCircle);
    }

    userMarker = L.marker(e.latlng).addTo(map)
        .bindPopup("あなたは今ここです").openPopup();

    userCircle = L.circle(e.latlng, radius).addTo(map);

    map.setView(e.latlng, 14);

    checkProximity(e.latlng);
}

function onLocationError(e) {
    alert("現在地を取得できませんでした: " + e.message);
}

// 近くに熊がいないかチェック（500m以内）
function checkProximity(userLatLng) {
    const ALERT_RADIUS_METERS = 500;
    let nearbyBears = [];

    sightings.forEach(bear => {
        const bearLatLng = L.latLng(bear.lat, bear.lng);
        const distance = userLatLng.distanceTo(bearLatLng); // メートル単位
        if (distance < ALERT_RADIUS_METERS) {
            nearbyBears.push(bear);
        }
    });

    const statusCard = document.getElementById('status-card');
    const statusTitle = document.getElementById('status-title');
    const statusMsg = document.getElementById('status-message');

    if (nearbyBears.length > 0) {
        statusCard.classList.remove('hidden');
        statusCard.classList.add('danger');
        statusTitle.textContent = `⚠️ 半径${ALERT_RADIUS_METERS}m以内に目撃情報あり`;
        statusMsg.textContent = `${nearbyBears.length}件の目撃情報が近くにあります。周囲をよく確認し、落ち着いて行動してください。`;
        
        // 最初の危険箇所への線を描画などの拡張も可能
    } else {
        // 安全な場合も表示（安心感のため）
        statusCard.classList.remove('hidden');
        statusCard.classList.remove('danger');
        statusTitle.textContent = `✅ 付近に直近の目撃情報はありません`;
        statusMsg.textContent = `ただし、油断せず鈴などを携帯しましょう。`;
        
        // 数秒後に消す
        setTimeout(() => {
            statusCard.classList.add('hidden');
        }, 5000);
    }
}

// イベントリスナー
document.getElementById('locate-btn').addEventListener('click', () => {
    map.locate({setView: true, maxZoom: 16});
});

map.on('locationfound', onLocationFound);
map.on('locationerror', onLocationError);

// 初期ロード
loadData();
