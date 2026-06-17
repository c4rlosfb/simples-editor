import { useCallback, useEffect, useRef, useState } from "react";

export interface WsMessage {
  type: string;
  [key: string]: unknown;
}

export interface UseWebSocketReturn {
  /** Current NASM assembly code (from asm_generated message) */
  asmCode: string;
  /** Compiled code errors */
  errors: WsMessage[];
  /** Whether the compile/execution pipeline is running */
  isRunning: boolean;
  /** Connect to WebSocket and start compile & run */
  sendCode: (code: string) => void;
  /** Send stdin data to the running process */
  sendStdin: (data: string) => void;
  /** Send stop signal */
  sendStop: () => void;
  /** Connected state */
  connected: boolean;
}

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [asmCode, setAsmCode] = useState("");
  const [errors, setErrors] = useState<WsMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const connect = useCallback((code: string) => {
    // Close previous connection
    wsRef.current?.close();

    // Determine WebSocket URL
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/run`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setIsRunning(true);
      setAsmCode("");
      setErrors([]);

      // Send compile_and_run immediately
      ws.send(JSON.stringify({ type: "compile_and_run", code }));
    };

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);

        switch (msg.type) {
          case "asm_generated":
            setAsmCode((msg.asm as string) || "");
            break;
          case "compile_error":
            setErrors((prev) => [...prev, msg]);
            break;
          case "exit":
          case "timeout":
          case "internal_error":
            setIsRunning(false);
            break;
          case "compile_started":
          case "exec_started":
            break;
          case "pong":
            break;
        }
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      setIsRunning(false);
    };

    ws.onerror = () => {
      setIsRunning(false);
    };
  }, []);

  const sendCode = useCallback(
    (code: string) => {
      connect(code);
    },
    [connect]
  );

  const sendStdin = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "stdin", data }));
    }
  }, []);

  const sendStop = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "stop" }));
    }
  }, []);

  return { asmCode, errors, isRunning, sendCode, sendStdin, sendStop, connected };
}
