import { createRoute, redirect, useNavigate } from "@tanstack/react-router";
import { supabase } from "@/lib/supabase";
import { rootRoute } from "./__root";
import SimplesEditor from "@/components/SimplesEditor";
import TerminalPanel from "@/components/TerminalPanel";

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: IndexRoute,
  beforeLoad: async () => {
    // Modo demonstração: pula autenticação Supabase
    if (import.meta.env.VITE_DEMO_MODE === "true") {
      return;
    }
    try {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        throw redirect({ to: "/login" });
      }
    } catch (error) {
      if (error instanceof Response || (error as any)?.redirect) throw error;
      throw redirect({ to: "/login" });
    }
  },
});

function IndexRoute() {
  const navigate = useNavigate();
  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate({ to: "/login" });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-cyan-400">Simples Editor</h1>
          <span className="text-xs text-gray-600">|</span>
          <span className="text-xs text-gray-500">SIMPLES → NASM → ELF i386</span>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-sm rounded transition-colors">
            ▶ Compilar
          </button>
          <button className="px-3 py-1 bg-red-800 hover:bg-red-700 text-sm rounded transition-colors">
            ■ Parar
          </button>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Sair
          </button>
        </div>
      </header>

      {/* Main content: Editor + NASM (top), Terminal (bottom) */}
      <main className="flex-1 flex flex-col min-h-0">
        {/* Top row: Editor + NASM */}
        <div className="flex-1 flex min-h-0">
          {/* Editor */}
          <div className="flex-1 border-r border-gray-800 flex flex-col">
            <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
              Editor SIMPLES
            </div>
            <div className="flex-1">
              <SimplesEditor />
            </div>
          </div>

          {/* NASM Panel */}
          <div className="w-1/2 flex flex-col">
            <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
              NASM x86 (i386)
            </div>
            <div className="flex-1 bg-gray-950 p-4 font-mono text-sm text-gray-400 overflow-auto">
              <span className="text-gray-600">
                ; Compile seu código SIMPLES para ver o assembly gerado aqui
              </span>
            </div>
          </div>
        </div>

        {/* Bottom: Terminal */}
        <div className="h-48 border-t border-gray-800 flex flex-col shrink-0">
          <div className="px-3 py-1 bg-gray-900 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
            Terminal
          </div>
          <div className="flex-1">
            <TerminalPanel />
          </div>
        </div>
      </main>
    </div>
  );
}
