import React, { useEffect, useRef } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

interface Props {
  lines: string[];
}

function TerminalPanel({ lines }: Props) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalInstance = useRef<Terminal | null>(null);
  const fitAddon = useRef<FitAddon | null>(null);
  const linesRendered = useRef(0);

  // Initialize terminal once on mount
  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new Terminal({
      theme: {
        background: '#1e1e2e',
        foreground: '#d4d4d4',
        cursor: '#569cd6',
      },
      fontSize: 14,
      fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
      cursorBlink: true,
    });

    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(terminalRef.current);
    fit.fit();

    terminalInstance.current = term;
    fitAddon.current = fit;

    term.writeln('Bem-vindo ao Simples Editor!');
    term.writeln('Pressione Run para compilar e executar.');
    term.write('$ ');

    return () => {
      term.dispose();
    };
  }, []);

  // Append new lines without clearing the terminal
  useEffect(() => {
    const term = terminalInstance.current;
    if (!term) return;

    // Only write lines that haven't been rendered yet
    const newLines = lines.slice(linesRendered.current);
    if (newLines.length === 0) return;

    for (const line of newLines) {
      term.writeln(line);
    }
    linesRendered.current = lines.length;
  }, [lines]);

  // Fit terminal on resize
  useEffect(() => {
    const handleResize = () => fitAddon.current?.fit();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return <div ref={terminalRef} className="h-full w-full" />;
}

export default TerminalPanel;
