"""Property Agent gate thresholds — named, disclosed, applied before docking.

Docking is the first expensive step (hours of CPU per candidate), so the
Property Agent gates candidates here. Every threshold is a named constant;
the property_filter node records the exact reason each candidate is
rejected. These are heuristic cutoffs, not validated predictions.
"""

PROPERTY_GATE_QED_MIN = 0.25
PROPERTY_GATE_SA_MAX = 6.0
PROPERTY_GATE_LIPINSKI_VIOLATIONS_MAX = 1
PROPERTY_GATE_PAINS_FREE = True
