import SimplesEditor from "./components/SimplesEditor";
import SplitPanel from "./components/SplitPanel";
import NasmPanel from "./components/NasmPanel";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>SIMPLES Editor</h1>
      </header>
      <main className="app-main">
        <SplitPanel
          left={<SimplesEditor />}
          right={<NasmPanel />}
          defaultRatio={0.65}
        />
      </main>
    </div>
  );
}

export default App;
