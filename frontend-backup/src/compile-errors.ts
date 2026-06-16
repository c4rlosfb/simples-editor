import type { editor } from 'monaco-editor'

/**
 * Estrutura de um erro de compilação do SIMPLES.
 * {line, column, message, phase}  — 1-indexed line/column.
 */
export interface CompileError {
  /** Linha onde o erro ocorreu (1-indexed) */
  line: number
  /** Coluna onde o erro ocorreu (1-indexed, opcional) */
  column?: number
  /** Mensagem descritiva do erro */
  message: string
  /** Fase do compilador: 'lexico' | 'sintatico' | 'semantico' */
  phase: 'lexico' | 'sintatico' | 'semantico'
}

/**
 * Converte erros de compilação do SIMPLES em markers do Monaco Editor.
 * Marcadores vermelhos (severity 8 = Error) com underline squiggly
 * na linha/coluna do erro e tooltip com a mensagem.
 */
export function compileErrorsToMarkers(
  errors: CompileError[]
): editor.IMarkerData[] {
  return errors.map((err) => {
    const startColumn = err.column ?? 1
    // Marcamos a posição até a coluna seguinte (ou um char de largura)
    const endColumn = startColumn + 1

    return {
      severity: 8, // monaco.MarkerSeverity.Error
      message: `[${err.phase.toUpperCase()}] ${err.message}`,
      startLineNumber: err.line,
      startColumn,
      endLineNumber: err.line,
      endColumn,
    }
  })
}
