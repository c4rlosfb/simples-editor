interface ToolbarProps {
  onRun: () => void;
  onStop: () => void;
  isRunning: boolean;
  canRun: boolean;
}

function Toolbar({ onRun, onStop, isRunning, canRun }: ToolbarProps) {
  return (
    <div className="toolbar">
      <div className="toolbar__left">
        <button
          className={`toolbar__btn toolbar__btn--run ${isRunning ? "toolbar__btn--active" : ""}`}
          onClick={onRun}
          disabled={!canRun}
        >
          <span className="toolbar__run-icon">{isRunning ? "⏳" : "▶"}</span>
          {isRunning ? "compilando…" : "Run"}
        </button>
        <button
          className="toolbar__btn toolbar__btn--stop"
          onClick={onStop}
          disabled={!isRunning}
        >
          ■ Stop
        </button>
      </div>
      <div className="toolbar__right">
        <span className="toolbar__state-label">
          {isRunning ? "Compilando…" : "Pronto"}
        </span>
      </div>
    </div>
  );
}

export default Toolbar;
