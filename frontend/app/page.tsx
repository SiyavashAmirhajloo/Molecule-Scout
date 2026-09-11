"use client";

import { useEffect, useState } from "react";

type Health = { db: string; redis: string };
type Hit = {
  canonical_smiles: string;
  chembl_id: string | null;
  name: string | null;
  similarity: number;
  citation: { database: string; entry_id: string | null; url: string };
};
type ProjectResponse = {
  project: { id: number; pdb_id: string | null; seed_source: string | null };
  seed_resolved: string | null;
  results: Hit[];
  message: string | null;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [pdbId, setPdbId] = useState("");
  const [seedSmiles, setSeedSmiles] = useState("CC(=O)Oc1ccccc1C(=O)O");
  const [seedName, setSeedName] = useState("");
  const [response, setResponse] = useState<ProjectResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const body: Record<string, string> = {};
      if (pdbId.trim()) body.pdb_id = pdbId.trim();
      if (seedSmiles.trim()) body.seed_smiles = seedSmiles.trim();
      else if (seedName.trim()) body.seed_name = seedName.trim();
      const r = await fetch(`${API}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const detail = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(
          typeof detail.detail === "string" ? detail.detail : JSON.stringify(detail.detail),
        );
      }
      setResponse(await r.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="text-2xl font-semibold">Molecule Scout</h1>
        <p className="mt-1 text-sm text-zinc-400">
          API: {health ? `db: ${health.db}, redis: ${health.redis}` : "unreachable"}
        </p>

        <form onSubmit={submit} className="mt-8 grid gap-3 rounded-lg bg-zinc-900 p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="block text-sm">
              <span className="text-zinc-400">PDB ID (target)</span>
              <input
                value={pdbId}
                onChange={(e) => setPdbId(e.target.value)}
                placeholder="1ABC"
                className="mt-1 w-full rounded bg-zinc-800 px-2 py-1.5 font-mono"
              />
            </label>
            <label className="block text-sm">
              <span className="text-zinc-400">Seed SMILES</span>
              <input
                value={seedSmiles}
                onChange={(e) => setSeedSmiles(e.target.value)}
                placeholder="CCO"
                className="mt-1 w-full rounded bg-zinc-800 px-2 py-1.5 font-mono"
              />
            </label>
            <label className="block text-sm">
              <span className="text-zinc-400">…or seed name</span>
              <input
                value={seedName}
                onChange={(e) => setSeedName(e.target.value)}
                placeholder="ASPIRIN"
                className="mt-1 w-full rounded bg-zinc-800 px-2 py-1.5 font-mono"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Retrieving…" : "Create project & retrieve"}
          </button>
        </form>

        {error && <p className="mt-4 rounded bg-red-950 p-3 text-sm text-red-200">{error}</p>}

        {response && (
          <section className="mt-6">
            <p className="text-sm text-zinc-400">
              Project #{response.project.id}
              {response.project.pdb_id && ` · target ${response.project.pdb_id}`}
              {response.seed_resolved && (
                <>
                  {" · seed "}
                  <code className="font-mono text-zinc-200">{response.seed_resolved}</code>
                </>
              )}
            </p>
            {response.message && (
              <p className="mt-3 rounded bg-zinc-900 p-3 text-sm text-zinc-300">
                {response.message}
              </p>
            )}
            {response.results.length > 0 && (
              <table className="mt-3 w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="py-2 pr-4">SMILES</th>
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Similarity</th>
                    <th className="py-2">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {response.results.map((hit) => (
                    <tr key={hit.chembl_id ?? hit.canonical_smiles} className="border-b border-zinc-900">
                      <td className="max-w-xs truncate py-2 pr-4 font-mono text-xs">
                        {hit.canonical_smiles}
                      </td>
                      <td className="py-2 pr-4">{hit.name ?? "—"}</td>
                      <td className="py-2 pr-4 font-mono">{hit.similarity.toFixed(4)}</td>
                      <td className="py-2">
                        <a
                          href={hit.citation.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-400 hover:underline"
                        >
                          {hit.citation.entry_id}
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
