import { useState, useEffect } from 'react';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  Button,
  Badge,
  Card,
  CardBody,
  ScrollShadow,
  Divider,
  Chip,
} from '@nextui-org/react';
import {
  BellIcon,
  XMarkIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  DocumentTextIcon,
  CreditCardIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import useWebSocket, { WebSocketMessage } from '@/hooks/useWebSocket';

interface Notification extends WebSocketMessage {
  id: string;
  read: boolean;
  createdAt: Date;
}

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  
  const { lastMessage, isConnected, connectionCount } = useWebSocket({
    enableNotifications: false, // We'll handle notifications manually here
    onMessage: (message) => {
      // Add new message as notification
      if (shouldShowAsNotification(message)) {
        const notification: Notification = {
          ...message,
          id: `${Date.now()}-${Math.random()}`,
          read: false,
          createdAt: new Date(),
        };
        
        setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep last 50
      }
    },
  });

  const shouldShowAsNotification = (message: WebSocketMessage): boolean => {
    const notificationTypes = [
      'invoice_created',
      'invoice_sent',
      'payment_received',
      'invoice_overdue',
      'customer_created',
      'system_update',
      'user_activity',
    ];
    
    return notificationTypes.includes(message.type);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (notificationId: string) => {
    setNotifications(prev =>
      prev.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, read: true }))
    );
  };

  const clearNotification = (notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'invoice_created':
      case 'invoice_sent':
        return <DocumentTextIcon className="h-5 w-5 text-blue-500" />;
      case 'payment_received':
        return <CreditCardIcon className="h-5 w-5 text-green-500" />;
      case 'invoice_overdue':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'customer_created':
        return <UserIcon className="h-5 w-5 text-purple-500" />;
      case 'system_update':
        return <InformationCircleIcon className="h-5 w-5 text-orange-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'warning';
      case 'info':
        return 'primary';
      default:
        return 'default';
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    
    if (notification.action_url) {
      // Navigate to the action URL
      window.location.href = notification.action_url;
    }
  };

  return (
    <Popover
      isOpen={isOpen}
      onOpenChange={setIsOpen}
      placement="bottom-end"
      showArrow
      className="w-96"
    >
      <PopoverTrigger>
        <Button
          isIconOnly
          variant="light"
          className="relative"
          aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
        >
          <div className="relative">
            <BellIcon className="h-5 w-5" />
            {unreadCount > 0 && (
              <Badge
                content={unreadCount > 99 ? '99+' : unreadCount}
                color="danger"
                size="sm"
                className="absolute -top-1 -right-1"
              />
            )}
            {/* Connection status indicator */}
            <div
              className={`absolute -bottom-1 -right-1 w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-gray-400'
              }`}
              title={isConnected ? 'Connected' : 'Disconnected'}
            />
          </div>
        </Button>
      </PopoverTrigger>

      <PopoverContent className="p-0 w-96">
        <div className="max-h-96">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold">Notifications</h3>
              {connectionCount > 0 && (
                <Chip size="sm" variant="flat" color="success">
                  {connectionCount} online
                </Chip>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <Button
                  size="sm"
                  variant="light"
                  onClick={markAllAsRead}
                  className="text-xs"
                >
                  Mark all read
                </Button>
              )}
              {notifications.length > 0 && (
                <Button
                  size="sm"
                  variant="light"
                  onClick={clearAllNotifications}
                  className="text-xs"
                  color="danger"
                >
                  Clear all
                </Button>
              )}
            </div>
          </div>

          {/* Connection Status */}
          <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 text-xs">
            <div className="flex items-center justify-between">
              <span className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span>
                  {isConnected ? 'Real-time updates active' : 'Disconnected'}
                </span>
              </span>
              {connectionCount > 0 && (
                <span className="text-gray-500">
                  {connectionCount} connections
                </span>
              )}
            </div>
          </div>

          {/* Notifications List */}
          <ScrollShadow className="max-h-80">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <BellIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No notifications yet</p>
                <p className="text-xs mt-1">
                  You'll see real-time updates here
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {notifications.map((notification, index) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors ${
                      !notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    }`}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div className="flex space-x-3">
                      <div className="flex-shrink-0">
                        {getNotificationIcon(notification.type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            {notification.title && (
                              <p className="font-medium text-sm text-gray-900 dark:text-gray-100">
                                {notification.title}
                              </p>
                            )}
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                              {notification.message}
                            </p>
                          </div>
                          
                          <div className="flex items-center space-x-2 ml-2">
                            {notification.priority && notification.priority !== 'info' && (
                              <Chip
                                size="sm"
                                variant="flat"
                                color={getPriorityColor(notification.priority)}
                              >
                                {notification.priority}
                              </Chip>
                            )}
                            
                            {!notification.read && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full" />
                            )}
                            
                            <Button
                              isIconOnly
                              size="sm"
                              variant="light"
                              onClick={(e) => {
                                e.stopPropagation();
                                clearNotification(notification.id);
                              }}
                              className="opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <XMarkIcon className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between mt-2">
                          <p className="text-xs text-gray-500">
                            {formatDistanceToNow(notification.createdAt, { addSuffix: true })}
                          </p>
                          
                          {notification.action_url && (
                            <span className="text-xs text-blue-500 hover:text-blue-700">
                              View details →
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollShadow>
          
          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-3 border-t text-center">
              <Button
                size="sm"
                variant="light"
                onClick={() => setIsOpen(false)}
              >
                Close
              </Button>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}