import { createRoute, redirect } from "@tanstack/react-router";
import { supabase } from "src/lib/supabase";
import { rootRoute } from "./__root";

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: IndexRoute,
  beforeLoad: async () => {
    const { data } = await supabase.auth.getSession();
    // Se não estiver logado, redireciona para o login
    if (!data.session) {
      throw redirect({ to: "/login" });
    }
  },
});

function IndexRoute() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-cyan-400">Simples Editor</h1>
        </div>
        <button
          onClick={async () => {
            await supabase.auth.signOut();
            window.location.href = "/login";
          }}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Sair
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <p className="text-xl mb-2">Bem-vindo ao Simples Editor</p>
          <p className="text-sm">
            Monaco Editor + painel NASM + terminal interativo
          </p>
          <p className="text-xs mt-4 text-gray-600">
            (Interface da IDE em implementação — Sprint 2)
          </p>
        </div>
      </main>
    </div>
  );
}
