import { useCallback } from "react";
import Editor, { BeforeMount } from "@monaco-editor/react";

interface NasmPanelProps {
  code: string;
}

const PLACEHOLDER = "; Compile seu código SIMPLES para ver o assembly NASM aqui.";

function NasmPanel({ code }: NasmPanelProps) {
  const handleBeforeMount: BeforeMount = useCallback((monaco) => {
    // Register NASM language if not already registered
    monaco.languages.register({ id: "asm" });
  }, []);

  return (
    <div className="nasm-panel">
      <div className="nasm-panel__header">
        <span className="nasm-panel__title">NASM x32</span>
        <span className="nasm-panel__badge">read-only</span>
      </div>
      <div className="nasm-panel__editor">
        <Editor
          defaultLanguage="asm"
          value={code || PLACEHOLDER}
          theme="vs-dark"
          beforeMount={handleBeforeMount}
          options={{
            readOnly: true,
            fontSize: 13,
            minimap: { enabled: false },
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            wordWrap: "off",
            renderWhitespace: "selection",
            tabSize: 4,
            insertSpaces: true,
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>
    </div>
  );
}

export default NasmPanel;
