export default function OutputPanel() {
  return (
    <div className="h-full bg-[#1e1e1e] flex flex-col">
      <div className="h-9 flex items-center px-3 text-xs font-medium uppercase tracking-wider text-[#969696] border-b border-[#3c3c3c]">
        Saída
      </div>
      <div className="flex-1 overflow-auto p-3 text-sm font-mono text-[#d4d4d4]">
        <p className="text-[#6a9955]">&gt; Pronto para executar</p>
      </div>
    </div>
  )
}
