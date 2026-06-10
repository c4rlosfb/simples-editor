import React, { useCallback } from 'react';
import Editor from '@monaco-editor/react';

interface CompileError {
  line: number;
  column: number;
  message: string;
  phase: string;
}

interface Props {
  code: string;
  onChange: (code: string) => void;
  errors: CompileError[];
}

const SIMPLES_LANGUAGE_ID = 'simples';

const SIMPLES_MONARCH_DEFINITION = {
  defaultToken: '',
  tokenPostfix: '.simples',

  keywords: [
    'programa', 'declare', 'inicio', 'fimprog', 'declare_partes', 'inicio_partes', 'registros',
    'inteiro', 'real', 'caracter', 'leia', 'escreva', 'se', 'entao', 'senao', 'fimse',
    'enquanto', 'faca', 'fimenquanto', 'repita', 'ate', 'para', 'e', 'ou', 'nao',
    'verdadeiro', 'falso',
  ],

  typeKeywords: ['inteiro', 'real', 'caracter'],

  operators: [':=', '=', '<>', '<', '>', '<=', '>=', '+', '-', '*', '/', ':', ',', ';'],

  tokenizer: {
    root: [
      [/[a-zA-Z_]\w*/, { cases: { '@typeKeywords': 'type', '@keywords': 'keyword', '@default': 'identifier' } }],
      [/'.*?'/, 'string'],
      [/".*?"/, 'string'],
      [/[0-9]+\.[0-9]*/, 'number.float'],
      [/[0-9]+/, 'number'],
      [/[{}()]/, '@brackets'],
      [/[:=<>+\-*\/,;]/, 'delimiter'],
      [/\/\/.*$/, 'comment'],
      [/[ 	
]+/, 'white'],
    ],
  },
} as const;

const SIMPLES_THEME = {
  base: 'vs-dark' as const,
  inherit: true,
  rules: [
    { token: 'keyword', foreground: '569cd6', fontStyle: 'bold' },
    { token: 'type', foreground: '4ec9b0' },
    { token: 'string', foreground: 'ce9178' },
    { token: 'number', foreground: 'b5cea8' },
    { token: 'number.float', foreground: 'b5cea8' },
    { token: 'comment', foreground: '6a9955' },
    { token: 'delimiter', foreground: 'd4d4d4' },
    { token: 'identifier', foreground: 'd4d4d4' },
  ],
  colors: {
    'editor.background': '#1e1e1e',
    'editor.foreground': '#d4d4d4',
    'editor.lineHighlightBackground': '#2a2d2e',
    'editor.selectionBackground': '#264f78',
  },
};

function SimplesEditor({ code, onChange, errors }: Props) {
  const handleBeforeMount = useCallback((monaco: any) => {
    // Register SIMPLES language
    monaco.languages.register({ id: SIMPLES_LANGUAGE_ID });
    monaco.languages.setMonarchTokensProvider(SIMPLES_LANGUAGE_ID, SIMPLES_MONARCH_DEFINITION);
    monaco.editor.defineTheme('simples-dark', SIMPLES_THEME);
  }, []);

  const handleMount = useCallback((editor: any, monaco: any) => {
    // Apply error markers
    if (errors.length > 0) {
      const markers = errors.map(err => ({
        startLineNumber: err.line,
        endLineNumber: err.line,
        startColumn: err.column,
        endColumn: err.column + 1,
        message: `[${err.phase}] ${err.message}`,
        severity: monaco.MarkerSeverity.Error,
      }));
      monaco.editor.setModelMarkers(editor.getModel(), 'simples', markers);
    }
  }, [errors]);

  return (
    <Editor
      language={SIMPLES_LANGUAGE_ID}
      value={code}
      onChange={(val) => onChange(val || '')}
      beforeMount={handleBeforeMount}
      onMount={handleMount}
      theme="simples-dark"
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        automaticLayout: true,
        padding: { top: 8 },
        scrollBeyondLastLine: false,
      }}
    />
  );
}

export default SimplesEditor;
