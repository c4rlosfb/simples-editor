// Route tree generated manually for TanStack React Router.
// Based on the file-based routes in src/routes/*

import { rootRoute } from "./routes/__root";
import { loginRoute } from "./routes/login";
import { indexRoute } from "./routes/index";

export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
]);
