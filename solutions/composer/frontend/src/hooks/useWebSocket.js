import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url) {
  const [ws, setWs] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    let websocket = null;

    const connect = () => {
      try {
        websocket = new WebSocket(url);
        
        websocket.onopen = () => {
          console.log('WebSocket接続が確立されました');
          reconnectAttempts.current = 0;
          setWs(websocket);
        };

        websocket.onerror = (error) => {
          console.error('WebSocketエラー:', error);
        };

        websocket.onclose = () => {
          console.log('WebSocket接続が閉じられました');
          setWs(null);
          
          // 再接続を試みる
          if (reconnectAttempts.current < maxReconnectAttempts) {
            reconnectAttempts.current++;
            reconnectTimeoutRef.current = setTimeout(() => {
              console.log(`再接続を試みます (${reconnectAttempts.current}/${maxReconnectAttempts})`);
              connect();
            }, 3000 * reconnectAttempts.current);
          }
        };
      } catch (error) {
        console.error('WebSocket接続エラー:', error);
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (websocket) {
        websocket.close();
      }
    };
  }, [url]);

  return ws;
}
