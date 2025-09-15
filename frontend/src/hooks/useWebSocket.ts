import { useEffect, useState, useRef } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
) => {
  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options;

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isManualClose = useRef(false);

  const connect = () => {
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('WebSocket连接已建立');
        setSocket(ws);
        setReadyState(ws.readyState);
        setReconnectAttempts(0);
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason);
        setSocket(null);
        setReadyState(ws.readyState);
        onClose?.();

        // 如果不是手动关闭且未达到最大重连次数，则尝试重连
        if (!isManualClose.current && reconnectAttempts < maxReconnectAttempts) {
          console.log(`尝试重连... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
          setReconnectAttempts(prev => prev + 1);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        onError?.(error);
      };

    } catch (error) {
      console.error('创建WebSocket连接失败:', error);
    }
  };

  const disconnect = () => {
    isManualClose.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socket) {
      socket.close();
    }
  };

  const sendMessage = (message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket未连接，无法发送消息');
    }
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [url]);

  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    socket,
    lastMessage,
    readyState,
    sendMessage,
    connect,
    disconnect,
    isConnected: readyState === WebSocket.OPEN,
    reconnectAttempts,
  };
};
