import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { setBackend } from "./api/hooks";
import { initTelegram, shouldUseMock } from "./lib/telegram";
import "./styles.css";

const client = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } },
});

async function main(): Promise<void> {
  initTelegram();
  const root = document.getElementById("root");
  if (!root) return;

  if (shouldUseMock()) {
    const { mockBackend } = await import("./api/mock");
    setBackend(mockBackend);
  }

  createRoot(root).render(
    <StrictMode>
      <QueryClientProvider client={client}>
        <App />
      </QueryClientProvider>
    </StrictMode>,
  );
}

void main();
