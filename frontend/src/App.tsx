import React, { useState, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import SimplesEditor from './components/SimplesEditor';
import NasmPanel from './components/NasmPanel';
import TerminalPanel from './components/TerminalPanel';
import RunButton from './components/RunButton';

const DEFAULT_CODE = `programa exemplo
  inteiro x, y
inicio
  escreva "Digite um numero: "
  leia x
  y <- x * 2
  escreva "Dobro: ", y
fim`;

interface CompileResult {
  success: boolean;
  asm?: string;
  errors?: Array<{ line: number; column: number; message: string; phase: string }>;
  exitCode?: number;
  output?: string;
}

function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [nasmCode, setNasmCode] = useState('');
  const [errors, setErrors] = useState<Array<{ line: number; column: number; message: string; phase: string }>>([]);
  const [terminalLines, setTerminalLines] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    setErrors([]);
    setNasmCode('');
    setTerminalLines([]);
    addTerminalLine('$ Compilando...');

    try {
      const res = await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const result: CompileResult = await res.json();

      if (result.errors && result.errors.length > 0) {
        setErrors(result.errors);
        addTerminalLine(`$ Erro de compilação: ${result.errors[0].message}`);
        return;
      }

      if (result.asm) {
        setNasmCode(result.asm);
        addTerminalLine('$ Assembly gerado. Executando...');
      }

      setTerminalLines(prev => [...prev, '$ Programa finalizado com codigo 0']);
    } catch (err) {
      addTerminalLine(`$ Erro: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setIsRunning(false);
    }
  }, [code]);

  const addTerminalLine = (line: string) => {
    setTerminalLines(prev => [...prev, line]);
  };

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
      {/* Toolbar */}
      <header className="flex items-center justify-between px-4 py-2 bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
        <h1 className="text-sm font-semibold text-[var(--text-secondary)] tracking-wide uppercase">
          Simples Editor
        </h1>
        <RunButton onClick={handleRun} disabled={isRunning} />
      </header>

      {/* Main panels */}
      <PanelGroup direction="horizontal" className="flex-1">
        {/* Editor panel */}
        <Panel defaultSize={55} minSize={30}>
          <div className="h-full flex flex-col">
            <div className="px-3 py-1.5 text-xs text-[var(--text-secondary)] bg-[var(--bg-tertiary)] border-b border-[var(--border-color)]">
              Editor SIMPLES
            </div>
            <div className="flex-1">
              <SimplesEditor code={code} onChange={setCode} errors={errors} />
            </div>
          </div>
        </Panel>

        <PanelResizeHandle className="w-1 bg-[var(--border-color)] hover:bg-[var(--accent)] transition-colors cursor-col-resize" />

        {/* NASM panel */}
        <Panel defaultSize={45} minSize={20}>
          <div className="h-full flex flex-col">
            <div className="px-3 py-1.5 text-xs text-[var(--text-secondary)] bg-[var(--bg-tertiary)] border-b border-[var(--border-color)]">
              NASM x86
            </div>
            <div className="flex-1">
              <NasmPanel code={nasmCode} />
            </div>
          </div>
        </Panel>
      </PanelGroup>

      {/* Terminal panel */}
      <div className="h-48 border-t border-[var(--border-color)] flex flex-col">
        <div className="px-3 py-1.5 text-xs text-[var(--text-secondary)] bg-[var(--bg-tertiary)] border-b border-[var(--border-color)]">
          Terminal
        </div>
        <div className="flex-1">
          <TerminalPanel lines={terminalLines} />
        </div>
      </div>
    </div>
  );
}

export default App;
