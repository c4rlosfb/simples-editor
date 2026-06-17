import { useState, useCallback, useRef } from "react";
import SimplesEditor from "./components/SimplesEditor";
import NasmPanel from "./components/NasmPanel";
import SplitPanel from "./components/SplitPanel";
import Toolbar from "./components/Toolbar";
import { useWebSocket } from "./hooks/useWebSocket";

function App() {
  const { asmCode, isRunning, sendCode, sendStop } = useWebSocket();
  const [editorCode, setEditorCode] = useState("");
  const readyToSend = useRef(true);

  const handleRun = useCallback(() => {
    readyToSend.current = false;
    sendCode(editorCode);
    // Re-enable after a small delay to prevent double-send
    setTimeout(() => { readyToSend.current = true; }, 500);
  }, [editorCode, sendCode]);

  const canRun = !isRunning && readyToSend.current;

  return (
    <div className="app">
      <header className="app-header">
        <h1>SIMPLES Editor</h1>
      </header>
      <Toolbar onRun={handleRun} onStop={sendStop} isRunning={isRunning} canRun={canRun} />
      <main className="app-main">
        <SplitPanel
          left={<SimplesEditor code={editorCode} onChange={setEditorCode} />}
          right={<NasmPanel code={asmCode} />}
          defaultRatio={0.65}
        />
      </main>
    </div>
  );
}

export default App;
