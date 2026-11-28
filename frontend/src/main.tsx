import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

const SAVED_SESSION_KEYS = [
  "radonc-mdt-last-case",
  "radonc-mdt-active-batch"
] as const;

function clearSavedBrowserSession() {
  try {
    for (const key of SAVED_SESSION_KEYS) {
      window.localStorage.removeItem(key);
    }
  } catch (error) {
    console.warn("[RadOnc] Browser storage could not be cleared.", error);
  }
}

// One-time recovery URL: /?reset-local-session=1 clears only browser-restored
// case/run pointers. The backend database and completed simulation records stay intact.
const startupUrl = new URL(window.location.href);
if (startupUrl.searchParams.get("reset-local-session") === "1") {
  clearSavedBrowserSession();
  startupUrl.searchParams.delete("reset-local-session");
  window.history.replaceState(
    {},
    document.title,
    startupUrl.pathname + startupUrl.search + startupUrl.hash
  );
}

class AppErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[RadOnc] Fatal UI render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <main style={{
          minHeight: "100vh",
          padding: "48px 24px",
          background: "#101a2a",
          color: "#e9eef7",
          fontFamily: '"Segoe UI", sans-serif'
        }}>
          <section style={{
            maxWidth: 760,
            margin: "0 auto",
            padding: 28,
            border: "1px solid rgba(238,140,133,.35)",
            borderRadius: 14,
            background: "#172438"
          }}>
            <p style={{ color: "#ee9a93", fontSize: 11, letterSpacing: 2 }}>RADONC MDT · UI RECOVERY</p>
            <h1 style={{ fontSize: 26, marginBottom: 12 }}>The dashboard encountered a rendering error.</h1>
            <p style={{ color: "#a9b7c9", lineHeight: 1.6 }}>
              The local API and stored simulation records have not been deleted. The error below is
              shown so the blank page can be diagnosed instead of silently disappearing.
            </p>
            <pre style={{
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              padding: 14,
              borderRadius: 8,
              background: "#0b1625",
              color: "#f1b7b2",
              fontSize: 12
            }}>{this.state.error.message}</pre>
            <button
              type="button"
              onClick={() => {
                clearSavedBrowserSession();
                window.location.replace("/");
              }}
              style={{
                padding: "11px 16px",
                border: 0,
                borderRadius: 8,
                background: "#8edac8",
                color: "#102b2d",
                fontWeight: 700,
                cursor: "pointer"
              }}
            >
              Clear saved browser session and reopen
            </button>
            <p style={{ marginTop: 16, color: "#91a0b5", fontSize: 11 }}>
              This only clears the browser's saved case and active-run pointers. It does not delete
              simulation records from the backend database or affect Ollama/model files.
            </p>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

window.addEventListener("error", (event) => {
  console.error("[RadOnc] Browser runtime error:", event.error ?? event.message);
});
window.addEventListener("unhandledrejection", (event) => {
  console.error("[RadOnc] Unhandled async error:", event.reason);
});

const container = document.getElementById("root");
if (!container) {
  document.body.textContent = "RadOnc MDT Simulator: the root element is missing from index.html.";
} else {
  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <AppErrorBoundary>
        <App />
      </AppErrorBoundary>
    </React.StrictMode>
  );
}
