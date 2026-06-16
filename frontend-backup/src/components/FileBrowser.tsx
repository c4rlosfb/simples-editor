export default function FileBrowser() {
  return (
    <div className="h-full bg-[#252526] flex flex-col">
      <div className="h-9 flex items-center px-3 text-xs font-medium uppercase tracking-wider text-[#969696] border-b border-[#3c3c3c]">
        Explorer
      </div>
      <div className="flex-1 overflow-auto p-2 text-sm text-[#969696]">
        <p className="text-xs italic">Nenhum arquivo aberto</p>
      </div>
    </div>
  )
}
