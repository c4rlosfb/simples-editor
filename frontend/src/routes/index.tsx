import { createRoute, redirect } from "@tanstack/react-router";
import { supabase } from "@/lib/supabase";
import { rootRoute } from "./__root";
import App from "@/App";

// ── Route ───────────────────────────────────────────────────────────────────

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: App,
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
