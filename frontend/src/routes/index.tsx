import { createRoute, redirect, useNavigate } from "@tanstack/react-router";
import { supabase } from "@/lib/supabase";
import { rootRoute } from "./__root";
import SimplesEditor, {
  type SimplesEditorHandle,
} from "@/components/SimplesEditor";
import TerminalPanel from "@/components/TerminalPanel";
import { useCallback, useEffect, useRef, useState } from "react";
import type * as Monaco from "monaco-editor";

// ── Types ───────────────────────────────────────────────────────────────────

interface CompileError {
  line: number;
  column: number;
  message: string;
  phase: string;
}

// ── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Gera um JWT de demonstração assinado com o segredo de dev.
 * Usa Web Crypto API (HMAC-SHA256) — compatível com o backend.
 */
async function createDemoToken(): Promise<string> {
  const secret = "dev-secret-do-not-use-in-prod";
  const header = { alg: "HS256", typ: "JWT" };
  const payload = {
    sub: "demo-user",
    exp: Math.floor(Date.now() / 1000) + 3600,
    email: "demo@simples-editor.local",
    role: "authenticated",
  };

  const encoder = new TextEncoder();
  const headerB64 = btoa(JSON.stringify(header))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  const payloadB64 = btoa(JSON.stringify(payload))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  const signingInput = `${headerB64}.${payloadB64}`;

  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign(
    "HMAC",
    key,
    encoder.encode(signingInput),
  );
  const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  return `${signingInput}.${sigB64}`;
}

// ── Route ───────────────────────────────────────────────────────────────────

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: IndexRoute,
  beforeLoad: async () => {
    // Modo demonstração: pula autenticação Supabase
    if (import.meta.env.VITE_DEMO_MODE === "true") {
      return;
    }
    try {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        throw redirect({ to: "/login" });
      }
    } catch (error) {
      if (error instanceof Response || (error as any)?.redirect) throw error;
      throw redirect({ to: "/login" });
    }
  },
});

// ── Component ───────────────────────────────────────────────────────────────

function IndexRoute() {
  const navigate = useNavigate();

  // Refs
  const editorRef = useRef<SimplesEditorHandle>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const monacoRef = useRef<typeof Monaco | null>(null);

  // State
  const [code, setCode] = useState("");
  const [asmOutput, setAsmOutput] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [compileErrors, setCompileErrors] = useState<CompileError[]>([]);
  const [terminalLines, setTerminalLines] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // ── Monaco global ───────────────────────────────────────────────────────

  useEffect(() => {
    const check = () => {
      const m = (window as any).monaco as typeof Monaco | undefined;
      if (m && !monacoRef.current) {
        monacoRef.current = m;
      }
    };
    check();
    const id = setInterval(check, 500);
    return () => clearInterval(id);
  }, []);

  // ── Editor markers helpers ──────────────────────────────────────────────

  const setEditorMarkers = useCallback(
    (errors: CompileError[], severity: "error" | "warning" = "error") => {
      const monaco = monacoRef.current;
      const editor = editorRef.current?.getEditor();
      if (!monaco || !editor) return;

      const model = editor.getModel();
      if (!model) return;

      const markerSeverity =
        severity === "error"
          ? monaco.MarkerSeverity.Error
          : monaco.MarkerSeverity.Warning;

      const markers = errors.map((e) => ({
        severity: markerSeverity,
        message: e.message,
        startLineNumber: Math.max(e.line || 1, 1),
        startColumn: Math.max(e.column || 1, 1),
        endLineNumber: Math.max(e.line || 1, 1),
        endColumn: (e.column || 1) + 20,
      }));

      monaco.editor.setModelMarkers(model, "simples-compile", markers);
    },
    [],
  );

  const clearEditorMarkers = useCallback(() => {
    const monaco = monacoRef.current;
    const editor = editorRef.current?.getEditor();
    if (!monaco || !editor) return;
    const model = editor.getModel();
    if (!model) return;
    monaco.editor.setModelMarkers(model, "simples-compile", []);
  }, []);

  // ── WebSocket connection ────────────────────────────────────────────────

  useEffect(() => {
    let ws: WebSocket | null = null;
    let mounted = true;

    async function connect() {
      try {
        let token: string | undefined;

        if (import.meta.env.VITE_DEMO_MODE === "true") {
          token = await createDemoToken();
        } else {
          const { data } = await supabase.auth.getSession();
          token = data.session?.access_token;
        }

        if (!token) {
          console.warn(
            "[SimplesEditor] WebSocket: sem token de autenticação disponível",
          );
          return;
        }

        const protocol =
          window.location.protocol === "https:" ? "wss:" : "ws:";
        // JWT tokens são URL-safe (base64url), não precisam de encodeURIComponent
        const wsUrl = `${protocol}//${window.location.host}/ws/run?token=${token}`;

        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!mounted) return;
          setWsConnected(true);
          setTerminalLines((prev) => [
            ...prev,
            "\x1b[1;32m✓ Conectado ao servidor de execução\x1b[0m",
          ]);
        };

        ws.onmessage = (event) => {
          if (!mounted) return;
          try {
            const msg = JSON.parse(event.data as string) as Record<
              string,
              unknown
            >;
            handleWsMessage(msg);
          } catch (e) {
            console.error(
              "[SimplesEditor] Falha ao parsear mensagem WebSocket:",
              e,
            );
          }
        };

        ws.onerror = () => {
          if (!mounted) return;
          setTerminalLines((prev) => [
            ...prev,
            "\x1b[1;31m✗ Erro de conexão WebSocket\x1b[0m",
          ]);
        };

        ws.onclose = () => {
          if (!mounted) return;
          setWsConnected(false);
          setIsExecuting(false);
          setTerminalLines((prev) => [
            ...prev,
            "\x1b[1;33m⏼ Desconectado do servidor\x1b[0m",
          ]);
        };
      } catch (e) {
        console.error(
          "[SimplesEditor] Erro ao conectar WebSocket:",
          e,
        );
      }
    }

    connect();

    return () => {
      mounted = false;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── WebSocket message handler ───────────────────────────────────────────

  const handleWsMessage = useCallback(
    (msg: Record<string, unknown>) => {
      const type = msg.type as string | undefined;

      switch (type) {
        case "compile_started":
          setTerminalLines((prev) => [
            ...prev,
            "\x1b[1;36m⏳ Compilando...\x1b[0m",
          ]);
          break;

        case "asm_generated":
          setAsmOutput((msg.asm as string) || "");
          setTerminalLines((prev) => [
            ...prev,
            "\x1b[1;32m✓ Compilação concluída (NASM gerado)\x1b[0m",
          ]);
          break;

        case "exec_started":
          setIsExecuting(true);
          setTerminalLines((prev) => [
            ...prev,
            "\x1b[1;33m▶ Executando programa...\x1b[0m",
          ]);
          break;

        case "stdout":
          setTerminalLines((prev) => [...prev, (msg.data as string) || ""]);
          break;

        case "stderr":
          setTerminalLines((prev) => [
            ...prev,
            `\x1b[1;31m${msg.data || ""}\x1b[0m`,
          ]);
          break;

        case "compile_error": {
          const rawErrors = msg.errors as
            | CompileError[]
            | undefined;
          const errors: CompileError[] = rawErrors?.length
            ? rawErrors
            : [
                {
                  line: (msg.line as number) || 0,
                  column: (msg.column as number) || 0,
                  message: (msg.message as string) || "Erro de compilação",
                  phase: (msg.phase as string) || "compiler",
                },
              ];
          setCompileErrors(errors);
          setTerminalLines((prev) => [
            ...prev,
            ...errors.map(
              (e) =>
                `\x1b[1;31m✗ Linha ${e.line}: ${e.message}\x1b[0m`,
            ),
          ]);
          setEditorMarkers(errors, "error");
          break;
        }

        case "exit":
          setIsExecuting(false);
          setTerminalLines((prev) => [
            ...prev,
            `\x1b[1;33m◼ Programa finalizado (exit ${msg.code ?? "?"}, ${msg.duration_ms ?? "?"}ms)\x1b[0m`,
          ]);
          break;

        case "timeout":
          setIsExecuting(false);
          setTerminalLines((prev) => [
            ...prev,
            `\x1b[1;31m⏱ Timeout — execução excedeu ${msg.limit_s ?? "?"}s\x1b[0m`,
          ]);
          break;

        case "internal_error":
          setTerminalLines((prev) => [
            ...prev,
            `\x1b[1;31m✗ Erro interno: ${msg.message || "desconhecido"}\x1b[0m`,
          ]);
          break;

        case "pong":
          // heartbeat — ignorar
          break;

        default:
          console.debug(
            "[SimplesEditor] Mensagem WS desconhecida:",
            type,
            msg,
          );
      }
    },
    [setEditorMarkers],
  );

  // ── Ações dos botões ────────────────────────────────────────────────────

  /** ▶ Compilar: POST /api/compile → mostra NASM no painel direito */
  const handleCompile = useCallback(async () => {
    const currentCode = editorRef.current?.getValue() || code;
    if (!currentCode.trim()) return;

    setIsCompiling(true);
    setAsmOutput(null);
    setCompileErrors([]);
    clearEditorMarkers();

    try {
      const res = await fetch("/api/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: currentCode }),
      });

      const data = (await res.json()) as {
        success: boolean;
        asm?: string;
        errors?: CompileError[];
      };

      if (data.success) {
        setAsmOutput(data.asm || "");
      } else {
        const errors: CompileError[] = data.errors?.length
          ? data.errors
          : [
              {
                line: 0,
                column: 0,
                message: "Erro de compilação desconhecido",
                phase: "compiler",
              },
            ];
        setCompileErrors(errors);
        setEditorMarkers(errors, "error");
      }
    } catch (e) {
      console.error("[SimplesEditor] Erro na compilação:", e);
      const netErr: CompileError = {
        line: 0,
        column: 0,
        message: `Erro de rede: ${e instanceof Error ? e.message : String(e)}`,
        phase: "network",
      };
      setCompileErrors([netErr]);
      setEditorMarkers([netErr], "error");
    } finally {
      setIsCompiling(false);
    }
  }, [code, clearEditorMarkers, setEditorMarkers]);

  /** ■ Parar: envia {"type":"stop"} pelo WebSocket */
  const handleStop = useCallback(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN && isExecuting) {
      ws.send(JSON.stringify({ type: "stop" }));
      setTerminalLines((prev) => [
        ...prev,
        "\x1b[1;33m⏹ Parando execução...\x1b[0m",
      ]);
    }
  }, [isExecuting]);

  /** Terminal input: se está executando → stdin; senão → dispara run */
  const handleTerminalInput = useCallback(
    (data: string) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;

      if (isExecuting) {
        // Programa rodando → envia stdin
        ws.send(JSON.stringify({ type: "stdin", data }));
      } else {
        // Nenhum programa rodando → dispara compile_and_run
        const currentCode = editorRef.current?.getValue() || code;
        if (!currentCode.trim()) return;
        setTerminalLines((prev) => [
          ...prev,
          `\x1b[1;36m$ ${data.trim() || "run"}\x1b[0m`,
        ]);
        ws.send(
          JSON.stringify({ type: "compile_and_run", code: currentCode }),
        );
      }
    },
    [code, isExecuting],
  );

  /** Logout */
  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate({ to: "/login" });
  };

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-cyan-400">
            Simples Editor
          </h1>
          <span className="text-xs text-gray-600">|</span>
          <span className="text-xs text-gray-500">
            SIMPLES → NASM → ELF i386
          </span>
          {wsConnected && (
            <span className="text-xs text-green-500" title="WebSocket conectado">
              ●
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm rounded transition-colors"
          >
            {isCompiling ? "⏳ Compilando..." : "▶ Compilar"}
          </button>
          <button
            onClick={handleStop}
            disabled={!isExecuting}
            className="px-3 py-1 bg-red-800 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm rounded transition-colors"
          >
            ■ Parar
          </button>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Sair
          </button>
        </div>
      </header>

      {/* Main content: Editor + NASM (top), Terminal (bottom) */}
      <main className="flex-1 flex flex-col min-h-0">
        {/* Top row: Editor + NASM */}
        <div className="flex-1 flex min-h-0">
          {/* Editor */}
          <div className="flex-1 border-r border-gray-800 flex flex-col">
            <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
              Editor SIMPLES
              {compileErrors.length > 0 && (
                <span className="ml-2 text-red-400">
                  ({compileErrors.length} erro{compileErrors.length > 1 ? "s" : ""})
                </span>
              )}
            </div>
            <div className="flex-1">
              <SimplesEditor ref={editorRef} onChange={setCode} />
            </div>
          </div>

          {/* NASM Panel */}
          <div className="w-1/2 flex flex-col">
            <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
              NASM x86 (i386)
              {asmOutput !== null && (
                <span className="ml-2 text-green-400">
                  ({asmOutput.length} bytes)
                </span>
              )}
            </div>
            <div className="flex-1 bg-gray-950 p-4 font-mono text-sm text-gray-400 overflow-auto">
              {asmOutput ? (
                <pre className="whitespace-pre-wrap text-green-300/80">
                  {asmOutput}
                </pre>
              ) : compileErrors.length > 0 ? (
                <div className="text-red-400 space-y-1">
                  {compileErrors.map((e, i) => (
                    <div key={i}>
                      <span className="text-red-300">Erro</span>{" "}
                      {e.line > 0 && (
                        <span className="text-gray-500">Linha {e.line}:</span>
                      )}{" "}
                      {e.message}
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-gray-600">
                  ; Compile seu código SIMPLES para ver o assembly gerado aqui
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Bottom: Terminal */}
        <div className="h-48 border-t border-gray-800 flex flex-col shrink-0">
          <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider flex items-center justify-between">
            <span>Terminal</span>
            <span className="text-gray-600">
              {isExecuting
                ? "Executando..."
                : wsConnected
                  ? "Digite para executar"
                  : "Desconectado"}
            </span>
          </div>
          <div className="flex-1">
            <TerminalPanel
              lines={terminalLines}
              onInput={handleTerminalInput}
              interactive={wsConnected}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
