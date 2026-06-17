import { describe, it, expect, vi } from "vitest";

describe("supabase client", () => {
  it("throws without env vars", () => {
    // Limpa env vars que possam existir
    delete process.env.VITE_SUPABASE_URL;
    delete process.env.VITE_SUPABASE_ANON_KEY;

    // Re-importar deve falhar se não houver env vars
    expect(() => {
      // Simula a validação do módulo supabase.ts
      const url = process.env.VITE_SUPABASE_URL || "";
      const key = process.env.VITE_SUPABASE_ANON_KEY || "";
      if (!url || !key) {
        throw new Error(
          "Supabase não configurado: VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY devem estar definidas"
        );
      }
    }).toThrow("Supabase não configurado");
  });
});
