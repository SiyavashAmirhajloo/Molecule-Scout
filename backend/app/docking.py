"""V6 docking seam: ligand prep (RDKit + Meeko) + Vina subprocess dock + rank.

Receptor prep (PDB -> PDBQT via Meeko ``mk_prepare_receptor``) was verified
on 1M17 during the step-0 spike: ``--default_altloc A`` is REQUIRED
(altloc residues A:751/A:831 hard-fail prep without it), and ``-p -v``
flags are required with ``-o`` or nothing is written. Ligand PDBQT via
Meeko ``mk_prepare_ligand`` (no MGLTools/OpenBabel system installs).
Vina runs as the upstream ``vina``/``vina.exe`` binary (v1.2.7 release
asset provisioned by ``scripts/fetch_vina.py`` — the pip ``vina`` package
has no Windows wheels and its sdist build fails, so it is not a dependency).
"""

import logging
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

FORMULA = "rank_score = 0.5 * norm_affinity + 0.3 * QED + 0.2 * novelty"
FORMULA_VERSION = "v6-1"
BOX_SIZE = (20.0, 20.0, 20.0)

# Vina grabs every core by default, which starves the Celery worker running it.
# ponytail: fixed at 2 to match compose --concurrency=2; make it configurable
# if worker concurrency ever changes.
VINA_CPU = 2
VINA_TIMEOUT_S = 600

# Trust boundary: pdb_id becomes a cache filename and an RCSB URL.
PDB_ID_RE = re.compile(r"[0-9][A-Za-z0-9]{3}")

# A co-crystal ligand has to look like a ligand. A lone sulfate or a zinc ion
# would give a confident dock against a meaningless pocket.
MIN_LIGAND_HEAVY_ATOMS = 6
EXCLUDED_RESNAMES = frozenset(
    # crystallization additives / buffers
    {"SO4", "PO4", "GOL", "EDO", "PEG", "PGE", "DMS", "ACT", "NO3", "FMT", "TRS"}
    # ions
    | {"CL", "NA", "K", "MG", "CA", "ZN", "MN", "FE", "CU", "NI", "CO", "CD", "HG",
       "BR", "I", "SO3", "PO3"}
    # modified residues (recorded as HETATM; MSE has 9 heavy atoms and passes
    # the count check, so exclusion has to be explicit)
    | {"MSE", "SEP", "TPO", "PTR", "KCX", "CME", "LLP"}
)

# Batch caps: docking is hours of CPU per candidate, so an unbounded request is
# a denial-of-service on our own worker.
MAX_CANDIDATES_PER_REQUEST = 50
MAX_LIGAND_HEAVY_ATOMS = 100

RECEPTOR_CACHE = Path(
    os.environ.get(
        "RECEPTOR_CACHE_DIR",
        str(Path(__file__).resolve().parent.parent / "models" / "receptors"),
    )
)
def _default_vina_bin() -> Path:
    """Vina is a subprocess binary, not a pip package.

    ``VINA_BIN`` wins when set (Docker/CI). Otherwise take whichever
    ``vina_*`` release asset ``scripts/fetch_vina.py`` installed, so we don't
    duplicate its platform mapping here and drift from it.
    """
    override = os.environ.get("VINA_BIN")
    if override:
        return Path(override)
    bin_dir = Path(__file__).resolve().parent.parent / "bin"
    for candidate in sorted(bin_dir.glob("vina_*")):
        if candidate.is_file() and not candidate.name.endswith(".tmp"):
            return candidate
    return bin_dir / "vina"


log = logging.getLogger(__name__)


class UnknownPDBError(ValueError):
    """Well-formed PDB ID that RCSB does not have (404)."""


class ReceptorFetchError(RuntimeError):
    """RCSB unreachable / network failure — upstream problem, not user input."""


def _validate_pdb_id(pdb_id: str) -> str:
    pdb_id = (pdb_id or "").strip().upper()
    if not PDB_ID_RE.fullmatch(pdb_id):
        raise ValueError(
            f"invalid PDB ID {pdb_id!r} — expected 4 characters, e.g. 1M17"
        )
    return pdb_id


def _fetch_pdb(pdb_id: str, dest: Path) -> str:
    """Download pdb_id to dest atomically. Raises UnknownPDBError / ReceptorFetchError."""
    import urllib.error
    import urllib.request

    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    # API and worker can both populate the cache; write to a temp file in the
    # same directory and rename, so a concurrent reader never sees a partial PDB.
    tmp = dest.with_suffix(f".{os.getpid()}.tmp")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        tmp.unlink(missing_ok=True)
        if e.code == 404:
            raise UnknownPDBError(f"unknown PDB ID {pdb_id}") from e
        raise ReceptorFetchError(f"RCSB returned HTTP {e.code} for {pdb_id}") from e
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        tmp.unlink(missing_ok=True)
        raise ReceptorFetchError(f"could not reach RCSB for {pdb_id}: {e}") from e
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return dest.read_text()


def _residue_heavy_atoms(pdb_text: str, resname: str) -> int:
    return sum(
        1
        for line in pdb_text.splitlines()
        if line.startswith("HETATM")
        and line[17:20].strip() == resname
        and line[76:78].strip() not in ("H", "D")
    )


def ligand_centroid(pdb_text: str, resname: str) -> tuple[float, float, float] | None:
    xs, ys, zs = [], [], []
    for line in pdb_text.splitlines():
        if line.startswith("HETATM") and line[17:20].strip() == resname:
            try:
                xs.append(float(line[30:38]))
                ys.append(float(line[38:46]))
                zs.append(float(line[46:54]))
            except ValueError:
                continue
    if not xs:
        return None
    return (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))


def find_cocrystal_ligand(pdb_text: str) -> tuple[str, tuple[float, float, float]] | None:
    """Largest credible co-crystal ligand + its centroid, else None (caller 422s).

    "Largest" rather than "first" because multi-ligand structures make the first
    HETATM arbitrary; excluded residues (sulfate, glycerol, ions, modified
    residues like MSE) are skipped so a crystallization artifact can never
    become a confident docking box.
    """
    resnames = {
        line[17:20].strip()
        for line in pdb_text.splitlines()
        if line.startswith("HETATM")
    }
    candidates = []
    for resname in resnames:
        if not resname or resname == "HOH" or resname in EXCLUDED_RESNAMES:
            continue
        if _residue_heavy_atoms(pdb_text, resname) < MIN_LIGAND_HEAVY_ATOMS:
            continue
        center = ligand_centroid(pdb_text, resname)
        if center is not None:
            candidates.append((_residue_heavy_atoms(pdb_text, resname), resname, center))
    if not candidates:
        return None
    _, resname, center = max(candidates)
    return resname, center


def inspect_receptor(pdb_id: str) -> tuple[Path, tuple[float, float, float]]:
    """Validate, fetch (cached), and locate the pocket. No prep — worker does that.

    Raises ValueError for a malformed ID or a structure with no credible
    co-crystal ligand, UnknownPDBError for a 404, ReceptorFetchError when RCSB
    is unreachable. The API layer maps these to 422 / 422 / 502.
    """
    pdb_id = _validate_pdb_id(pdb_id)
    RECEPTOR_CACHE.mkdir(parents=True, exist_ok=True)
    pdb_path = RECEPTOR_CACHE / f"{pdb_id}.pdb"
    pdb_text = pdb_path.read_text() if pdb_path.exists() else _fetch_pdb(pdb_id, pdb_path)
    hit = find_cocrystal_ligand(pdb_text)
    if hit is None:
        raise ValueError(
            f"no co-crystal ligand found for {pdb_id}; cannot define binding "
            "pocket — docking refused rather than guessing"
        )
    return pdb_path, hit[1]


def prepare_receptor(pdb_id: str, center: tuple[float, float, float]) -> Path:
    """Meeko PDB -> PDBQT (cached). Returns the receptor PDBQT path."""
    pdb_id = _validate_pdb_id(pdb_id)
    pdbqt_path = RECEPTOR_CACHE / f"{pdb_id}.pdbqt"
    if pdbqt_path.exists():
        return pdbqt_path
    pdb_path = RECEPTOR_CACHE / f"{pdb_id}.pdb"
    prot_lines = [
        ln for ln in pdb_path.read_text().splitlines() if ln.startswith("ATOM")
    ]
    prot_file = RECEPTOR_CACHE / f"{pdb_id}_protein.pdb"
    prot_file.write_text("\n".join(prot_lines) + "\n")
    cmd = [
        *_meeko_bin("mk_prepare_receptor"),
        "--read_pdb", str(prot_file),
        "-o", str(RECEPTOR_CACHE / pdb_id),
        "-p", "-v",
        "--box_center", *[str(c) for c in center],
        "--box_size", *[str(s) for s in BOX_SIZE],
        "--default_altloc", "A",
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as e:
        raise ValueError(f"receptor prep failed for {pdb_id}: {e}") from e
    if not pdbqt_path.exists():
        raise ValueError(f"receptor prep failed for {pdb_id}: no PDBQT written")
    return pdbqt_path


def prep_ligand(smiles: str) -> str | None:
    """SMILES -> PDBQT string via RDKit ETKDG + Meeko. None if unpreppable.

    Returns None (never raises) for anything Vina can't take: oversized,
    unparseable, unembeddable, or multi-fragment after stripping. Callers
    exclude these and keep going — one bad molecule must not fail a batch.
    """
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    from rdkit import Chem
    from rdkit.Chem import rdDistGeom

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    # Salts ("Cl.Na") and dotted diffusion output are multi-fragment, which
    # Meeko rejects outright. Keep the largest fragment — the parent drug.
    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=True)
    if len(frags) > 1:
        mol = max(frags, key=lambda m: m.GetNumHeavyAtoms())
    if mol.GetNumHeavyAtoms() > MAX_LIGAND_HEAVY_ATOMS:
        log.warning(
            "ligand has %d heavy atoms (> %d), excluded",
            mol.GetNumHeavyAtoms(),
            MAX_LIGAND_HEAVY_ATOMS,
        )
        return None
    try:
        mol = Chem.AddHs(mol)
        if rdDistGeom.EmbedMolecule(mol, rdDistGeom.ETKDGv3()) != 0:
            return None
        setups = MoleculePreparation().prepare(mol)
        if not setups:
            return None
        # Meeko splits preparation from writing: the setup object has no
        # write method, PDBQTWriterLegacy does.
        pdbqt, ok, err = PDBQTWriterLegacy.write_string(setups[0])
        if not ok:
            log.warning("meeko pdbqt write failed: %s", err)
            return None
        return pdbqt
    except Exception as e:
        log.warning("ligand prep raised: %s", e)
        return None


def parse_affinity(pdbqt_text: str) -> float | None:
    """First Vina result affinity, or None. Parsing this wrong silently
    corrupts every rank score, so it is a tested unit of its own."""
    for line in pdbqt_text.splitlines():
        if line.startswith("REMARK VINA RESULT:"):
            try:
                return float(line.split()[3])
            except (IndexError, ValueError):
                return None
    return None


def _meeko_bin(name: str) -> list[str]:
    """Resolve a Meeko console script.

    Returns a command list ready to pass to ``subprocess.run``. When the
    script has a ``.py`` extension (common in pip/Docker installs), it is
    invoked via ``python <path>`` since bare ``.py`` files can't be
    exec'd directly on every platform. Returns ``[name]`` as a fallback
    to let subprocess surface the real error.
    """
    import shutil

    for variant in (name, name + ".py"):
        found = shutil.which(variant)
        if found:
            return [sys.executable, found] if found.endswith(".py") else [found]
    for base in (
        Path(sys.executable).parent,
        Path.home() / ".local" / "bin",
        Path("/usr/local/bin"),
    ):
        for variant in (name, name + ".py"):
            cand = base / variant
            if cand.is_file():
                if cand.suffix == ".py":
                    return [sys.executable, str(cand)]
                return [str(cand)]
    return [name]


def _run_subprocess(cmd: list[str]) -> tuple[int, str, str]:
    """(returncode, stdout, stderr). Never raises — dock() decides what a
    failure means."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=VINA_TIMEOUT_S, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, "", "vina failed to run or timed out"
    return proc.returncode, proc.stdout, proc.stderr


VinaRunner = Callable[[list[str]], tuple[int, str, str]]


def dock(
    ligand_pdbqt: str,
    receptor_pdbqt: Path | str,
    center: tuple[float, float, float],
    size: tuple[float, float, float] = BOX_SIZE,
    exhaustiveness: int = 8,
    runner: VinaRunner = _run_subprocess,
) -> tuple[float | None, str | None]:
    """Run Vina. Returns (affinity, pose PDBQT) or (None, None) on any failure."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        lig = Path(tmp) / "lig.pdbqt"
        out = Path(tmp) / "out.pdbqt"
        lig.write_text(ligand_pdbqt)
        cmd = [
            str(_default_vina_bin()),
            "--receptor", str(receptor_pdbqt),
            "--ligand", str(lig),
            "--center_x", str(center[0]),
            "--center_y", str(center[1]),
            "--center_z", str(center[2]),
            "--size_x", str(size[0]),
            "--size_y", str(size[1]),
            "--size_z", str(size[2]),
            "--exhaustiveness", str(exhaustiveness),
            "--cpu", str(VINA_CPU),
            "--num_modes", "1",
            "--out", str(out),
        ]
        returncode, _, stderr = runner(cmd)
        if returncode != 0:
            log.warning("vina exited %d: %s", returncode, stderr.strip()[:200])
            return None, None
        if not out.exists():
            log.warning("vina exited 0 but wrote no output file")
            return None, None
        pose = out.read_text()
        return parse_affinity(pose), pose


def rank_batch(
    scored: list[dict],
) -> list[dict]:
    """Attach norm_affinity + rank_score in place. Failed (None affinity) sort last, unranked.

    scored items: {smiles, affinity|None, qed, novelty}. All-equal affinities
    -> norm 1.0 for all (avoids 0/0).
    """
    affs = [s["affinity"] for s in scored if s["affinity"] is not None]
    lo = min(affs) if affs else 0.0
    hi = max(affs) if affs else 0.0
    span = (hi - lo) or 1.0
    for s in scored:
        if s["affinity"] is None:
            s["norm_affinity"] = None
            s["rank_score"] = None
        else:
            # No spread to normalize over: equally-bounding candidates are all
            # "best" (1.0); 0.0 would report them as the worst binders.
            norm = 1.0 if hi == lo else (hi - s["affinity"]) / span
            s["norm_affinity"] = round(norm, 4)
            s["rank_score"] = round(0.5 * norm + 0.3 * s["qed"] + 0.2 * s["novelty"], 4)
        s["formula"] = FORMULA
        s["formula_version"] = FORMULA_VERSION
    scored.sort(
        key=lambda s: (s["rank_score"] is None, -(s["rank_score"] or 0.0))
    )
    return scored
