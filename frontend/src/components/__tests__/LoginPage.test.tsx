import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import LoginPage from "../LoginPage";

// Mock do supabase
vi.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
    },
  },
}));

describe("LoginPage", () => {
  it("renders without crashing", () => {
    const { container } = render(<LoginPage />);
    expect(container).toBeTruthy();
  });

  it("displays login heading", () => {
    render(<LoginPage />);
    expect(screen.getByText(/entrar|login|simples|editor/i)).toBeTruthy();
  });
});
