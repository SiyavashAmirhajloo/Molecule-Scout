"use client";

import { useEffect, useState } from "react";
import MoleculeTable, { MoleculeRow } from "./components/MoleculeTable";
import PoseViewer from "./components/PoseViewer";

type DockRow = {
  id: number;
  smiles: string;
  affinity: number | null;
  qed: number | null;
  novelty: number | null;
  rank_score: number | null;
  properties: MoleculeRow["properties"];
};

type DockingResult = {
  ranked: DockRow[];
  formula: string;
  formula_version: string;
  receptor: { pdb_id: string; center: number[] };
};

type DockingDetail = {
  id: number;
  smiles: string;
  affinity: number | null;
  formula_version: string;
  pose_pdbqt: string | null;
};

type Health = { db: string; redis: string };
type Hit = MoleculeRow & {
  chembl_id: string | null;
  citation: { database: string; entry_id: string | null; url: string };
};
type ProjectResponse = {
  project: { id: number; pdb_id: string | null; seed_source: string | null };
  seed_resolved: string | null;
  results: Hit[];
  message: string | null;
};
type GeneratedCandidate = { smiles: string; properties: MoleculeRow["properties"] };
type GenerationResult = {
  candidates: GeneratedCandidate[];
  metrics: {
    n_requested: number;
    n_valid: number;
    validity: number;
    uniqueness: number;
    novelty: number;
    diversity: number;
    avg_similarity_to_seed: number | null;
  };
  checkpoint: string;
  seed: number | null;
  conditioning: {
    mode: string;
    seed_smiles?: string;
    similarity?: number;
    reason?: string;
  };
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
  const [genCount, setGenCount] = useState("20");
  const [genJobId, setGenJobId] = useState<string | null>(null);
  const [genStatus, setGenStatus] = useState<string | null>(null);
  const [genResult, setGenResult] = useState<GenerationResult | null>(null);
  const [genError, setGenError] = useState<string | null>(null);
  // Docking state for the generation section.
  const [dockJobId, setDockJobId] = useState<string | null>(null);
  const [dockStatus, setDockStatus] = useState<string | null>(null);
  const [dockResult, setDockResult] = useState<DockingResult | null>(null);
  const [dockError, setDockError] = useState<string | null>(null);
  const [selectedPose, setSelectedPose] = useState<DockingDetail | null>(null);

  // Dock N generated candidates by index. Defined at component scope so the
  // list view above and the generate view below can share it.
  async function dockResultsList(
    projectId: number,
    rows: GeneratedCandidate[],
    limit = 20,
  ) {
    const smiles = Array.from(
      new Set(rows.map((c) => c.smiles).filter(Boolean)),
    ).slice(0, limit);
    setDockError(null);
    setDockResult(null);
    setSelectedPose(null);
    try {
      const r = await fetch(`${API}/projects/${projectId}/dock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_smiles: smiles }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const { id } = await r.json();
      setDockJobId(id);
      setDockStatus("queued");
      const poll = setInterval(async () => {
        const s = await fetch(`${API}/jobs/${id}`).then((x) => x.json());
        setDockStatus(s.status);
        if (s.status === "success") {
          clearInterval(poll);
          setDockResult(s.result as DockingResult);
        } else if (s.status === "failure") {
          clearInterval(poll);
          setDockError(s.error ?? "Docking failed");
        }
      }, 2000);
    } catch (err) {
      setDockError(err instanceof Error ? err.message : "Request failed");
    }
  }

  async function openPose(projectId: number, dockingId: number) {
    setSelectedPose(null);
    try {
      const r = await fetch(`${API}/projects/${projectId}/docking/${dockingId}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setSelectedPose((await r.json()) as DockingDetail);
    } catch (err) {
      setDockError(err instanceof Error ? err.message : "Request failed");
    }
  }

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
              <div className="mt-3">
                <MoleculeTable rows={response.results} />
                <button
                  onClick={async () => {
                    setGenError(null);
                    setGenResult(null);
                    try {
                      const r = await fetch(
                        `${API}/projects/${response.project.id}/generate`,
                        {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ n: 20 }),
                        },
                      );
                      if (!r.ok) throw new Error(`HTTP ${r.status}`);
                      const { id } = await r.json();
                      setGenJobId(id);
                      setGenStatus("queued");
                      const poll = setInterval(async () => {
                        const s = await fetch(`${API}/jobs/${id}`).then((x) => x.json());
                        setGenStatus(s.status);
                        if (s.status === "success") {
                          clearInterval(poll);
                          setGenResult(s.result);
                        } else if (s.status === "failure") {
                          clearInterval(poll);
                          setGenError(s.error ?? "Generation failed");
                        }
                      }, 2000);
                    } catch (err) {
                      setGenError(err instanceof Error ? err.message : "Request failed");
                    }
                  }}
                  className="mt-4 rounded bg-emerald-600 px-4 py-2 text-sm font-medium"
                >
                  Generate conditioned on these results
                </button>
              </div>
            )}
          </section>
        )}

        <section className="mt-10 border-t border-zinc-800 pt-6">
          <h2 className="text-lg font-medium">Generate candidates</h2>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setGenError(null);
              setGenResult(null);
              setGenJobId(null);
              try {
                const r = await fetch(`${API}/jobs/generate`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ n: Number(genCount) || 20 }),
                });
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                const { id } = await r.json();
                setGenJobId(id);
                setGenStatus("queued");
                const poll = setInterval(async () => {
                  const s = await fetch(`${API}/jobs/${id}`).then((x) => x.json());
                  setGenStatus(s.status);
                  if (s.status === "success") {
                    clearInterval(poll);
                    setGenResult(s.result);
                  } else if (s.status === "failure") {
                    clearInterval(poll);
                    setGenError(s.error ?? "Generation failed");
                  }
                }, 2000);
              } catch (err) {
                setGenError(err instanceof Error ? err.message : "Request failed");
              }
            }}
            className="mt-3 flex items-end gap-3"
          >
            <label className="block text-sm">
              <span className="text-zinc-400">Count</span>
              <input
                value={genCount}
                onChange={(e) => setGenCount(e.target.value)}
                className="mt-1 w-24 rounded bg-zinc-800 px-2 py-1.5 font-mono"
              />
            </label>
            <button
              type="submit"
              className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium"
            >
              Generate
            </button>
            {genStatus && genJobId && (
              <span className="pb-2 font-mono text-sm text-zinc-400">
                {genJobId.slice(0, 8)}… · {genStatus}
              </span>
            )}
          </form>
          {genError && (
            <p className="mt-4 rounded bg-red-950 p-3 text-sm text-red-200">{genError}</p>
          )}
          {genResult && (
            <div className="mt-4">
              <p className="font-mono text-sm text-zinc-400">
                validity {genResult.metrics.validity} · uniqueness{" "}
                {genResult.metrics.uniqueness} · novelty {genResult.metrics.novelty} ·
                diversity {genResult.metrics.diversity}
                {genResult.metrics.avg_similarity_to_seed !== null &&
                  ` · sim-to-seed ${genResult.metrics.avg_similarity_to_seed}`}{" "}
                · {genResult.checkpoint}
              </p>
              <p className="mt-1 text-sm text-zinc-400">
                {genResult.conditioning.mode === "retrieval-conditioned" ? (
                  <>
                    Conditioned on{" "}
                    <code className="font-mono text-zinc-200">
                      {genResult.conditioning.seed_smiles}
                    </code>{" "}
                    (similarity {genResult.conditioning.similarity})
                  </>
                ) : (
                  <>Fallback: {genResult.conditioning.reason ?? "unconditioned"}</>
                )}
              </p>
              <div className="mt-3">
                <MoleculeTable
                  rows={genResult.candidates.map((c) => ({
                    canonical_smiles: c.smiles,
                    name: null,
                    properties: c.properties,
                  }))}
                />
              </div>
              {response?.project.pdb_id && response?.project.id && (
                <button
                  onClick={() =>
                    dockResultsList(response.project.id, genResult.candidates)
                  }
                  className="mt-4 rounded bg-emerald-600 px-4 py-2 text-sm font-medium"
                >
                  Dock against {response.project.pdb_id}
                </button>
              )}
            </div>
          )}
          {dockError && (
            <p className="mt-4 rounded bg-red-950 p-3 text-sm text-red-200">{dockError}</p>
          )}
          {dockStatus && dockJobId && (
            <p className="mt-3 pb-2 font-mono text-sm text-zinc-400">
              {dockJobId.slice(0, 8)}… · {dockStatus}
            </p>
          )}
          {dockResult && response?.project.id && (
            <div className="mt-4">
              <p className="font-mono text-sm text-zinc-400">
                {dockResult.ranked.length} candidates · receptor{" "}
                {dockResult.receptor.pdb_id} · {dockResult.formula_version}
              </p>
              <div className="mt-3">
                <MoleculeTable
                  rows={dockResult.ranked.map((r) => ({
                    canonical_smiles: r.smiles,
                    name: null,
                    properties: r.properties,
                    docking_id: r.id,
                    affinity: r.affinity,
                    novelty: r.novelty,
                    rank_score: r.rank_score,
                  }))}
                  onSelect={(dockingId) =>
                    openPose(response.project.id, dockingId)
                  }
                />
              </div>
              {selectedPose?.pose_pdbqt && (
                <div className="mt-4 rounded-lg bg-zinc-900 p-4">
                  <p className="mb-2 font-mono text-xs text-zinc-400">
                    Pose for <code>{selectedPose.smiles}</code>
                    {selectedPose.affinity !== null &&
                      ` · ${selectedPose.affinity.toFixed(2)} kcal/mol · score ${dockResult.formula_version}`}
                  </p>
                  <PoseViewer posePdbqt={selectedPose.pose_pdbqt} />
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
