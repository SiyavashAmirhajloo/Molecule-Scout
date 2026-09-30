"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import MoleculeTable, { MoleculeRow } from "../../components/MoleculeTable";

const PoseViewer = dynamic(() => import("../../components/PoseViewer"), {
  loading: () => (
    <p className="py-10 text-center text-sm text-lab-muted">Loading viewer…</p>
  ),
});

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Project = { id: number; pdb_id: string | null };
type RetrievalHit = MoleculeRow & {
  chembl_id: string | null;
  citation: { database: string; entry_id: string | null; url: string };
};
type ProjectResponse = {
  project: Project & { seed_source: string | null };
  seed_resolved: string | null;
  results: RetrievalHit[];
  message: string | null;
};
type GeneratedCandidate = { smiles: string; properties: MoleculeRow["properties"] };
type GenerationResult = {
  candidates: GeneratedCandidate[];
  metrics: Record<string, number>;
  checkpoint: string;
  seed: number | null;
  conditioning: {
    mode: string;
    seed_smiles?: string;
    similarity?: number;
    reason?: string;
  };
};
type DockedRow = {
  id: number;
  smiles: string;
  affinity: number | null;
  qed: number | null;
  novelty: number | null;
  rank_score: number | null;
  properties: MoleculeRow["properties"];
};
type DockingResult = {
  ranked: DockedRow[];
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

type Stage = "retrieve" | "generate" | "dock";

function useJobPoll<T>(): [string | null, string | null, T | null, string | null, (id: string) => void, () => void] {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback((id: string) => {
    setJobId(id);
    setStatus("queued");
    setResult(null);
    setError(null);
    const poll = setInterval(async () => {
      try {
        const s = await fetch(`${API}/jobs/${id}`).then((x) => x.json());
        setStatus(s.status);
        if (s.status === "success") {
          clearInterval(poll);
          setResult(s.result as T);
        } else if (s.status === "failure") {
          clearInterval(poll);
          setError(s.error ?? "Job failed");
        }
      } catch {
        clearInterval(poll);
        setError("Lost contact with the job — try again");
      }
    }, 2000);
  }, []);

  const reset = useCallback(() => {
    setJobId(null);
    setStatus(null);
    setResult(null);
    setError(null);
  }, []);

  return [jobId, status, result, error, start, reset];
}

export default function ProjectPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage>("retrieve");
  const [genCount, setGenCount] = useState("20");
  const [selectedPose, setSelectedPose] = useState<DockingDetail | null>(null);
  const [poseError, setPoseError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [needsRefresh, setNeedsRefresh] = useState(false);

  const [genJobId, genStatus, genResult, genError, startGen, resetGen] =
    useJobPoll<GenerationResult>();
  const [dockJobId, dockStatus, dockResult, dockError, startDock, resetDock] =
    useJobPoll<DockingResult>();

  useEffect(() => {
    fetch(`${API}/projects/${projectId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data: ProjectResponse) => {
        setProject(data);
        setNeedsRefresh(data.results.length === 0);
      })
      .catch(() => setError("Project not found or the API is unreachable."));
  }, [projectId]);

  // Refresh the project after a slow background step lands.
  const refreshProject = useCallback(() => {
    fetch(`${API}/projects/${projectId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data: ProjectResponse) => setProject(data))
      .catch(() => {});
  }, [projectId]);

  // When the dock job finishes, merge the ranks into the table view.
  const dockRanked = useMemo(() => {
    if (!dockResult || !genResult) return null;
    return dockResult.ranked.map((r) => ({
      canonical_smiles: r.smiles,
      name: null as string | null,
      properties: r.properties,
      docking_id: r.id,
      affinity: r.affinity,
      novelty: r.novelty,
      rank_score: r.rank_score,
    }));
  }, [dockResult, genResult]);

  async function runGeneration() {
    resetGen();
    resetDock();
    setSelectedPose(null);
    setActionError(null);
    const n = Number(genCount) || 20;
    try {
      const r = await fetch(`${API}/projects/${projectId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => null);
        throw new Error(d?.detail ?? `HTTP ${r.status}`);
      }
      const { id } = await r.json();
      startGen(id);
      setStage("generate");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Generation failed to start");
    }
  }

  async function runDocking() {
    if (!genResult) return;
    resetDock();
    setSelectedPose(null);
    setActionError(null);
    const smiles = Array.from(
      new Set(genResult.candidates.map((c) => c.smiles).filter(Boolean)),
    ).slice(0, 20);
    try {
      const r = await fetch(`${API}/projects/${projectId}/dock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_smiles: smiles }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => null);
        throw new Error(d?.detail ?? `HTTP ${r.status}`);
      }
      const { id } = await r.json();
      startDock(id);
      setStage("dock");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Docking failed to start");
    }
  }

  async function openPose(dockingId: number) {
    setPoseError(null);
    try {
      const r = await fetch(`${API}/projects/${projectId}/docking/${dockingId}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const detail = (await r.json()) as DockingDetail;
      if (!detail.pose_pdbqt) setPoseError("No pose stored for this result.");
      setSelectedPose(detail);
    } catch {
      setPoseError("Could not load the pose.");
    }
  }

  if (error) {
    return (
      <div className="bench">
        <p className="panel text-sm text-lab-danger">{error}</p>
        <Link href="/" className="mt-4 inline-block text-sm text-lab-emerald">
          ← New project
        </Link>
      </div>
    );
  }
  if (!project) {
    return (
      <div className="bench">
        <p className="py-16 text-center text-sm text-lab-muted">Loading project…</p>
      </div>
    );
  }

  const stages: { key: Stage; label: string; done: boolean }[] = [
    { key: "retrieve", label: "Retrieve", done: project.results.length > 0 },
    {
      key: "generate",
      label: "Generate",
      done: genResult !== null && genResult.candidates.length > 0,
    },
    { key: "dock", label: "Dock", done: dockRanked !== null },
  ];

  return (
    <div className="bench">
      {/* Bench header */}
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="text-xl font-semibold tracking-tight">
          Project #{project.project.id}
          {project.project.pdb_id && (
            <span className="ml-2 font-mono text-sm font-normal text-lab-amber">
              {project.project.pdb_id}
            </span>
          )}
        </h1>
        <Link href="/" className="text-sm text-lab-muted transition hover:text-lab-text">
          ← New project
        </Link>
      </div>
      {project.seed_resolved && (
        <p className="mt-1 font-mono text-xs text-lab-muted">
          seed {project.seed_resolved}
        </p>
      )}

      {/* Pipeline connector */}
      <ol className="mt-5 flex items-center gap-0 overflow-x-auto" aria-label="Pipeline progress">
        {stages.map((s, i) => (
          <li key={s.key} className="flex flex-1 items-center last:flex-none">
            <button
              onClick={() => setStage(s.key)}
              disabled={s.key === "dock" && !genResult}
              className={`flex cursor-pointer items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition ${
                stage === s.key
                  ? "bg-lab-surface text-lab-text"
                  : "text-lab-muted hover:text-lab-text disabled:cursor-not-allowed disabled:opacity-40"
              }`}
              aria-current={stage === s.key ? "step" : undefined}
            >
              <span
                className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                  s.done
                    ? "bg-lab-emerald text-lab-bg"
                    : stage === s.key
                      ? "bg-lab-amber text-lab-bg"
                      : "border border-lab-line bg-lab-surface text-lab-muted"
                }`}
              >
                {s.done ? "✓" : i + 1}
              </span>
              {s.label}
            </button>
            {i < stages.length - 1 && (
              <span className="mx-1 h-px min-w-6 flex-1 bg-lab-line" aria-hidden="true" />
            )}
          </li>
        ))}
      </ol>

      {/* Retrieval stage */}
      {stage === "retrieve" && (
        <section className="panel mt-5" aria-live="polite">
          <div className="mb-3 flex items-baseline justify-between gap-3">
            <h2 className="panel-title">Known analogs · ChEMBL corpus</h2>
            {needsRefresh && project.results.length > 0 && (
              <button onClick={refreshProject} className="btn-secondary text-xs">
                Refresh
              </button>
            )}
          </div>
          {project.message && (
            <p className="mb-3 rounded-md bg-lab-surface px-3 py-2 text-sm text-lab-muted">
              {project.message}
            </p>
          )}
          {project.results.length > 0 ? (
            <MoleculeTable rows={project.results} />
          ) : (
            <p className="py-8 text-center text-sm text-lab-muted">
              No compounds retrieved yet — a fresh project will fill this in.
            </p>
          )}
          <button
            onClick={runGeneration}
            disabled={project.results.length === 0}
            className="btn-primary mt-4"
          >
            Generate candidates
          </button>
          {actionError && (
            <p className="mt-3 text-sm text-lab-danger">{actionError}</p>
          )}
        </section>
      )}

      {/* Generation stage */}
      {stage === "generate" && (
        <section className="panel mt-5" aria-live="polite">
          <div className="mb-3 flex flex-wrap items-end gap-3">
            <h2 className="panel-title">Generated candidates</h2>
            <label className="flex items-center gap-2 text-xs text-lab-muted">
              Count
              <input
                value={genCount}
                onChange={(e) => setGenCount(e.target.value)}
                className="w-16 rounded border border-lab-line bg-lab-surface px-2 py-1 font-mono text-lab-text"
              />
            </label>
            <button
              onClick={() => runGeneration().catch(() => {})}
              className="btn-secondary text-xs"
            >
              Regenerate
            </button>
          </div>

          {genStatus && genJobId && genStatus !== "success" && (
            <p className="rounded-md bg-lab-surface px-3 py-2 font-mono text-xs text-lab-muted">
              {genJobId.slice(0, 8)}… · {genStatus} — diffusion sampling takes
              a minute or two on CPU
            </p>
          )}
          {genError && <p className="text-sm text-lab-danger">{genError}</p>}

          {genResult && (
            <>
              <p className="font-mono text-xs text-lab-muted">
                validity {genResult.metrics.validity} · uniqueness{" "}
                {genResult.metrics.uniqueness} · novelty{" "}
                {genResult.metrics.novelty} · diversity{" "}
                {genResult.metrics.diversity} · {genResult.checkpoint}
              </p>
              <p className="mt-1 text-xs text-lab-muted">
                {genResult.conditioning.mode === "retrieval-conditioned" ? (
                  <>
                    Conditioned on{" "}
                    <code className="font-mono text-lab-text">
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
              {project.project.pdb_id && (
                <button onClick={runDocking} className="btn-primary mt-4">
                  Dock against {project.project.pdb_id}
                </button>
              )}
              {actionError && (
                <p className="mt-3 text-sm text-lab-danger">{actionError}</p>
              )}
            </>
          )}
        </section>
      )}

      {/* Docking stage */}
      {stage === "dock" && (
        <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_26rem]">
          <section className="panel min-w-0" aria-live="polite">
            <h2 className="panel-title mb-3">Docked &amp; ranked</h2>
            {dockStatus && dockJobId && dockStatus !== "success" && (
              <p className="rounded-md bg-lab-surface px-3 py-2 font-mono text-xs text-lab-muted">
                {dockJobId.slice(0, 8)}… · {dockStatus} — Vina takes several
                minutes for a batch
              </p>
            )}
            {dockError && <p className="text-sm text-lab-danger">{dockError}</p>}
            {dockRanked ? (
              <MoleculeTable rows={dockRanked} onSelect={openPose} />
            ) : (
              <p className="py-8 text-center text-sm text-lab-muted">
                {genResult
                  ? "Run docking from the Generate tab."
                  : "Generate candidates first, then dock them."}
              </p>
            )}
          </section>

          {/* Finding drawer: the selected result, beside the table. */}
          <aside className="panel h-fit lg:sticky lg:top-20" aria-live="polite">
            <h2 className="panel-title">Finding</h2>
            {poseError && (
              <p className="mt-3 text-sm text-lab-danger">{poseError}</p>
            )}
            {selectedPose ? (
              <div className="mt-3">
                <p className="break-all font-mono text-xs text-lab-muted">
                  {selectedPose.smiles}
                </p>
                {selectedPose.affinity !== null && (
                  <p className="mt-1 font-mono text-sm text-lab-amber">
                    {selectedPose.affinity.toFixed(2)} kcal/mol · score{" "}
                    {selectedPose.formula_version}
                  </p>
                )}
                {selectedPose.pose_pdbqt ? (
                  <div className="mt-3">
                    {/* Code-split: 3Dmol ships only when someone opens a result. */}
                    <PoseViewer posePdbqt={selectedPose.pose_pdbqt} />
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-lab-muted">
                    No pose stored for this result.
                  </p>
                )}
              </div>
            ) : (
              <p className="mt-3 text-sm text-lab-muted">
                Click a ranked row to inspect its pose and scores here —
                beside the table, where it belongs.
              </p>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
