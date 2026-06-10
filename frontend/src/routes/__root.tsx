import { createRootRoute, Outlet, HeadContent, Scripts } from "@tanstack/react-router";

export const rootRoute = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <html lang="pt-BR" className="dark">
      <head>
        <HeadContent />
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Simples Editor</title>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </head>
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <Outlet />
        <Scripts />
      </body>
    </html>
  );
}
