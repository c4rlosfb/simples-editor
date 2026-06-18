import {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useRef,
} from "react";
import Editor, { BeforeMount, OnMount } from "@monaco-editor/react";
import {
  LANGUAGE_ID,
  registerSimplesLanguageWith,
  SIMPLES_EDITOR_OPTIONS,
} from "../lib/simples-language";

const DEFAULT_CODE = `programa exemplo
inicio
  escreva "ola mundo"
fim`;

/** Interface pública exposta via ref para o componente pai. */
export interface SimplesEditorHandle {
  /** Retorna o código atual do editor. */
  getValue: () => string;
  /** Substitui o conteúdo do editor. */
  setValue: (value: string) => void;
  /** Retorna a instância do Monaco Editor (para markers, etc.). */
  getEditor: () => import("monaco-editor").editor.IStandaloneCodeEditor | null;
}

interface SimplesEditorProps {
  /** Chamado sempre que o código muda. */
  onChange?: (code: string) => void;
  /** Código inicial (opcional, usa DEFAULT_CODE se não informado). */
  defaultValue?: string;
  /** Quando true, o editor fica em modo somente-leitura (ex: durante compilação/execução). */
  readOnly?: boolean;
}

/**
 * Editor Monaco configurado para a linguagem SIMPLES.
 *
 * Expõe um ref com getValue/setValue/getEditor para que o componente pai
 * possa ler o código e aplicar markers de erro.
 */
const SimplesEditor = forwardRef<SimplesEditorHandle, SimplesEditorProps>(
  function SimplesEditor({ onChange, defaultValue, readOnly }, ref) {
    const editorRef =
      useRef<import("monaco-editor").editor.IStandaloneCodeEditor | null>(null);
    // Guarda a instância do monaco para uso em markers
    const monacoRef = useRef<typeof import("monaco-editor") | null>(null);

    const handleBeforeMount: BeforeMount = useCallback((monaco) => {
      monacoRef.current = monaco;
      registerSimplesLanguageWith(monaco);
    }, []);

    const handleOnMount: OnMount = useCallback(
      (editor) => {
        editorRef.current = editor;
        editor.focus();
        // Notifica o pai do código inicial
        if (onChange) {
          onChange(editor.getValue());
        }
      },
      [onChange],
    );

    const handleChange = useCallback(
      (value: string | undefined) => {
        if (onChange && value !== undefined) {
          onChange(value);
        }
      },
      [onChange],
    );

    useImperativeHandle(ref, () => ({
      getValue: () => editorRef.current?.getValue() || "",
      setValue: (value: string) => {
        editorRef.current?.setValue(value);
      },
      getEditor: () => editorRef.current,
    }));

    return (
      <div className="editor-container">
        <Editor
          defaultLanguage={LANGUAGE_ID}
          defaultValue={defaultValue || DEFAULT_CODE}
          theme="simples-dark"
          beforeMount={handleBeforeMount}
          onMount={handleOnMount}
          onChange={handleChange}
          options={{
            ...SIMPLES_EDITOR_OPTIONS,
            ...(readOnly !== undefined ? { readOnly } : {}),
          }}
        />
      </div>
    );
  },
);

export default SimplesEditor;
