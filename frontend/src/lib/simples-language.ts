import type { editor } from "monaco-editor";
import { simplesLanguage } from "./simples-monarch";
export const LANGUAGE_ID = "simples";
let registered = false;
export function registerSimplesLanguage(): void { if (registered) return; registerSimplesLanguageWith(getMonaco()); registered = true; }
export function registerSimplesLanguageWith(monaco: typeof import("monaco-editor")): void {
  monaco.languages.register({ id: LANGUAGE_ID });
  monaco.languages.setMonarchTokensProvider(LANGUAGE_ID, simplesLanguage);
  monaco.editor.defineTheme("simples-dark", {
    base: "vs-dark", inherit: true,
    rules: [
      { token: "keyword", foreground: "#22d3ee", fontStyle: "bold" }, { token: "operator", foreground: "#c084fc" },
      { token: "number", foreground: "#fb923c" }, { token: "number.float", foreground: "#fb923c" },
      { token: "string", foreground: "#4ade80" }, { token: "comment", foreground: "#6b7280", fontStyle: "italic" },
      { token: "identifier", foreground: "#e5e7eb" }, { token: "delimiter", foreground: "#9ca3af" },
      { token: "type", foreground: "#67e8f9" }, { token: "function", foreground: "#fde047" },
    ],
    colors: {
      "editor.background": "#0a0a0a", "editor.foreground": "#e5e7eb", "editor.lineHighlightBackground": "#1f293722",
      "editor.selectionBackground": "#22d3ee33", "editorCursor.foreground": "#22d3ee", "editorLineNumber.foreground": "#4b5563",
      "editorLineNumber.activeForeground": "#9ca3af", "editorGutter.background": "#0a0a0a",
      "editor.selectionHighlightBackground": "#22d3ee22", "editorBracketMatch.background": "#22d3ee22", "editorBracketMatch.border": "#22d3ee44",
    },
  });
}
function getMonaco(): typeof import("monaco-editor") {
  const m = (typeof window !== "undefined" && (window as any).monaco) || (globalThis as any).monaco;
  if (!m) throw new Error("Monaco Editor não encontrado."); return m;
}
export const SIMPLES_EDITOR_OPTIONS: editor.IStandaloneEditorConstructionOptions = {
  language: LANGUAGE_ID, theme: "simples-dark", fontSize: 14,
  fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  minimap: { enabled: false }, lineNumbers: "on", renderWhitespace: "selection",
  bracketPairColorization: { enabled: true }, autoClosingBrackets: "always", autoClosingQuotes: "always",
  matchBrackets: "always", tabSize: 2, insertSpaces: true, scrollBeyondLastLine: false,
  wordWrap: "off", smoothScrolling: true, cursorBlinking: "smooth", cursorStyle: "line",
  renderLineHighlight: "line", padding: { top: 12, bottom: 12 },
};
