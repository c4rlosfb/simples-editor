import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Supabase não configurado: " +
    "VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY devem estar definidas no .env. " +
    "Consulte frontend/.env.example."
  );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
