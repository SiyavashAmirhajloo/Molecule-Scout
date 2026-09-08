"use client";

import { useEffect, useState } from "react";

type Health = { db: string; redis: string };

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/health`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  const status = error ? "unreachable" : health ? `db: ${health.db}, redis: ${health.redis}` : "…";

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-100">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Molecule Scout</h1>
        <p className="mt-2 text-sm text-zinc-400">API: {status}</p>
      </div>
    </main>
  );
}
