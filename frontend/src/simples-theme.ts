import type { editor } from 'monaco-editor'

export const simplesDarkTheme: editor.IStandaloneThemeData = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    // Keywords in cyan (#00d4ff)
    { token: 'keyword', foreground: '00d4ff', fontStyle: 'bold' },
    // Type keywords in a lighter cyan
    { token: 'type', foreground: '4ec9b0' },
    // Numbers in orange (#ff9500)
    { token: 'number', foreground: 'ff9500' },
    { token: 'number.float', foreground: 'ff9500' },
    // Strings in green-orange tone
    { token: 'string', foreground: 'ce9178' },
    // Comments in green
    { token: 'comment', foreground: '6a9955', fontStyle: 'italic' },
    // Operators in pale yellow
    { token: 'operator', foreground: 'd4d4d4' },
    // Delimiters
    { token: 'delimiter', foreground: 'd4d4d4' },
    // Identifiers default
    { token: 'identifier', foreground: 'd4d4d4' },
  ],
  colors: {
    'editor.background': '#1e1e1e',
    'editor.foreground': '#d4d4d4',
    'editor.lineHighlightBackground': '#2a2d2e',
    'editor.selectionBackground': '#264f78',
    'editor.inactiveSelectionBackground': '#3a3d41',
    'editorCursor.foreground': '#aeafad',
    'editorLineNumber.foreground': '#858585',
    'editorLineNumber.activeForeground': '#c6c6c6',
  },
}
