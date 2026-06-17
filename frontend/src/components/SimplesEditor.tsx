import { useCallback } from "react";
import Editor, { BeforeMount, OnMount } from "@monaco-editor/react";
import { LANGUAGE_ID, registerSimplesLanguageWith, SIMPLES_EDITOR_OPTIONS } from "../lib/simples-language";

const DEFAULT_CODE = `programa exemplo
inicio
  escreva "ola mundo"
fim`;

function SimplesEditor() {
  const handleBeforeMount: BeforeMount = useCallback((monaco) => {
    registerSimplesLanguageWith(monaco);
  }, []);

  const handleOnMount: OnMount = useCallback((editor) => {
    editor.focus();
  }, []);

  return (
    <div className="editor-container">
      <Editor
        defaultLanguage={LANGUAGE_ID}
        defaultValue={DEFAULT_CODE}
        theme="simples-dark"
        beforeMount={handleBeforeMount}
        onMount={handleOnMount}
        options={SIMPLES_EDITOR_OPTIONS}
      />
    </div>
  );
}

export default SimplesEditor;
