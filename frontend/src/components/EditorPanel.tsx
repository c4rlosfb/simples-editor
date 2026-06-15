import { useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import type { CompileError } from '../compile-errors'
import { compileErrorsToMarkers } from '../compile-errors'

interface EditorPanelProps {
  /** Erros de compilação a serem exibidos como markers no editor */
  errors?: CompileError[]
}

const defaultCode = `programa Exemplo
inicio
  escreva "Ola, mundo!"
fim`

export default function EditorPanel({ errors = [] }: EditorPanelProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null)

  const handleEditorDidMount = (
    editor: editor.IStandaloneCodeEditor,
    monaco: typeof import('monaco-editor')
  ) => {
    editorRef.current = editor
    monacoRef.current = monaco
  }

  // Atualiza markers sempre que a lista de erros mudar
  useEffect(() => {
    const ed = editorRef.current
    const monaco = monacoRef.current
    if (!ed || !monaco) return

    const model = ed.getModel()
    if (!model) return

    const markers = compileErrorsToMarkers(errors)
    monaco.editor.setModelMarkers(model, 'compile-errors', markers)
  }, [errors])

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
          onMount={handleEditorDidMount}
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
