import React from 'react';

function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header style={{
        background: '#252526', padding: '12px 24px',
        borderBottom: '1px solid #3c3c3c', display: 'flex',
        justifyContent: 'space-between', alignItems: 'center'
      }}>
        <h1 style={{ fontSize: 16, color: '#858585', textTransform: 'uppercase', letterSpacing: 1 }}>
          Simples Editor
        </h1>
        <HealthBadge />
      </header>
      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <h2 style={{ fontSize: 24, color: '#569cd6' }}>Bem-vindo ao Simples Editor</h2>
        <p style={{ color: '#858585', fontSize: 14 }}>
          IDE Web para a linguagem SIMPLES
        </p>
        <HealthCheck />
      </main>
    </div>
  );
}

function HealthBadge() {
  const [ok, setOk] = React.useState(null);
  React.useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(d => setOk(d.status === 'ok'))
      .catch(() => setOk(false));
  }, []);
  if (ok === null) return <span style={{ color: '#888' }}>● verificando...</span>;
  return <span style={{ color: ok ? '#4ec9b0' : '#f44747' }}>● {ok ? 'online' : 'offline'}</span>;
}

function HealthCheck() {
  const [ok, setOk] = React.useState(null);
  React.useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(d => setOk(d.status === 'ok'))
      .catch(() => setOk(false));
  }, []);
  return (
    <div style={{ padding: 12, borderRadius: 6, background: ok === null ? '#2d2d2d' : ok ? '#1a3a2a' : '#3a1a1a', fontSize: 13 }}>
      {ok === null ? '⏳ Verificando conexão com o backend...' :
       ok ? '✅ Backend online — API health check passou' :
       '❌ Backend offline — API health check falhou'}
    </div>
  );
}

export default App;
