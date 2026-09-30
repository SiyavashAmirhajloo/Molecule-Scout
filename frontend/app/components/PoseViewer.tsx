"use client";

import { useEffect, useRef, useState } from "react";

// Pinned version + SRI: a tampered or silently-updated CDN asset must not
// execute. Regenerate with:
//   curl -sL <CDN_SRC> | openssl dgst -sha384 -binary | openssl base64 -A
const CDN_SRC = "https://cdn.jsdelivr.net/npm/3dmol@2.4.0/build/3Dmol-min.js";
const SRI = "sha384-AXFomAwcJ1kYYBUXZ5nLoRIVNeVdonlsEdeL9ntPHPErY2wVCWgT3bQ1p8Oye0i2";

type Props = {
  posePdbqt: string;
  /** Receptor PDBQT, optional — docks are readable on the ligand alone. */
  receptorPdbqt?: string | null;
};

/**
 * Single-pose V6 viewer. 3Dmol loads from a pinned CDN build; if that fails we
 * say so in the interface rather than showing a blank box.
 */
export default function PoseViewer({ posePdbqt, receptorPdbqt }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cancelled = false;
    let viewer: MolViewer3D | null = null;

    ensureScript().then(($3Dmol) => {
      if (cancelled) return;
      if (!$3Dmol) {
        setLoadError(
          "3Dmol.js could not be loaded from the CDN — check your connection.",
        );
        return;
      }
      try {
        viewer = new $3Dmol.createViewer(host, {
          backgroundColor: "black",
          antialias: true,
        });
        if (receptorPdbqt) {
          // Style per model rather than by index, so adding the receptor first
          // never shifts which atoms the ligand style lands on.
          viewer.addModel(receptorPdbqt, "pdbqt").setStyle(
            {},
            { cartoon: { color: "white" } },
          );
        }
        viewer.addModel(posePdbqt, "pdbqt").setStyle(
          {},
          { stick: { colorscheme: "greenCarbon" } },
        );
        viewer.zoomTo();
        viewer.render();
      } catch (e) {
        setRenderError(e instanceof Error ? e.message : "Could not render pose");
      }
    });

    return () => {
      cancelled = true;
      try {
        viewer?.clear();
      } catch {
        // Best effort: old viewer just garbage-collects.
      }
    };
  }, [posePdbqt, receptorPdbqt]);

  if (loadError) {
    return (
      <p className="rounded bg-red-950 p-3 text-sm text-red-200">{loadError}</p>
    );
  }
  if (renderError) {
    return (
      <p className="rounded bg-red-950 p-3 text-sm text-red-200">
        Pose viewer error: {renderError}
      </p>
    );
  }

  return (
    <div className="grid gap-2">
      <div
        ref={hostRef}
        className="h-72 w-full rounded bg-black"
        style={{ minWidth: "16rem" }}
      />
      <p className="text-xs text-zinc-500">
        Ligand pose (sticks) {receptorPdbqt ? "+ protein (cartoon/surface)" : ""}
      </p>
    </div>
  );
}

type MolViewer3D = {
  addModel(data: string, format: string): { setStyle(sel: object, style: object): void };
  setStyle(sel: object, style: object): void;
  addSurface(type: number, opts: object): void;
  zoomTo(): void;
  render(): void;
  clear(): void;
  center(vec: { x: number; y: number; z: number }): void;
};

type MolGlobal = {
  createViewer: new (el: HTMLElement, opts: object) => MolViewer3D;
  SurfaceType: { VDW: number };
};

let scriptPromise: Promise<MolGlobal | null> | null = null;

/** Load 3Dmol once per page; the script tag is what the SRI hash verifies. */
function ensureScript(): Promise<MolGlobal | null> {
  if (typeof window === "undefined") return Promise.resolve(null);
  const existing = document.querySelector<HTMLScriptElement>(
    `script[data-3dmol]`,
  );
  if (existing) {
    return new Promise((resolve) => {
      if (typeof window.$3Dmol !== "undefined") resolve(window.$3Dmol);
      else existing.addEventListener("load", () => resolve(window.$3Dmol ?? null));
      existing.addEventListener("error", () => resolve(null));
    });
  }
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve) => {
      const s = document.createElement("script");
      s.src = CDN_SRC;
      s.integrity = SRI;
      s.crossOrigin = "anonymous";
      s.async = true;
      s.dataset.threedmol = "true";
      s.onload = () => resolve(window.$3Dmol ?? null);
      s.onerror = () => resolve(null);
      document.head.appendChild(s);
    });
  }
  return scriptPromise;
}

declare global {
  interface Window {
    $3Dmol?: MolGlobal;
  }
}
