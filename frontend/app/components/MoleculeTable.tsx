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
  /** V6 docking fields — present only on rows from a docking run. */
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
      // Affinities are negative: more negative = better binder. Negate so a
      // descending sort puts the best binder first. Failed docks sort last.
      return row.affinity === null || row.affinity === undefined
        ? Number.NEGATIVE_INFINITY
        : -row.affinity;
  }
}

function Pass({ ok }: { ok: boolean }) {
  return ok ? (
    <span className="text-emerald-400">✓</span>
  ) : (
    <span className="text-red-400">✗</span>
  );
}

export default function MoleculeTable({
  rows,
  onSelect,
}: {
  rows: MoleculeRow[];
  /** Called with the row's docking result id when the user clicks a docked row. */
  onSelect?: (dockingId: number) => void;
}) {
  const hasRanks = rows.some((r) => r.rank_score !== undefined);
  const [sortKey, setSortKey] = useState<SortKey>(hasRanks ? "rank_score" : "similarity");
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
      <th className="cursor-pointer py-2 pr-4 select-none" onClick={() => {
        if (active) setSortDesc(!sortDesc);
        else {
          setSortKey(key);
          setSortDesc(true);
        }
      }}>
        {label}
        {active && <span className="ml-1 text-emerald-400">{sortDesc ? "▼" : "▲"}</span>}
      </th>
    );
  }

  return (
    <div>
      {hasRanks && (
        <p className="mb-2 rounded bg-zinc-900 px-3 py-2 text-xs text-zinc-400">
          Ranked by{" "}
          <code className="font-mono text-zinc-300">{RANK_FORMULA}</code>.{" "}
          <span className="text-zinc-500">
            norm_affinity is min-max normalized within this batch only, so these
            scores are not comparable across runs.
          </span>
        </p>
      )}
      <div className="flex flex-wrap items-center gap-4 rounded-lg bg-zinc-900 p-3 text-sm">
        <label className="flex items-center gap-2 text-zinc-400">
          QED ≥
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            value={minQed}
            onChange={(e) => setMinQed(Number(e.target.value))}
            className="w-16 rounded bg-zinc-800 px-2 py-1 font-mono"
          />
        </label>
        <label className="flex items-center gap-2 text-zinc-400">
          SA ≤
          <input
            type="number"
            min={1}
            max={10}
            step={0.5}
            value={maxSa}
            onChange={(e) => setMaxSa(Number(e.target.value))}
            className="w-16 rounded bg-zinc-800 px-2 py-1 font-mono"
          />
        </label>
        <label className="flex items-center gap-2 text-zinc-400">
          <input
            type="checkbox"
            checked={lipinskiOnly}
            onChange={(e) => setLipinskiOnly(e.target.checked)}
          />
          Lipinski ✓ only
        </label>
        <label className="flex items-center gap-2 text-zinc-400">
          <input
            type="checkbox"
            checked={painsFreeOnly}
            onChange={(e) => setPainsFreeOnly(e.target.checked)}
          />
          PAINS-free only
        </label>
        <span className="ml-auto text-zinc-500">
          {visible.length}/{rows.length}
        </span>
      </div>

      <table className="mt-3 w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-800 text-zinc-400">
            {hasRanks && <th className="py-2 pr-4">Rank</th>}
            <th className="py-2 pr-4">SMILES</th>
            <th className="py-2 pr-4">Name</th>
            {header("Sim", "similarity")}
            {header("QED", "qed")}
            {header("SA", "sa_score")}
            {header("MW", "molecular_weight")}
            {header("logP", "logp")}
            {hasRanks && header("Affinity", "affinity")}
            {hasRanks && header("Score", "rank_score")}
            <th className="py-2 pr-4">Lipinski</th>
            <th className="py-2 pr-4">PAINS</th>
            <th className="py-2">Source</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((row, i) => (
            <tr
              key={row.docking_id ?? row.citation?.entry_id ?? row.canonical_smiles}
              onClick={
                onSelect && row.docking_id !== undefined
                  ? () => onSelect(row.docking_id as number)
                  : undefined
              }
              className={`border-b border-zinc-900 ${
                onSelect && row.docking_id !== undefined
                  ? "cursor-pointer hover:bg-zinc-900/60"
                  : ""
              }`}
            >
              {hasRanks && <td className="py-2 pr-4 font-mono">{i + 1}</td>}
              <td className="max-w-[12rem] truncate py-2 pr-4 font-mono text-xs">
                {row.canonical_smiles}
              </td>
              <td className="py-2 pr-4">{row.name ?? "—"}</td>
              <td className="py-2 pr-4 font-mono">
                {row.similarity !== undefined ? row.similarity.toFixed(4) : "—"}
              </td>
              <td className="py-2 pr-4 font-mono">{row.properties.qed.toFixed(3)}</td>
              <td className="py-2 pr-4 font-mono">{row.properties.sa_score.toFixed(2)}</td>
              <td className="py-2 pr-4 font-mono">
                {row.properties.lipinski.molecular_weight.toFixed(1)}
              </td>
              <td className="py-2 pr-4 font-mono">{row.properties.lipinski.logp.toFixed(2)}</td>
              {hasRanks && (
                <td className="py-2 pr-4 font-mono">
                  {row.affinity !== null && row.affinity !== undefined
                    ? row.affinity.toFixed(2)
                    : "—"}
                </td>
              )}
              {hasRanks && (
                <td className="py-2 pr-4 font-mono text-emerald-300">
                  {row.rank_score !== null && row.rank_score !== undefined
                    ? row.rank_score.toFixed(3)
                    : "—"}
                </td>
              )}
              <td className="py-2 pr-4">
                <Pass ok={row.properties.lipinski.passes} />
                <span className="ml-1 text-xs text-zinc-500">
                  {row.properties.lipinski.violations}
                </span>
              </td>
              <td className="py-2 pr-4">
                <Pass ok={row.properties.pains.passes} />
              </td>
              <td className="py-2">
                {row.citation ? (
                  <a
                    href={row.citation.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-400 hover:underline"
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
  );
}
