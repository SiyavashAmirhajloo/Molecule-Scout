"""Trace emission: always to the run's trace list; optionally to Langfuse.

Langfuse is only initialised when both keys are present in the environment.
Without keys (CI, local dev) the structured trace in the run record is the
only sink — the prompt's "or structured logging" fallback. Langfuse
emission is unverified unless it has been run with real keys.
"""

import os


def emit_trace_to_langfuse(run_id: int, trace: list[dict]) -> bool:
    """Best-effort Langfuse emission. Returns True if emitted, False if skipped.

    Never raises — a tracing failure must not break a pipeline run.
    """
    if not (os.environ.get("LANGFUSE_SECRET_KEY") and os.environ.get("LANGFUSE_PUBLIC_KEY")):
        return False
    try:
        from langfuse import Langfuse

        lf = Langfuse()
        lf.trace(
            name=f"pipeline_run_{run_id}",
            metadata={"run_id": run_id, "events": trace},
        )
        lf.flush()
        return True
    except Exception:
        return False
