import NasmPanel from './NasmPanel'

interface OutputPanelProps {
  /** Código NASM gerado pelo compilador */
  nasmCode?: string
}

export default function OutputPanel({ nasmCode }: OutputPanelProps) {
  return (
    <div className="h-full bg-[#1e1e1e] flex flex-col">
      <div className="h-9 flex items-center px-3 text-xs font-medium uppercase tracking-wider text-[#969696] border-b border-[#3c3c3c]">
        NASM x86
      </div>
      <div className="flex-1">
        <NasmPanel code={nasmCode} />
      </div>
    </div>
  )
}
