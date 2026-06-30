import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useAuth } from './AuthContext';

type SocketMessageListener = (data: any) => void;

interface SocketContextType {
  isConnected: boolean;
  sendMessage: (action: string, payload: Record<string, any>) => void;
  registerListener: (event: string, callback: SocketMessageListener) => () => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export const SocketProvider = ({ children }: { children: React.ReactNode }) => {
  const { user, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const socketRef = useRef<WebSocket | null>(null);
  // Maps event names (e.g. 'new_message', 'question_analyzed') to lists of callbacks
  const listenersRef = useRef<Record<string, SocketMessageListener[]>>({});

  useEffect(() => {
    // Connect only if authenticated
    if (!isAuthenticated || !user) {
      if (socketRef.current) {
        socketRef.current.close();
      }
      setIsConnected(false);
      return;
    }

    let reconnectTimer: any;
    const connect = () => {
      const accessToken = localStorage.getItem('access_token');
      if (!accessToken) return;

      // Build websocket url using current host context or VITE_WS_URL env variable
      const customWsUrl = import.meta.env.VITE_WS_URL as string;
      let wsUrl: string;
      if (customWsUrl) {
        // Convert HTTP/HTTPS URLs to WS/WSS protocols, or prepend wss:// if it is a raw hostname
        const normalizedWsUrl = customWsUrl.startsWith('http')
          ? customWsUrl.replace(/^http/, 'ws')
          : `wss://${customWsUrl}`;
        wsUrl = `${normalizedWsUrl}/ws/${user.id}?token=${accessToken}`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${protocol}//${host}/ws/${user.id}?token=${accessToken}`;
      }

      console.log(`Connecting to WebSocket: ${wsUrl}`);
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('WebSocket connection established.');
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const eventName = payload.event;
          
          if (eventName && listenersRef.current[eventName]) {
            // Distribute event data to all active registered callbacks
            listenersRef.current[eventName].forEach((callback) => {
              try {
                callback(payload);
              } catch (err) {
                console.error('Error executing socket listener callback:', err);
              }
            });
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message payload:', err);
        }
      };

      socket.onclose = (event) => {
        setIsConnected(false);
        socketRef.current = null;
        console.log(`WebSocket connection closed (code: ${event.code}). Reconnecting in 3s...`);
        // Backoff reconnect
        reconnectTimer = setTimeout(connect, 3000);
      };

      socket.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        socket.close();
      };
    };

    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.onclose = null; // Prevent reconnect loop on clean unmount
        socketRef.current.close();
      }
      clearTimeout(reconnectTimer);
    };
  }, [user, isAuthenticated]);

  const sendMessage = (action: string, payload: Record<string, any>) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ action, ...payload }));
    } else {
      console.warn('Cannot send WebSocket message: Socket is not active.');
    }
  };

  const registerListener = (event: string, callback: SocketMessageListener) => {
    if (!listenersRef.current[event]) {
      listenersRef.current[event] = [];
    }
    listenersRef.current[event].push(callback);

    // Return cleanup function to unsubscribe easily on component unmount
    return () => {
      if (listenersRef.current[event]) {
        listenersRef.current[event] = listenersRef.current[event].filter(
          (cb) => cb !== callback
        );
      }
    };
  };

  return (
    <SocketContext.Provider value={{ isConnected, sendMessage, registerListener }}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (context === undefined) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};
