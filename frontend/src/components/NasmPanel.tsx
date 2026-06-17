function NasmPanel() {
  return (
    <div className="nasm-panel">
      <div className="nasm-panel__header">
        <span className="nasm-panel__title">NASM x32</span>
        <span className="nasm-panel__badge">read-only</span>
      </div>
      <div className="nasm-panel__body">
        <p className="nasm-panel__placeholder">
          Compile seu código SIMPLES para ver o assembly NASM aqui.
        </p>
      </div>
    </div>
  );
}

export default NasmPanel;
