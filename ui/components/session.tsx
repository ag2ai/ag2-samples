"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import { ReactNode, SubmitEvent, useState, useSyncExternalStore } from "react";

const STORAGE_KEY = "weather-ag-ui.session";

type Session = { token: string; name: string };

// Demonstration only: keeping the Access token in localStorage exposes it to any script on
// the page. A production app would use an HttpOnly cookie or its identity provider's SDK.
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

function readStored(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function store(session: Session | null) {
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Storage unavailable: the User stays signed out after a reload.
  }
  listeners.forEach((listener) => listener());
}

// A stored token past its expiry is treated as signed out, so the User is asked again
// instead of seeing every request refused. The signature is the backend's to check; this
// only reads the expiry claim.
function parseSession(raw: string | null): Session | null {
  try {
    const session = raw ? (JSON.parse(raw) as Session) : null;
    if (!session) return null;
    const claims = JSON.parse(atob(session.token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return claims.exp * 1000 > Date.now() ? session : null;
  } catch {
    return null;
  }
}

export function Session({ children }: { children: ReactNode }) {
  // `undefined` on the server and during hydration, so the first paint matches the server's.
  const raw = useSyncExternalStore(subscribe, readStored, () => undefined);
  if (raw === undefined) return null;
  const session = parseSession(raw);

  if (!session) {
    return (
      <SignIn
        onSignedIn={store}
      />
    );
  }

  const signOut = () => store(null);

  return (
    <>
      <div className="fixed top-0 inset-x-0 z-30 flex items-center justify-end gap-3 px-4 py-2 text-sm text-gray-400 bg-[#0d0d0d]">
        <span>
          Signed in as <strong className="text-gray-200">{session.name}</strong>
        </span>
        <button
          onClick={signOut}
          className="rounded-full border border-[#2e2e2e] px-3 py-1 hover:bg-[#171717]"
        >
          Sign out
        </button>
      </div>
      {/* Keyed by token: signing out and in again mounts a fresh, empty chat. */}
      <CopilotKit
        key={session.token}
        agent="agenticChatAgent"
        runtimeUrl="/api/copilotkit"
        headers={{ Authorization: `Bearer ${session.token}` }}
      >
        {children}
      </CopilotKit>
    </>
  );
}

function SignIn({ onSignedIn }: { onSignedIn: (session: Session) => void }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? "Could not sign in.");
      onSignedIn({ token: body.token, name: body.name });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="dark min-h-screen bg-[#0d0d0d] flex items-center justify-center">
      <form onSubmit={submit} className="w-80 space-y-4 text-gray-200">
        <h1 className="text-xl font-medium">Weather Assistant</h1>
        <p className="text-sm text-gray-500">
          Demonstration sign-in: enter any name. No password is checked.
        </p>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your name"
          className="w-full rounded-xl bg-zinc-800 px-4 py-3 focus:outline-none"
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          disabled={busy || !name.trim()}
          className="w-full rounded-xl bg-zinc-700 px-4 py-3 disabled:opacity-50"
        >
          Sign in
        </button>
      </form>
    </main>
  );
}
