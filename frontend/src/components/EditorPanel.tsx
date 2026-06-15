import Editor, { OnMount } from '@monaco-editor/react'
import { useRef } from 'react'

const defaultCode = `programa Exemplo
inicio
  escreva "Ola, mundo!"
fim`

export default function EditorPanel() {
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null)

  const handleMount: OnMount = (editor) => {
    editorRef.current = editor
    editor.focus()
  }

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      <div className="h-9 flex items-center px-3 text-xs text-[#969696] border-b border-[#3c3c3c]">
        <span>main.simples</span>
      </div>
      <div className="flex-1">
        <Editor
          height="100%"
          defaultLanguage="simples"
          defaultValue={defaultCode}
          theme="simples-dark"
          onMount={handleMount}
          options={{
            fontSize: 14,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 8 },
          }}
        />
      </div>
    </div>
  )
}
