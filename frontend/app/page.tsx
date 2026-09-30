"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const router = useRouter();
  const [pdbId, setPdbId] = useState("");
  const [seedSmiles, setSeedSmiles] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const trimmed = seedSmiles.trim();
      if (!pdbId.trim() && !trimmed) throw new Error("Provide a PDB ID or a seed molecule");
      const body: Record<string, string> = {};
      if (pdbId.trim()) body.pdb_id = pdbId.trim();
      if (trimmed) body.seed_smiles = trimmed;
      const r = await fetch(`${API}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail));
      }
      const { project } = await r.json();
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bench">
      <section className="panel">
        <h1 className="text-2xl font-semibold tracking-tight">
          Start a project
        </h1>
        <p className="mt-1 text-sm text-lab-muted">
          Target protein + seed molecule. Retrieval, generation, and docking follow.
        </p>

        <form onSubmit={submit} className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="pdb" className="field-label">
              Target PDB ID
            </label>
            <input
              id="pdb"
              value={pdbId}
              onChange={(e) => setPdbId(e.target.value)}
              placeholder="1M17"
              className="field-input"
            />
            <p className="mt-1 text-xs text-lab-muted">
              EGFR kinase domain with erlotinib co-crystal
            </p>
          </div>
          <div>
            <label htmlFor="seed" className="field-label">
              Seed molecule
            </label>
            <input
              id="seed"
              value={seedSmiles}
              onChange={(e) => setSeedSmiles(e.target.value)}
              placeholder="SMILES or name (e.g. ERLOTINIB)"
              className="field-input"
            />
            <p className="mt-1 text-xs text-lab-muted">
              SMILES parses directly; names resolve against the ChEMBL corpus
            </p>
          </div>
          <div className="sm:col-span-2">
            <button type="submit" disabled={loading} className="btn-primary w-full sm:w-auto">
              {loading ? "Creating…" : "Create project"}
            </button>
          </div>
        </form>

        {error && (
          <p className="mt-4 rounded-md border border-lab-danger/30 bg-lab-danger/10 px-3 py-2 text-sm text-lab-danger">
            {error}
          </p>
        )}
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        {[
          { n: "01", t: "Retrieve", d: "Known analogs from ChEMBL with citations" },
          { n: "02", t: "Generate", d: "Diffusion candidates conditioned on retrieval" },
          { n: "03", t: "Dock", d: "Vina affinity + composite rank score" },
        ].map((s) => (
          <div key={s.n} className="panel">
            <span className="text-xs font-mono text-lab-amber">{s.n}</span>
            <h2 className="mt-1 text-sm font-semibold">{s.t}</h2>
            <p className="mt-1 text-xs text-lab-muted">{s.d}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
