import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: "#16213e", color: "#eee", border: "1px solid #f5a623" },
          success: { iconTheme: { primary: "#6fcf6f", secondary: "#16213e" } },
          error: { iconTheme: { primary: "#e24b4a", secondary: "#fff" } },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>
);
