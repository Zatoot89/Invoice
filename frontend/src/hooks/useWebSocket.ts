import { useEffect, useState, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';

export interface WebSocketMessage {
  type: string;
  title?: string;
  message: string;
  data?: any;
  timestamp: string;
  action_url?: string;
  priority?: 'low' | 'info' | 'high' | 'critical';
}

export interface WebSocketHookOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  enableNotifications?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: WebSocketMessage | null;
  connectionCount: number;
  error: string | null;
}

const useWebSocket = (options: WebSocketHookOptions = {}) => {
  const {
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    enableNotifications = true,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    lastMessage: null,
    connectionCount: 0,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Get WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.host}`;
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('Authentication token not found');
    }
    
    return `${host}/api/v1/ws/ws?token=${token}`;
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      setState(prev => ({
        ...prev,
        lastMessage: message,
        error: null,
      }));

      // Call custom message handler
      if (onMessage) {
        onMessage(message);
      }

      // Handle different message types
      switch (message.type) {
        case 'connection':
          setState(prev => ({ ...prev, isConnected: true, isConnecting: false }));
          if (onConnect) onConnect();
          break;

        case 'heartbeat':
          // Update connection count from heartbeat
          if (message.data?.connections) {
            setState(prev => ({ ...prev, connectionCount: message.data.connections }));
          }
          break;

        case 'invoice_created':
        case 'invoice_sent':
        case 'payment_received':
        case 'customer_created':
          if (enableNotifications) {
            toast.success(message.message, {
              duration: 4000,
              icon: getNotificationIcon(message.type),
            });
          }
          break;

        case 'invoice_overdue':
          if (enableNotifications) {
            toast.error(message.message, {
              duration: 6000,
              icon: '⚠️',
            });
          }
          break;

        case 'system_update':
          if (enableNotifications) {
            const toastFunction = message.priority === 'high' ? toast.error : toast.info;
            toastFunction(message.message, {
              duration: message.priority === 'high' ? 8000 : 5000,
            });
          }
          break;

        case 'user_activity':
          if (enableNotifications && message.priority !== 'low') {
            toast(message.message, {
              duration: 3000,
              icon: '🔔',
            });
          }
          break;

        case 'error':
          setState(prev => ({ ...prev, error: message.message }));
          toast.error(message.message);
          break;

        case 'pong':
          // Handle pong response to ping
          break;

        default:
          console.log('Unhandled WebSocket message:', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [onMessage, onConnect, enableNotifications]);

  // Get notification icon based on message type
  const getNotificationIcon = (type: string): string => {
    switch (type) {
      case 'invoice_created':
        return '📄';
      case 'invoice_sent':
        return '📨';
      case 'payment_received':
        return '💰';
      case 'customer_created':
        return '👤';
      default:
        return '🔔';
    }
  };

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setState(prev => ({ 
      ...prev, 
      isConnecting: true, 
      error: null 
    }));

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setState(prev => ({ 
          ...prev, 
          isConnected: true, 
          isConnecting: false,
          error: null
        }));
        
        reconnectAttemptsRef.current = 0;
        
        // Start heartbeat ping
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setState(prev => ({ 
          ...prev, 
          isConnected: false, 
          isConnecting: false 
        }));
        
        if (onDisconnect) onDisconnect();
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectAttemptsRef.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${reconnectAttempts})`);
            connect();
          }, reconnectInterval * Math.pow(1.5, reconnectAttemptsRef.current - 1));
        } else if (reconnectAttemptsRef.current >= reconnectAttempts) {
          setState(prev => ({ 
            ...prev, 
            error: 'Failed to reconnect to server' 
          }));
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ 
          ...prev, 
          error: 'WebSocket connection error',
          isConnecting: false
        }));
        
        if (onError) onError(error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Connection failed',
        isConnecting: false
      }));
    }
  }, [getWebSocketUrl, handleMessage, onDisconnect, onError, reconnectAttempts, reconnectInterval]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setState(prev => ({ 
      ...prev, 
      isConnected: false, 
      isConnecting: false 
    }));
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket is not connected');
    return false;
  }, []);

  // Send typing indicator
  const sendTypingIndicator = useCallback((isTyping: boolean) => {
    return sendMessage({
      type: 'typing',
      is_typing: isTyping,
    });
  }, [sendMessage]);

  // Subscribe to specific events
  const subscribe = useCallback((eventTypes: string[]) => {
    return sendMessage({
      type: 'subscribe',
      events: eventTypes,
    });
  }, [sendMessage]);

  // Auto connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    sendTypingIndicator,
    subscribe,
  };
};

export default useWebSocket;