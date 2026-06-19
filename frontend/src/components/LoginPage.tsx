import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { supabase } from "../lib/supabase";

const siteUrl = import.meta.env.VITE_SITE_URL || (typeof window !== "undefined" ? window.location.origin : "");

export function LoginPage() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
      <Auth
        supabaseClient={supabase}
        appearance={{
          theme: ThemeSupa,
          variables: {
            default: {
              colors: {
                brand: "#22d3ee",
                brandAccent: "#06b6d4",
                brandButtonText: "#0a0a0a",
                defaultButtonBackground: "#1f2937",
                defaultButtonBackgroundHover: "#374151",
                inputBackground: "#111827",
                inputBorder: "#374151",
                inputText: "#e5e7eb",
                inputLabelText: "#9ca3af",
                messageText: "#f87171",
              },
            },
          },
          style: {
            button: {
              borderRadius: "0.5rem",
              fontSize: "0.875rem",
              padding: "0.625rem 1rem",
            },
            input: {
              borderRadius: "0.5rem",
              fontSize: "0.875rem",
              padding: "0.625rem 0.75rem",
            },
            label: {
              fontSize: "0.875rem",
              color: "#9ca3af",
            },
            anchor: {
              color: "#22d3ee",
            },
            message: {
              fontSize: "0.8rem",
            },
          },
        }}
        providers={[]}
        redirectTo={`${siteUrl}/`}
        onlyThirdPartyProviders={false}
        magicLink={false}
        showLinks={true}
        view="sign_in"
      />
    </div>
  );
}
