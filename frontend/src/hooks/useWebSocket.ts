import { useEffect, useCallback, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { setConnectionStatus, addMessage, setError } from '../store/chatSlice';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const useWebSocket = () => {
  const ws = useRef<WebSocket | null>(null);
  const dispatch = useDispatch();
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      // 使用相对路径，让Vite代理处理
      ws.current = new WebSocket('ws://' + window.location.host + '/ws');

      ws.current.onopen = () => {
        console.log('WebSocket连接已建立');
        dispatch(setConnectionStatus(true));
        dispatch(setError(null));
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
          reconnectTimeout.current = undefined;
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket连接已关闭');
        dispatch(setConnectionStatus(false));
        // 尝试重新连接
        reconnectTimeout.current = setTimeout(() => {
          console.log('尝试重新连接...');
          connect();
        }, 3000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket错误:', error);
        dispatch(setError('连接错误'));
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.role && data.content) {
            dispatch(addMessage(data as Message));
          }
        } catch (error) {
          console.error('消息解析错误:', error);
        }
      };
    } catch (error) {
      console.error('WebSocket连接错误:', error);
      dispatch(setError('连接失败'));
    }
  }, [dispatch]);

  const sendMessage = useCallback((message: Message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket未连接');
      dispatch(setError('消息发送失败：未连接到服务器'));
    }
  }, [dispatch]);

  useEffect(() => {
    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, [connect]);

  return { sendMessage };
}; 