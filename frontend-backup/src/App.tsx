import { useState } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import EditorPanel from './components/EditorPanel'
import FileBrowser from './components/FileBrowser'
import OutputPanel from './components/OutputPanel'
import Toolbar from './components/Toolbar'
import type { CompileError } from './compile-errors'
import './setup-monaco'

const MOCK_NASM = `; NASM x86 assembly — output do compilador SIMPLES
; Arquivo: main.asm
;
; Compile com: nasm -f elf64 main.asm -o main.o
; Link com:    ld main.o -o main

section .data
    _msg db 'Hello World!', 10
    _msg_len equ $ - _msg

section .bss
    _input resb 256

section .text
    global _start

_start:
    ; write(1, _msg, _msg_len)
    mov rax, 1
    mov rdi, 1
    lea rsi, [_msg]
    mov rdx, _msg_len
    syscall

    ; exit(0)
    mov rax, 60
    xor rdi, rdi
    syscall`

const MOCK_ERRORS: CompileError[] = [
  {
    line: 3,
    column: 5,
    message: 'Token inesperado: "escreva". Esperado "fim".',
    phase: 'sintatico',
  },
  {
    line: 1,
    column: 10,
    message: 'Identificador "Exemplo" nao declarado.',
    phase: 'semantico',
  },
]

export default function App() {
  const [nasmCode, setNasmCode] = useState(MOCK_NASM)
  const [compileErrors, setCompileErrors] = useState<CompileError[]>(MOCK_ERRORS)

  return (
    <div className="h-screen flex flex-col bg-[#1e1e1e]">
      <Toolbar />
      <div className="flex-1">
        <PanelGroup direction="horizontal">
          <Panel defaultSize={20} minSize={10} maxSize={40}>
            <FileBrowser />
          </Panel>
          <PanelResizeHandle className="w-1 bg-[#333] hover:bg-[#007acc] transition-colors cursor-col-resize" />
          <Panel defaultSize={55} minSize={30}>
            <EditorPanel errors={compileErrors} />
          </Panel>
          <PanelResizeHandle className="w-1 bg-[#333] hover:bg-[#007acc] transition-colors cursor-col-resize" />
          <Panel defaultSize={25} minSize={10} maxSize={40}>
            <OutputPanel nasmCode={nasmCode} />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  )
}
