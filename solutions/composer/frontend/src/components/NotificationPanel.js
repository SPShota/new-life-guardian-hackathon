import React from 'react';
import './NotificationPanel.css';

function NotificationPanel({ notifications, onDismiss }) {
  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="NotificationPanel">
      {notifications.slice(0, 5).map((notification) => (
        <div
          key={notification.id}
          className={`Notification ${notification.type}`}
          onClick={() => onDismiss(notification.id)}
        >
          <div className="Notification-header">
            <strong>{notification.title}</strong>
            <button
              className="Notification-close"
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(notification.id);
              }}
            >
              ×
            </button>
          </div>
          <div className="Notification-message">{notification.message}</div>
          <div className="Notification-time">
            {new Date(notification.timestamp).toLocaleTimeString('ja-JP')}
          </div>
        </div>
      ))}
    </div>
  );
}

export default NotificationPanel;
