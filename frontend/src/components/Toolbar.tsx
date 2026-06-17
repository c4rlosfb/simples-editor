import { useState } from "react";

type EditorState = "idle" | "compiling" | "compile_error" | "executing" | "finished";

function Toolbar() {
  const [editorState, setEditorState] = useState<EditorState>("idle");

  const isRunning = editorState === "compiling" || editorState === "executing";
  const isIdle = editorState === "idle" || editorState === "finished" || editorState === "compile_error";

  const handleRun = () => {
    if (!isIdle) return;

    setEditorState("compiling");

    // Simula 2 segundos de compilação, depois volta a idle
    setTimeout(() => {
      setEditorState("idle");
    }, 2000);
  };

  const runLabel = (() => {
    switch (editorState) {
      case "compiling":
        return "compilando…";
      case "executing":
        return "executando…";
      default:
        return "▶ Run";
    }
  })();

  return (
    <div className="toolbar">
      <div className="toolbar__left">
        <button
          className={`toolbar__btn toolbar__btn--run ${!isIdle ? "toolbar__btn--active" : ""}`}
          onClick={handleRun}
          disabled={!isIdle}
        >
          <span className="toolbar__run-icon">{isRunning ? "⏳" : "▶"}</span>
          {runLabel}
        </button>

        <button className="toolbar__btn toolbar__btn--stop" disabled={isIdle}>
          ■ Stop
        </button>
      </div>

      <div className="toolbar__right">
        <span className="toolbar__state-label">
          {editorState === "idle" && "Pronto"}
          {editorState === "compiling" && "Compilando…"}
          {editorState === "compile_error" && "Erro de compilação"}
          {editorState === "executing" && "Executando…"}
          {editorState === "finished" && "Finalizado"}
        </span>
      </div>
    </div>
  );
}

export default Toolbar;
