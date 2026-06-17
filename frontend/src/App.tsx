import SimplesEditor from "./components/SimplesEditor";
import Toolbar from "./components/Toolbar";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>SIMPLES Editor</h1>
      </header>
      <Toolbar />
      <main className="app-main">
        <SimplesEditor />
      </main>
    </div>
  );
}

export default App;
