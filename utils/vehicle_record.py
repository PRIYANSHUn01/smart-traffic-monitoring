# utils/vehicle_record.py — The canonical data structure for one tracked vehicle
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VehicleRecord:
    """
    Holds all data for one detected vehicle in a single frame.
    Populated progressively as the frame passes through each module.
    """

    # ── Set by VehicleDetector (Day 8) ────────────────────────────────────
    vehicle_type: str  = 'motorcycle'
    cls_id:       int  = 3
    conf:         float = 0.0
    box:          List[int] = field(default_factory=lambda: [0,0,0,0])
    cx:           int  = 0
    cy:           int  = 0

    # ── Set by ByteTrack (Day 9) ──────────────────────────────────────────
    track_id:     Optional[int] = None
    counted:      bool = False

    # ── Set by RiderCounter (Day 15) ──────────────────────────────────────
    rider_count:  int  = 1
    rider_label:  str  = 'Solo'

    # ── Set by HelmetDetector (Day 12) ────────────────────────────────────
    helmet_status: str   = 'unknown'
    helmet_conf:   float = 0.0

    # ── Set by PlateReader (Day 21) ───────────────────────────────────────
    plate:         str  = 'UNKNOWN'
    plate_stable:  bool = False

    # ── Set by violation checker (Day 25) ────────────────────────────────
    violations:   List[str] = field(default_factory=list)

    def to_dict(self):
        """Convert to plain dict for CSV logging and JSON serialisation."""
        import dataclasses
        return dataclasses.asdict(self)

    def has_violation(self):
        return len(self.violations) > 0