import React, { useState, useEffect } from 'react';
import { Bell, X, Check, Trash2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  priority: string;
  link?: string;
  created_at: string;
  read: boolean;
}

export const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) return;

    // Fetch notifications
    fetchNotifications();
    fetchUnreadCount();

    // Set up polling (every 30 seconds)
    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000);

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const fetchNotifications = async () => {
    try {
      const response = await fetch('/api/v1/notifications?limit=10', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await fetch('/api/v1/notifications/count', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.count);
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const markAsRead = async (id: string) => {
    try {
      await fetch(`/api/v1/notifications/${id}/read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await fetch('/api/v1/notifications/read-all', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, read: true }))
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const getIconColor = (type: string) => {
    switch (type) {
      case 'brief_ready': return 'text-purple-600';
      case 'article_ready': return 'text-blue-600';
      case 'document_processed': return 'text-green-600';
      case 'scout_finding': return 'text-orange-600';
      case 'budget_warning': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  if (!isAuthenticated) return null;

  return (
    <div className="relative">
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) fetchNotifications();
        }}
        className="relative p-2 text-gray-600 hover:text-purple-600 transition-colors"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border z-50 max-h-[600px] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
                >
                  <Check className="w-4 h-4" />
                  Mark all read
                </button>
              )}
            </div>

            <div className="overflow-y-auto max-h-[400px]">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Bell className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No notifications yet</p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 border-b hover:bg-gray-50 transition-colors ${
                      !notification.read ? 'bg-purple-50' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`mt-1 ${getIconColor(notification.type)}`}>
                        <div className="w-2 h-2 rounded-full bg-current" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 text-sm">
                          {notification.title}
                        </p>
                        <p className="text-gray-600 text-sm mt-0.5">
                          {notification.message}
                        </p>
                        <p className="text-gray-400 text-xs mt-1">
                          {formatTime(notification.created_at)}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        {!notification.read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="p-1 text-gray-400 hover:text-purple-600"
                            title="Mark as read"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        {notification.link && (
                          <a
                            href={notification.link}
                            className="p-1 text-gray-400 hover:text-purple-600"
                            title="View"
                          >
                            <span className="sr-only">View</span>
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 border-t bg-gray-50 text-center">
              <a 
                href="/notifications" 
                className="text-sm text-purple-600 hover:text-purple-700"
              >
                View all notifications
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
