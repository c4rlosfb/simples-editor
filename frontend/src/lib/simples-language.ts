/**
 * Registro da linguagem SIMPLES no Monaco Editor.
 *
 * Configura o tokenizer Monarch e o tema dark customizado.
 * Deve ser importado ANTES de criar instâncias do Monaco Editor.
 *
 * Referência: PRD §13.1 e §13.2
 */

import type { editor, languages } from "monaco-editor";
import { simplesLanguage } from "./simples-monarch";

const LANGUAGE_ID = "simples";

let registered = false;

/**
 * Registra a linguagem SIMPLES no Monaco Editor.
 *
 * Idempotente — só executa na primeira chamada.
 */
export function registerSimplesLanguage(): void {
  if (registered) return;

  const monaco = getMonaco();

  // 1. Registra a linguagem
  monaco.languages.register({ id: LANGUAGE_ID });

  // 2. Configura o tokenizer Monarch
  monaco.languages.setMonarchTokensProvider(LANGUAGE_ID, simplesLanguage);

  // 3. Tema dark customizado
  monaco.editor.defineTheme("simples-dark", createSimplesDarkTheme());

  registered = true;
}

/**
 * Cria a definição do tema dark "simples-dark".
 *
 * Keywords em ciano, números em laranja, strings em verde,
 * comentários em cinza, identificadores neutros.
 */
function createSimplesDarkTheme(): editor.IStandaloneThemeData {
  return {
    base: "vs-dark",
    inherit: true,
    rules: [
      // Keywords SIMPLES
      { token: "keyword", foreground: "#22d3ee", fontStyle: "bold" },       // ciano
      // Operadores
      { token: "operator", foreground: "#c084fc" },                          // roxo
      // Números
      { token: "number", foreground: "#fb923c" },                            // laranja
      { token: "number.float", foreground: "#fb923c" },                      // laranja
      // Strings
      { token: "string", foreground: "#4ade80" },                            // verde
      // Comentários
      { token: "comment", foreground: "#6b7280", fontStyle: "italic" },      // cinza
      // Identificadores
      { token: "identifier", foreground: "#e5e7eb" },                        // cinza claro
      // Delimitadores
      { token: "delimiter", foreground: "#9ca3af" },                         // cinza médio
      // Type annotations (futuro)
      { token: "type", foreground: "#67e8f9" },                              // ciano claro
      // Funções (procedimentos)
      { token: "function", foreground: "#fde047" },                          // amarelo
    ],
    colors: {
      "editor.background": "#0a0a0a",
      "editor.foreground": "#e5e7eb",
      "editor.lineHighlightBackground": "#1f293722",
      "editor.selectionBackground": "#22d3ee33",
      "editorCursor.foreground": "#22d3ee",
      "editorLineNumber.foreground": "#4b5563",
      "editorLineNumber.activeForeground": "#9ca3af",
      "editorGutter.background": "#0a0a0a",
      "editor.selectionHighlightBackground": "#22d3ee22",
      "editorBracketMatch.background": "#22d3ee22",
      "editorBracketMatch.border": "#22d3ee44",
    },
  };
}

/**
 * Helper para obter a instância global do Monaco.
 *
 * Em ambiente com @monaco-editor/react, a instância está disponível
 * via `loader.config({ monaco })`.
 */
function getMonaco(): typeof import("monaco-editor") {
  // @ts-ignore — monaco é exposto globalmente pelo Monaco Editor
  const monaco = (typeof window !== "undefined" && (window as any).monaco)
    || (globalThis as any).monaco;

  if (!monaco) {
    throw new Error(
      "Monaco Editor não encontrado. " +
      "Certifique-se de que o bundle foi carregado antes de registrar a linguagem."
    );
  }

  return monaco;
}

/**
 * Configuração padrão do editor para a linguagem SIMPLES.
 */
export const SIMPLES_EDITOR_OPTIONS: editor.IStandaloneEditorConstructionOptions = {
  language: LANGUAGE_ID,
  theme: "simples-dark",
  fontSize: 14,
  fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  minimap: { enabled: false },
  lineNumbers: "on",
  renderWhitespace: "selection",
  bracketPairColorization: { enabled: true },
  autoClosingBrackets: "always",
  autoClosingQuotes: "always",
  matchBrackets: "always",
  tabSize: 2,
  insertSpaces: true,
  scrollBeyondLastLine: false,
  wordWrap: "off",
  smoothScrolling: true,
  cursorBlinking: "smooth",
  cursorStyle: "line",
  renderLineHighlight: "line",
  padding: { top: 12, bottom: 12 },
};
