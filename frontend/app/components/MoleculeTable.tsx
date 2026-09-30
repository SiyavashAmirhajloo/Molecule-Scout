"use client";

import { useMemo, useState } from "react";

export type Properties = {
  qed: number;
  sa_score: number;
  lipinski: {
    molecular_weight: number;
    logp: number;
    h_bond_donors: number;
    h_bond_acceptors: number;
    violations: number;
    passes: boolean;
  };
  pains: { matches: number; passes: boolean };
};

export type MoleculeRow = {
  canonical_smiles: string;
  name: string | null;
  similarity?: number;
  citation?: { entry_id: string | null; url: string };
  properties: Properties;
  docking_id?: number;
  affinity?: number | null;
  novelty?: number | null;
  rank_score?: number | null;
};

export const RANK_FORMULA =
  "rank_score = 0.5 * norm_affinity + 0.3 * QED + 0.2 * novelty";

type SortKey =
  | "similarity"
  | "qed"
  | "sa_score"
  | "molecular_weight"
  | "logp"
  | "rank_score"
  | "affinity";

function cellValue(row: MoleculeRow, key: SortKey): number {
  switch (key) {
    case "similarity":
      return row.similarity ?? 0;
    case "qed":
      return row.properties.qed;
    case "sa_score":
      return row.properties.sa_score;
    case "molecular_weight":
      return row.properties.lipinski.molecular_weight;
    case "logp":
      return row.properties.lipinski.logp;
    case "rank_score":
      return row.rank_score ?? 0;
    case "affinity":
      return row.affinity === null || row.affinity === undefined
        ? Number.NEGATIVE_INFINITY
        : -row.affinity;
  }
}

function Pass({ ok }: { ok: boolean }) {
  return (
    <span
      className={ok ? "text-lab-emerald" : "text-lab-danger"}
      aria-hidden="true"
    >
      {ok ? "✓" : "✗"}
    </span>
  );
}

export default function MoleculeTable({
  rows,
  onSelect,
}: {
  rows: MoleculeRow[];
  onSelect?: (dockingId: number) => void;
}) {
  const hasRanks = rows.some((r) => r.rank_score !== undefined);
  const [sortKey, setSortKey] = useState<SortKey>(
    hasRanks ? "rank_score" : "similarity",
  );
  const [sortDesc, setSortDesc] = useState(true);
  const [minQed, setMinQed] = useState(0);
  const [maxSa, setMaxSa] = useState(10);
  const [lipinskiOnly, setLipinskiOnly] = useState(false);
  const [painsFreeOnly, setPainsFreeOnly] = useState(false);

  const visible = useMemo(() => {
    const filtered = rows.filter(
      (r) =>
        r.properties.qed >= minQed &&
        r.properties.sa_score <= maxSa &&
        (!lipinskiOnly || r.properties.lipinski.passes) &&
        (!painsFreeOnly || r.properties.pains.passes),
    );
    return [...filtered].sort((a, b) =>
      sortDesc
        ? cellValue(b, sortKey) - cellValue(a, sortKey)
        : cellValue(a, sortKey) - cellValue(b, sortKey),
    );
  }, [rows, sortKey, sortDesc, minQed, maxSa, lipinskiOnly, painsFreeOnly]);

  function header(label: string, key: SortKey) {
    const active = sortKey === key;
    return (
      <th
        className="cursor-pointer select-none py-2.5 pr-4 text-left transition hover:text-lab-text"
        onClick={() => {
          if (active) setSortDesc(!sortDesc);
          else {
            setSortKey(key);
            setSortDesc(true);
          }
        }}
      >
        {label}
        {active && (
          <span className="ml-1 text-lab-amber">{sortDesc ? "▼" : "▲"}</span>
        )}
      </th>
    );
  }

  return (
    <div className="min-w-0">
      {hasRanks && (
        <p className="mb-3 rounded-lg border border-lab-line/60 bg-lab-surface px-3 py-2 text-xs text-lab-muted">
          Ranked by{" "}
          <code className="font-mono text-lab-amber">{RANK_FORMULA}</code>.{" "}
          <span className="text-lab-muted/70">
            norm_affinity is min–max within this batch — scores are never
            comparable across runs.
          </span>
        </p>
      )}

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-lab-line bg-lab-panel px-3 py-2.5 text-sm">
        <label className="flex items-center gap-1.5 text-lab-muted">
          QED ≥
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            value={minQed}
            onChange={(e) => setMinQed(Number(e.target.value))}
            className="w-14 rounded border border-lab-line bg-lab-surface px-2 py-1 font-mono text-lab-text"
          />
        </label>
        <label className="flex items-center gap-1.5 text-lab-muted">
          SA ≤
          <input
            type="number"
            min={1}
            max={10}
            step={0.5}
            value={maxSa}
            onChange={(e) => setMaxSa(Number(e.target.value))}
            className="w-14 rounded border border-lab-line bg-lab-surface px-2 py-1 font-mono text-lab-text"
          />
        </label>
        <label className="flex items-center gap-1.5 text-lab-muted">
          <input
            type="checkbox"
            checked={lipinskiOnly}
            onChange={(e) => setLipinskiOnly(e.target.checked)}
            className="accent-lab-emerald"
          />
          Lipinski ✓
        </label>
        <label className="flex items-center gap-1.5 text-lab-muted">
          <input
            type="checkbox"
            checked={painsFreeOnly}
            onChange={(e) => setPainsFreeOnly(e.target.checked)}
            className="accent-lab-emerald"
          />
          PAINS-free
        </label>
        <span className="ml-auto font-mono text-xs text-lab-muted/70">
          {visible.length} / {rows.length}
        </span>
      </div>

      <div className="mt-4 overflow-x-auto rounded-lg border border-lab-line">
        <table className="w-full min-w-[52rem] text-left text-sm">
          <thead>
            <tr className="border-b border-lab-line bg-lab-panel text-lab-muted">
              {hasRanks && <th className="py-2.5 pl-3 pr-4 text-lab-amber">#</th>}
              <th className="py-2.5 pr-4">Structure</th>
              <th className="py-2.5 pr-4">Name</th>
              {header("Sim", "similarity")}
              {header("QED", "qed")}
              {header("SA", "sa_score")}
              {header("MW", "molecular_weight")}
              {header("logP", "logp")}
              {hasRanks && header("Affinity", "affinity")}
              {hasRanks && header("Score", "rank_score")}
              <th className="py-2.5 pr-4">Lip</th>
              <th className="py-2.5 pr-4">PAINS</th>
              <th className="py-2.5 pr-4">Source</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 && (
              <tr>
                <td
                  colSpan={hasRanks ? 13 : 11}
                  className="py-10 text-center text-sm text-lab-muted"
                >
                  No molecules match these filters — relax them.
                </td>
              </tr>
            )}
            {visible.map((row, i) => (
              <tr
                key={
                  row.docking_id ??
                  row.citation?.entry_id ??
                  row.canonical_smiles
                }
                onPointerUp={(e) => {
                  if (
                    onSelect &&
                    row.docking_id !== undefined &&
                    e.button === 0
                  ) {
                    onSelect(row.docking_id as number);
                  }
                }}
                className={`border-b border-lab-line/60 transition ${
                  onSelect && row.docking_id !== undefined
                    ? "cursor-pointer hover:bg-lab-surface/70"
                    : ""
                }`}
              >
                {hasRanks && (
                  <td className="pl-3 pr-4 py-2.5 font-mono text-lab-muted">
                    {i + 1}
                  </td>
                )}
                <td className="max-w-[14rem] truncate py-2.5 pr-4 font-mono text-xs">
                  {row.canonical_smiles}
                </td>
                <td className="py-2.5 pr-4">{row.name ?? "—"}</td>
                <td className="py-2.5 pr-4 font-mono">
                  {row.similarity !== undefined ? row.similarity.toFixed(4) : "—"}
                </td>
                <td className="py-2.5 pr-4 font-mono">{row.properties.qed.toFixed(3)}</td>
                <td className="py-2.5 pr-4 font-mono">{row.properties.sa_score.toFixed(2)}</td>
                <td className="py-2.5 pr-4 font-mono">
                  {row.properties.lipinski.molecular_weight.toFixed(1)}
                </td>
                <td className="py-2.5 pr-4 font-mono">{row.properties.lipinski.logp.toFixed(2)}</td>
                {hasRanks && (
                  <td className="py-2.5 pr-4 font-mono">
                    {row.affinity !== null && row.affinity !== undefined
                      ? row.affinity.toFixed(2)
                      : "—"}
                  </td>
                )}
                {hasRanks && (
                  <td className="py-2.5 pr-4 font-mono font-medium text-lab-amber">
                    {row.rank_score !== null && row.rank_score !== undefined
                      ? row.rank_score.toFixed(3)
                      : "—"}
                  </td>
                )}
                <td className="py-2.5 pr-4">
                  <Pass ok={row.properties.lipinski.passes} />
                </td>
                <td className="py-2.5 pr-4">
                  <Pass ok={row.properties.pains.passes} />
                </td>
                <td className="py-2.5">
                  {row.citation ? (
                    <a
                      href={row.citation.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-lab-emerald underline-offset-2 hover:underline"
                      onPointerUp={(e) => e.stopPropagation()}
                    >
                      {row.citation.entry_id}
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
