"""Prompt construction and the deterministic template rationale.

The verification sentence is a hard requirement from docs/architecture.md's
Responsible Use section. It is in the prompt AND enforced in code afterwards —
the model is not trusted to include it.
"""

DISCLAIMER = (
    "Generated molecules are not validated drug candidates. This report is a "
    "triage aid for a human researcher and requires human/wet-lab verification "
    "before any claim about activity is made."
)
VERIFICATION_PHRASE = "requires human/wet-lab verification"

SYSTEM_PROMPT = """You are a computational chemistry triage assistant.

Write a short (3-5 sentence) plain-English rationale for ONE candidate molecule,
grounded ONLY in the structured facts provided. Rules:
- Do not invent activity data, targets, or literature claims.
- Explain what the docking affinity and composite rank score mean for this
  candidate relative to the rest of this batch.
- State what remains uncertain.
- You MUST end with a sentence stating that the result requires human/wet-lab
  verification and is a triage aid, not a final answer.
- Never describe the molecule as a drug candidate; it is a hypothesis.
"""


def candidate_facts(cand: dict, rank: int, total: int, conditioning: dict | None) -> str:
    """The structured, verifiable facts for one candidate — the only input."""
    affinity = cand.get("affinity")
    aff = f"{affinity:.2f} kcal/mol" if isinstance(affinity, (int, float)) else "not docked"
    parts = [
        f"Candidate {rank} of {total} (ranked by composite score).",
        f"SMILES: {cand.get('smiles')}",
        f"Docking affinity: {aff}.",
        (
            f"Composite rank score: {cand.get('rank_score')} "
            f"({cand.get('formula_version', 'v6-1')})."
        ),
        (
            f"QED: {cand.get('qed')}; novelty vs ChEMBL corpus: "
            f"{cand.get('novelty')} (1.0 = unlike any known drug)."
        ),
    ]
    cond = conditioning or {}
    if cond.get("mode") == "retrieval-conditioned":
        parts.append(
            "Generation was conditioned on retrieved analog "
            f"{cond.get('seed_smiles')} at similarity {cond.get('similarity')}."
        )
    elif cond.get("mode") == "fallback-unconditioned":
        parts.append(
            "No close literature analog was found; generation used property "
            f"targets only ({cond.get('reason')})."
        )
    return "\n".join(parts)


def template_rationale(cand: dict, rank: int, total: int, conditioning: dict | None) -> str:
    """Deterministic rationale from real numbers. Used when no LLM is configured
    and as the per-candidate fallback when an LLM call fails."""
    affinity = cand.get("affinity")
    novelty = cand.get("novelty")
    qed = cand.get("qed")
    score = cand.get("rank_score")
    bits = [f"Ranks {rank} of {total} in this batch (composite score {score})."]
    if isinstance(affinity, (int, float)):
        bits.append(
            f"Docking affinity {affinity:.2f} kcal/mol"
            + (" — among the stronger binders here." if rank <= max(1, total // 3) else ".")
        )
    if isinstance(qed, (int, float)):
        bits.append(f"Drug-likeness (QED) {qed:.3f}.")
    if isinstance(novelty, (int, float)):
        if novelty >= 0.8:
            bits.append(
                "Structurally far from any known ChEMBL drug (novelty "
                f"{novelty:.2f}); that raises both opportunity and risk."
            )
        else:
            bits.append(
                f"Structurally close to a known drug (novelty {novelty:.2f}), "
                "so its behavior is more predictable."
            )
    cond = conditioning or {}
    if cond.get("mode") == "fallback-unconditioned":
        bits.append("No close literature analog was found; generation used property targets only.")
    bits.append(
        "Uncertainty remains high: docking is a static estimate and no assay "
        "has been run. This result requires human/wet-lab verification and is a "
        "triage aid, not a final answer."
    )
    return " ".join(bits)
