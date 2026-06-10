import React from 'react';
import Editor from '@monaco-editor/react';

interface Props {
  code: string;
}

function NasmPanel({ code }: Props) {
  return (
    <Editor
      language="asm"
      value={code || '; Nenhum assembly gerado ainda.
; Compile um programa SIMPLES para ver o NASM aqui.'}
      theme="vs-dark"
      options={{
        readOnly: true,
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

export default NasmPanel;
