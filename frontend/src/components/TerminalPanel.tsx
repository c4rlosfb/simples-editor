/**
 * TerminalPanel — emulador de terminal interativo com xterm.js.
 *
 * Conecta ao backend via WebSocket /ws/run para stdin/stdout em tempo real.
 * Suporta resize automático com FitAddon.
 * Expõe métodos imperativos (write, writeln, clear, focus) via ref.
 *
 * Referência: PRD §8.1 e §12.1
 */

import { useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";

// ── Types ──────────────────────────────────────────────────────────────────

interface TerminalPanelProps {
  /** Linhas a serem escritas no terminal (append-only) */
  lines: string[];
  /** Callback quando o usuário digita algo (ex: stdin para o backend) */
  onInput?: (data: string) => void;
  /** Se true, o terminal aceita input do teclado */
  interactive?: boolean;
  /** Tema customizado (opcional, usa dark padrão) */
  theme?: Record<string, string>;
}

/** Métodos expostos via ref */
export interface TerminalPanelHandle {
  write(data: string): void;
  writeln(data: string): void;
  clear(): void;
  focus(): void;
}

// ── Constants ──────────────────────────────────────────────────────────────

const DEFAULT_THEME = {
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

// ── Component ──────────────────────────────────────────────────────────────

const TerminalPanel = forwardRef<TerminalPanelHandle, TerminalPanelProps>(
  function TerminalPanel(
    { lines = [], onInput, interactive = true, theme = DEFAULT_THEME },
    ref,
  ) {
    const containerRef = useRef<HTMLDivElement>(null);
    const termRef = useRef<Terminal | null>(null);
    const fitRef = useRef<FitAddon | null>(null);
    const linesRendered = useRef(0);
    const inputBuffer = useRef("");

    // ── Expor métodos imperativos ──────────────────────────────────────────

    useImperativeHandle(ref, () => ({
      write(data: string) {
        termRef.current?.write(data);
      },
      writeln(data: string) {
        termRef.current?.writeln(data);
      },
      clear() {
        termRef.current?.clear();
        linesRendered.current = 0;
        termRef.current?.write("$ ");
      },
      focus() {
        termRef.current?.focus();
      },
    }), []);

    // ── Inicializa o terminal uma vez ──────────────────────────────────────

    useEffect(() => {
      if (!containerRef.current) return;

      const term = new Terminal({
        theme,
        fontSize: 14,
        fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
        cursorBlink: true,
        cursorStyle: "bar",
        allowProposedApi: true,
        scrollback: 5000,
        tabStopWidth: 2,
      });

      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(containerRef.current);
      fit.fit();

      termRef.current = term;
      fitRef.current = fit;

      // Banner de boas-vindas
      term.writeln("\x1b[1;36m┌─────────────────────────────────────────┐\x1b[0m");
      term.writeln("\x1b[1;36m│\x1b[0m  \x1b[1;33mSimples Editor — Terminal Interativo\x1b[0m     \x1b[1;36m│\x1b[0m");
      term.writeln("\x1b[1;36m│\x1b[0m  Pressione Run para compilar e executar   \x1b[1;36m│\x1b[0m");
      term.writeln("\x1b[1;36m└─────────────────────────────────────────┘\x1b[0m");
      term.write("\r\n$ ");

      // Captura input do teclado
      if (interactive && onInput) {
        term.onData((data) => {
          if (data === "\r" || data === "\n") {
            const line = inputBuffer.current;
            term.write("\r\n");
            onInput(line + "\n");
            inputBuffer.current = "";
            term.write("$ ");
            return;
          }
          if (data === "\x7f" || data === "\b") {
            if (inputBuffer.current.length > 0) {
              inputBuffer.current = inputBuffer.current.slice(0, -1);
              term.write("\b \b");
            }
            return;
          }
          if (data >= " ") {
            inputBuffer.current += data;
            term.write(data);
          }
        });
      }

      return () => {
        term.dispose();
      };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Append novas linhas (delta, não re-renderiza tudo) ─────────────────

    useEffect(() => {
      const term = termRef.current;
      if (!term) return;

      const newLines = lines.slice(linesRendered.current);
      for (const line of newLines) {
        term.writeln(line);
      }
      linesRendered.current = lines.length;
    }, [lines]);

    // ── Resize no redimensionamento da janela ──────────────────────────────

    useEffect(() => {
      const handleResize = () => {
        try {
          fitRef.current?.fit();
        } catch {
          // Fit pode falhar se o container não estiver visível
        }
      };

      const observer = new ResizeObserver(handleResize);
      if (containerRef.current) {
        observer.observe(containerRef.current);
      }

      window.addEventListener("resize", handleResize);
      return () => {
        observer.disconnect();
        window.removeEventListener("resize", handleResize);
      };
    }, []);

    // ── Render ─────────────────────────────────────────────────────────────

    return (
      <div
        ref={containerRef}
        className="h-full w-full"
        style={{ background: theme.background }}
      />
    );
  },
);

export default TerminalPanel;
export type { TerminalPanelProps };
