import { createRoute, redirect } from "@tanstack/react-router";
import { supabase } from "src/lib/supabase";
import { rootRoute } from "./__root";
import { LoginPage } from "src/components/LoginPage";

export const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginRoute,
  beforeLoad: async () => {
    const { data } = await supabase.auth.getSession();
    // Se já estiver logado, redireciona para a IDE
    if (data.session) {
      throw redirect({ to: "/" });
    }
  },
});

function LoginRoute() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-cyan-400">Simples Editor</h1>
          <p className="text-gray-400 mt-2">
            IDE web para a linguagem SIMPLES
          </p>
        </div>
        <LoginPage />
      </div>
    </div>
  );
}
