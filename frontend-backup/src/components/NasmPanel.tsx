import Editor from '@monaco-editor/react'

interface NasmPanelProps {
  /** Código NASM x86-64 a ser exibido */
  code?: string
}

const PLACEHOLDER = `; Nenhum assembly gerado ainda.
; Compile um programa SIMPLES para ver o NASM aqui.
;
; Exemplo do que você verá:
;
; section .data
;     _msg db 'Hello World!', 10
;
; section .text
;     global _start
; _start:
;     mov eax, 4
;     mov ebx, 1
;     mov ecx, _msg
;     mov edx, 12
;     int 0x80
;     mov eax, 1
;     xor ebx, ebx
;     int 0x80`

const NASM_OPTIONS = {
  readOnly: true,
  minimap: { enabled: false },
  fontSize: 14,
  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
  lineNumbers: 'on' as const,
  automaticLayout: true,
  padding: { top: 8 },
  scrollBeyondLastLine: false,
  folding: true,
  renderWhitespace: 'boundary' as const,
  wordWrap: 'off' as const,
  contextmenu: false,
}

export default function NasmPanel({ code }: NasmPanelProps) {
  return (
    <Editor
      height="100%"
      language="asm"
      value={code || PLACEHOLDER}
      theme="vs-dark"
      options={NASM_OPTIONS}
    />
  )
}
