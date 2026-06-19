import { useCallback, useEffect, useRef, useState } from "react";
import Editor, { BeforeMount, OnMount } from "@monaco-editor/react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import type { ImperativePanelHandle } from "react-resizable-panels";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";

import {
  LANGUAGE_ID,
  registerSimplesLanguageWith,
  SIMPLES_EDITOR_OPTIONS,
} from "./lib/simples-language";
import type * as Monaco from "monaco-editor";

// ── Types ────────────────────────────────────────────────────────────────

interface CompileError {
  line: number;
  column: number;
  message: string;
  phase: string;
}

interface Example {
  label: string;
  code: string;
}

// ── Constants ─────────────────────────────────────────────────────────────

const DEFAULT_CODE = `programa exemplo
inicio
  escreva("Ola mundo!");
fim`;

const EXAMPLES: Example[] = [
  {
    label: "Hello World",
    code: `programa hello
inicio
  escreva("Ola mundo!");
fim`,
  },
  {
    label: "Fatorial",
    code: `programa fatorial
  inteiro n, fat, i;
inicio
  leia n;
  fat <- 1;
  para i de 1 ate n passo 1 faca
    fat <- fat * i;
  fimpara
  escreval(fat);
fim`,
  },
  {
    label: "Fibonacci",
    code: `programa fibonacci
  inteiro n, a, b, temp, i;
inicio
  leia n;
  a <- 0;
  b <- 1;
  se n >= 1 entao
    escreva(a);
  fimse
  se n >= 2 entao
    escreva(b);
  fimse
  para i de 3 ate n passo 1 faca
    temp <- a + b;
    escreva(temp);
    a <- b;
    b <- temp;
  fimpara
fim`,
  },
  {
    label: "Tabuada",
    code: `programa tabuada
  inteiro n, i;
inicio
  leia n;
  para i de 1 ate 10 passo 1 faca
    escreva(n);
    escreva(" x ");
    escreva(i);
    escreva(" = ");
    escreval(n * i);
  fimpara
fim`,
  },
];

// ── Terminal Theme ────────────────────────────────────────────────────────

const TERMINAL_THEME = {
  background: "#1e1e2e",
  foreground: "#d4d4d4",
  cursor: "#22d3ee",
  cursorAccent: "#1e1e2e",
  selectionBackground: "#22d3ee33",
  black: "#1e1e2e",
  red: "#f44747",
  green: "#4ade80",
  yellow: "#fde047",
  blue: "#569cd6",
  magenta: "#c084fc",
  cyan: "#22d3ee",
  white: "#e5e7eb",
};

// ── App Component ─────────────────────────────────────────────────────────

function App() {
  // Refs
  const editorRef = useRef<import("monaco-editor").editor.IStandaloneCodeEditor | null>(null);
  const nasmPanelRef = useRef<ImperativePanelHandle>(null);
  const monacoRef = useRef<typeof Monaco | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const examplesRef = useRef<HTMLDivElement>(null);

  // Refs para evitar stale closures nos callbacks do terminal/WebSocket
  const handleRunRef = useRef<() => void>(() => {});
  const isExecutingRef = useRef(false);
  const handleWsMessageRef = useRef<(msg: Record<string, unknown>) => void>(() => {});

  // State
  const [code, setCode] = useState(DEFAULT_CODE);
  const [asmOutput, setAsmOutput] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [compileErrors, setCompileErrors] = useState<CompileError[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [examplesOpen, setExamplesOpen] = useState(false);

  // ── Monaco Language Registration ───────────────────────────────────────

  const handleBeforeMount: BeforeMount = useCallback((monaco) => {
    monacoRef.current = monaco;
    registerSimplesLanguageWith(monaco);
  }, []);

  const handleOnMount: OnMount = useCallback((editor) => {
    editorRef.current = editor;
    editor.focus();
  }, []);

  // ── Editor Markers ─────────────────────────────────────────────────────

  const setEditorMarkers = useCallback(
    (errors: CompileError[]) => {
      const monaco = monacoRef.current;
      const editor = editorRef.current;
      if (!monaco || !editor) return;
      const model = editor.getModel();
      if (!model) return;

      monaco.editor.setModelMarkers(model, "simples-compile",
        errors.map((e) => ({
          severity: monaco.MarkerSeverity.Error,
          message: e.message,
          startLineNumber: Math.max(e.line || 1, 1),
          startColumn: Math.max(e.column || 1, 1),
          endLineNumber: Math.max(e.line || 1, 1),
          endColumn: (e.column || 1) + 20,
        }))
      );
    },
    [],
  );

  const clearEditorMarkers = useCallback(() => {
    const monaco = monacoRef.current;
    const editor = editorRef.current;
    if (!monaco || !editor) return;
    const model = editor.getModel();
    if (!model) return;
    monaco.editor.setModelMarkers(model, "simples-compile", []);
  }, []);

  // ── Terminal Setup ─────────────────────────────────────────────────────

  useEffect(() => {
    if (!terminalRef.current) return;
    const term = new Terminal({
      theme: TERMINAL_THEME,
      fontSize: 14,
      fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
      cursorBlink: true,
      cursorStyle: "bar",
      scrollback: 5000,
    });

    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(terminalRef.current);
    fit.fit();

    termRef.current = term;
    fitRef.current = fit;

    // Banner inicial (bordas alinhadas, 44 colunas)
    const W = 44;
    const stripAnsi = (s: string) => s.replace(/\x1b\[[0-9;]*m/g, "");
    const boxTop = "\x1b[1;36m┌" + "─".repeat(W-2) + "┐\x1b[0m";
    const boxBot = "\x1b[1;36m└" + "─".repeat(W-2) + "┘\x1b[0m";
    const pad = (text: string) => {
      const visible = stripAnsi(text);
      const inner = W - 2;
      const padding = Math.max(0, inner - visible.length - 1);
      return "\x1b[1;36m│\x1b[0m " + text + " ".repeat(padding) + "\x1b[1;36m│\x1b[0m";
    };

    term.writeln(boxTop);
    term.writeln(pad("\x1b[1;33mSimples Editor — Terminal Interativo\x1b[0m"));
    term.writeln(pad("Aguardando conexão com o servidor..."));
    term.writeln(boxBot);
    term.write("\x1b[?25l");

    let inputBuffer = "";

    term.onData((data) => {
      if (data === "\r" || data === "\n") {
        const line = inputBuffer;
        term.write("\r\n");
        if (line.trim() === "run") {
          handleRunRef.current();
        } else if (wsRef.current?.readyState === WebSocket.OPEN) {
          if (isExecutingRef.current) {
            wsRef.current.send(JSON.stringify({ type: "stdin", data: line + "\n" }));
          } else {
            term.writeln("\x1b[1;33mExecute com 'run' ou ▶ Compilar\x1b[0m");
          }
        }
        inputBuffer = "";
        term.write("$ ");
        return;
      }
      if (data === "\x7f" || data === "\b") {
        if (inputBuffer.length > 0) {
          inputBuffer = inputBuffer.slice(0, -1);
          term.write("\b \b");
        }
        return;
      }
      if (data >= " ") {
        inputBuffer += data;
        term.write(data);
      }
    });

    // Resize
    const observer = new ResizeObserver(() => {
      try { fitRef.current?.fit(); } catch { /* ignore */ }
    });
    observer.observe(terminalRef.current);

    return () => {
      observer.disconnect();
      term.dispose();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── WebSocket Connection ────────────────────────────────────────────────

  useEffect(() => {
    let ws: WebSocket | null = null;
    let mounted = true;

    async function connect() {
      const token = await createDemoToken();
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws/run?token=${token}`;

      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mounted) return;
        setWsConnected(true);
        // Limpa banner de "Aguardando" e mostra prompt ativo
        const term = termRef.current;
        if (term) {
          term.write("\x1b[?25h"); // mostra cursor
          term.writeln("\x1b[1;32m✓ Conectado ao servidor\x1b[0m");
          term.write("$ ");
        }
      };

      ws.onmessage = (event) => {
        if (!mounted) return;
        try {
          const msg = JSON.parse(event.data as string);
          handleWsMessageRef.current(msg);
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        if (!mounted) return;
        setWsConnected(false);
        setIsExecuting(false);
        const term = termRef.current;
        if (term) {
          term.write("\x1b[?25l"); // esconde cursor
          term.writeln("\x1b[1;33m⏼ Desconectado do servidor\x1b[0m");
        }
      };
      ws.onerror = () => {
        if (!mounted) return;
        const term = termRef.current;
        if (term) {
          term.writeln("\x1b[1;31m✗ Erro de conexão com servidor\x1b[0m");
        }
      };
    }

    connect();
    return () => { mounted = false; ws?.close(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleWsMessage = useCallback((msg: Record<string, unknown>) => {
    const type = msg.type as string;

    switch (type) {
      case "compile_started":
        termRef.current?.writeln("\x1b[1;36m⏳ Compilando...\x1b[0m");
        break;

      case "asm_generated":
        setAsmOutput((msg.asm as string) || "");
        termRef.current?.writeln("\x1b[1;32m✓ Compilação concluída (NASM gerado)\x1b[0m");
        break;

      case "exec_started":
        setIsExecuting(true);
        termRef.current?.writeln("\x1b[1;33m▶ Executando programa...\x1b[0m");
        break;

      case "stdout":
        termRef.current?.write((msg.data as string) || "");
        break;

      case "stderr":
        termRef.current?.writeln(`\x1b[1;31m${msg.data || ""}\x1b[0m`);
        break;

      case "compile_error": {
        const rawErrors = msg.errors as CompileError[] | undefined;
        const errors: CompileError[] = rawErrors?.length ? rawErrors : [{
          line: (msg.line as number) || 0,
          column: (msg.column as number) || 0,
          message: (msg.message as string) || "Erro de compilação",
          phase: (msg.phase as string) || "compiler",
        }];
        setCompileErrors(errors);
        setEditorMarkers(errors);
        errors.forEach((e) => termRef.current?.writeln(`\x1b[1;31m✗ Linha ${e.line}: ${e.message}\x1b[0m`));
        break;
      }

      case "exit":
        setIsExecuting(false);
        termRef.current?.writeln(`\x1b[1;33m◼ Programa finalizado (exit ${msg.code ?? "?"}, ${msg.duration_ms ?? "?"}ms)\x1b[0m`);
        break;

      case "timeout":
        setIsExecuting(false);
        termRef.current?.writeln(`\x1b[1;31m⏱ Timeout — execução excedeu ${msg.limit_s ?? "?"}s\x1b[0m`);
        break;

      case "internal_error":
        termRef.current?.writeln(`\x1b[1;31m✗ Erro interno: ${msg.message || "desconhecido"}\x1b[0m`);
        break;
    }
  }, [setEditorMarkers]);

  // Sincroniza refs para evitar stale closures
  handleWsMessageRef.current = handleWsMessage;

  // Sincroniza isExecuting com a ref (usada no terminal e WebSocket)
  useEffect(() => {
    isExecutingRef.current = isExecuting;
  }, [isExecuting]);

  // ── Actions ─────────────────────────────────────────────────────────────

  const handleRun = useCallback(() => {
    const currentCode = editorRef.current?.getValue() || code;
    if (!currentCode.trim()) return;

    setIsCompiling(true);
    setAsmOutput(null);
    setCompileErrors([]);
    clearEditorMarkers();

    // First, compile via REST
    fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: currentCode }),
    })
      .then((res) => res.json())
      .then((data: { success: boolean; asm?: string; errors?: CompileError[] }) => {
        if (data.success) {
          setAsmOutput(data.asm || "");
          // Now execute via WebSocket
          const ws = wsRef.current;
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "compile_and_run", code: currentCode }));
          }
        } else {
          const errors = data.errors?.length ? data.errors : [{
            line: 0, column: 0, message: "Erro de compilação", phase: "compiler",
          }];
          setCompileErrors(errors);
          setEditorMarkers(errors);
        }
      })
      .catch((e) => {
        setCompileErrors([{
          line: 0, column: 0,
          message: `Erro de rede: ${e instanceof Error ? e.message : String(e)}`,
          phase: "network",
        }]);
      })
      .finally(() => setIsCompiling(false));
  }, [code, clearEditorMarkers, setEditorMarkers]);

  // Sincroniza ref para evitar stale closure no terminal
  handleRunRef.current = handleRun;

  const handleStop = useCallback(() => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN && isExecutingRef.current) {
      ws.send(JSON.stringify({ type: "stop" }));
      termRef.current?.writeln("\x1b[1;33m⏹ Parando execução...\x1b[0m");
    }
  }, []);

  const handleClear = useCallback(() => {
    termRef.current?.clear();
    termRef.current?.writeln("\x1b[1;36m┌─────────────────────────────────────────┐\x1b[0m");
    termRef.current?.writeln("\x1b[1;36m│\x1b[0m  \x1b[1;33mSimples Editor — Terminal Interativo\x1b[0m     \x1b[1;36m│\x1b[0m");
    termRef.current?.writeln("\x1b[1;36m└─────────────────────────────────────────┘\x1b[0m");
    termRef.current?.write("$ ");
    setAsmOutput(null);
    setCompileErrors([]);
    clearEditorMarkers();
  }, [clearEditorMarkers]);

  const handleSelectExample = useCallback((example: Example) => {
    editorRef.current?.setValue(example.code);
    setCode(example.code);
    setExamplesOpen(false);
  }, []);

  // Close examples dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (examplesRef.current && !examplesRef.current.contains(e.target as Node)) {
        setExamplesOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Double-click to collapse/expand NASM panel
  const handleNasmSplitterDoubleClick = useCallback(() => {
    const panel = nasmPanelRef.current;
    if (!panel) return;
    if (panel.isCollapsed()) {
      panel.expand();
    } else {
      panel.collapse();
    }
  }, []);

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-cyan-400">Simples Editor</h1>
          <span className="text-xs text-gray-600">|</span>
          <span className="text-xs text-gray-500">SIMPLES → NASM → ELF i386</span>
          {wsConnected && (
            <span className="text-xs text-green-500" title="WebSocket conectado">●</span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Examples dropdown */}
          <div className="relative" ref={examplesRef}>
            <button
              onClick={() => setExamplesOpen((p) => !p)}
              className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-sm rounded transition-colors flex items-center gap-1"
            >
              exemplos ▾
            </button>
            {examplesOpen && (
              <div className="absolute right-0 mt-1 w-48 bg-gray-800 border border-gray-700 rounded-md shadow-lg z-50 overflow-hidden">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.label}
                    onClick={() => handleSelectExample(ex)}
                    className="block w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={handleRun}
            disabled={isCompiling}
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm rounded transition-colors"
          >
            {isCompiling ? "⏳ Compilando..." : "▶ Compilar"}
          </button>

          <button
            onClick={handleStop}
            disabled={!isExecuting}
            className="px-3 py-1 bg-red-900 hover:bg-red-800 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed text-sm rounded transition-colors text-red-200"
          >
            ■ Parar
          </button>

          <button
            onClick={handleClear}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-sm rounded transition-colors"
            title="Limpar terminal, NASM e erros"
          >
            Limpar
          </button>
        </div>
      </header>

      {/* Main content: Editor + NASM (top), Terminal (bottom) */}
      <main className="flex-1 flex flex-col min-h-0">
        <PanelGroup direction="vertical" className="flex-1">
          {/* Top row: Editor + NASM */}
          <Panel defaultSize={75} minSize={30}>
            <PanelGroup direction="horizontal">
              {/* Editor SIMPLES */}
              <Panel defaultSize={60} minSize={20}>
                <div className="h-full flex flex-col">
                  <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                    Editor SIMPLES
                    {compileErrors.length > 0 && (
                      <span className="ml-2 text-red-400">
                        ({compileErrors.length} erro{compileErrors.length > 1 ? "s" : ""})
                      </span>
                    )}
                  </div>
                  <div className="flex-1">
                    <Editor
                      defaultLanguage={LANGUAGE_ID}
                      value={code}
                      theme="simples-dark"
                      beforeMount={handleBeforeMount}
                      onMount={handleOnMount}
                      onChange={(v) => setCode(v || "")}
                      options={{
                        ...SIMPLES_EDITOR_OPTIONS,
                        readOnly: isCompiling || isExecuting,
                      }}
                    />
                  </div>
                </div>
              </Panel>

              {/* Vertical splitter */}
              <PanelResizeHandle
                className="w-1 bg-gray-800 hover:bg-cyan-600 active:bg-cyan-500 transition-colors cursor-col-resize"
                onDoubleClick={handleNasmSplitterDoubleClick}
              />

              {/* NASM Panel */}
              <Panel
                ref={nasmPanelRef}
                defaultSize={40}
                minSize={0}
                collapsible={true}
                collapsedSize={0}
              >
                <div className="h-full flex flex-col">
                  <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                    NASM x86 (i386)
                    {asmOutput !== null && (
                      <span className="ml-2 text-green-400">({asmOutput.length} bytes)</span>
                    )}
                  </div>
                  <div className="flex-1">
                    {asmOutput !== null ? (
                      <Editor
                        value={asmOutput}
                        language="asm"
                        theme="vs-dark"
                        options={{
                          readOnly: true,
                          fontSize: 13,
                          fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                          minimap: { enabled: false },
                          lineNumbers: "off",
                          renderWhitespace: "none",
                          scrollBeyondLastLine: false,
                          wordWrap: "off",
                          glyphMargin: false,
                          folding: false,
                          lineDecorationsWidth: 0,
                          lineNumbersMinChars: 0,
                          padding: { top: 8, bottom: 8 },
                          domReadOnly: true,
                          contextmenu: false,
                          overviewRulerLanes: 0,
                          hideCursorInOverviewRuler: true,
                          overviewRulerBorder: false,
                          renderLineHighlight: "none",
                          occurrencesHighlight: false,
                          selectionHighlight: false,
                          matchBrackets: "never",
                        }}
                      />
                    ) : compileErrors.length > 0 ? (
                      <div className="flex-1 bg-gray-950 p-4 overflow-auto">
                        <div className="text-red-400 space-y-1 font-mono text-sm">
                          {compileErrors.map((e, i) => (
                            <div key={i}>
                              <span className="text-red-300">Erro</span>{" "}
                              {e.line > 0 && <span className="text-gray-500">Linha {e.line}:</span>}{" "}
                              {e.message}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 bg-gray-950 flex items-center justify-center">
                        <span className="text-gray-600 text-sm font-mono">
                          ; Compile seu código SIMPLES para ver o assembly gerado aqui
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </Panel>
            </PanelGroup>
          </Panel>

          {/* Horizontal splitter */}
          <PanelResizeHandle className="h-1 bg-gray-800 hover:bg-cyan-600 active:bg-cyan-500 transition-colors cursor-row-resize" />

          {/* Bottom: Terminal */}
          <Panel defaultSize={25} minSize={12}>
            <div className="h-full border-t border-gray-800 flex flex-col">
              <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider flex items-center justify-between">
                <span>Terminal</span>
                <span className={wsConnected ? "text-green-400" : "text-yellow-500"}>
                  {isExecuting ? "Executando..." : wsConnected ? "Conectado" : "Desconectado"}
                </span>
              </div>
              <div ref={terminalRef} className="flex-1" style={{ background: "#1e1e2e" }} />
            </div>
          </Panel>
        </PanelGroup>
      </main>
    </div>
  );
}

// ── Demo JWT Helper ───────────────────────────────────────────────────────

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
  const headerB64 = btoa(JSON.stringify(header)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const payloadB64 = btoa(JSON.stringify(payload)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const signingInput = `${headerB64}.${payloadB64}`;

  const key = await crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(signingInput));
  const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

  return `${signingInput}.${sigB64}`;
}

export default App;
