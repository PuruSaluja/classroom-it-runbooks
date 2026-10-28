"""Write the illustrative inventory/rooms.csv.

The rooms are made up, so this script is where they come from, and running it again
writes the same file byte for byte. What it decides, and what was written by hand:

- **By hand, in PLANS below:** each building's floors, how many rooms each floor has,
  and how likely each room type is on that floor. A floor's rooms are numbered from
  ``<floor>01`` up.
- **Drawn with a fixed seed:** each room's type (by those weights), its seats (any
  whole number in the type's range in profiles.toml, equally likely), and how it
  differs from its type: with probability ``P_EXTRA`` one item from the type's
  ``EXTRAS``, and with probability ``P_WITHOUT`` one of its ``WITHOUT``.
- **One rule:** an active learning room with more than 60 seats gets two more team
  tables (a display and a set of table inputs each).

    python scripts/make_inventory.py [--out inventory/rooms.csv]
"""

from __future__ import annotations

import argparse
import csv
import io
import random
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261028
P_EXTRA = 0.2
P_WITHOUT = 0.1

GENERAL = {"standard": 6, "seminar": 2, "hybrid": 2}
SCIENCE = {"standard": 4, "computer-lab": 3, "seminar": 1}
BUSINESS = {"standard": 3, "hybrid": 3, "seminar": 2}
LIBRARY = {"seminar": 5, "hybrid": 2, "active-learning": 1}
ENGINEERING = {"computer-lab": 4, "standard": 3, "active-learning": 1}
ACTIVE = {"active-learning": 3, "hybrid": 2, "seminar": 2}
LECTURE = {"lecture-hall": 1}

# Each building's floors: (floor, rooms on it, room-type weights).
PLANS = {
    "ALD": [(f, 7, GENERAL) for f in (1, 2, 3, 4)],
    "BIR": [(1, 3, LECTURE)] + [(f, 6, SCIENCE) for f in (2, 3, 4)],
    "CED": [(f, 8, GENERAL) for f in (1, 2, 3)],
    "ELM": [(f, 5, BUSINESS) for f in (1, 2, 3, 4, 5)],
    "HAW": [(1, 2, LECTURE)] + [(f, 7, GENERAL) for f in (2, 3)],
    "LAU": [(f, 6, LIBRARY) for f in (2, 3, 4)],
    "MAP": [(1, 4, LECTURE), (2, 4, LECTURE)],
    "OAK": [(f, 6, ENGINEERING) for f in (1, 2, 3, 4)],
    "PIN": [(f, 8, ACTIVE) for f in (1, 2, 3)],
    "WIL": [(f, 8, GENERAL) for f in (1, 2, 3, 4)],
}

EXTRAS = {
    "seminar": ["webcam", "wall-port*2"],
    "standard": ["wireless-presentation", "assistive-listening", "webcam",
                 "wireless-mic-lapel", "wireless-presenter", "wall-port*2"],
    "hybrid": ["assistive-listening", "wireless-presentation", "wireless-mic-lapel"],
    "lecture-hall": ["ceiling-mic-array", "wireless-mic-handheld*2"],
    "active-learning": ["document-camera", "webcam"],
    "computer-lab": ["document-camera", "wireless-presentation", "projection-screen"],
}  # fmt: skip
WITHOUT = {
    "seminar": ["wireless-presentation"],
    "standard": ["document-camera", "usb-hub"],
    "hybrid": ["document-camera"],
    "lecture-hall": ["confidence-monitor"],
    "active-learning": ["interactive-display"],
    "computer-lab": ["wifi-ap"],
}


def rooms(seats: dict[str, tuple[int, int]], seed: int = SEED) -> list[list[str]]:
    """Every room's row, building by building in PLANS' order."""
    rng = random.Random(seed)
    rows = []
    for building, floors in PLANS.items():
        for floor, count, weights in floors:
            types = list(weights)
            for n in range(1, count + 1):
                profile = rng.choices(types, weights=[weights[t] for t in types])[0]
                low, high = seats[profile]
                room_seats = rng.randint(low, high)
                extra = [rng.choice(EXTRAS[profile])] if rng.random() < P_EXTRA else []
                without = [rng.choice(WITHOUT[profile])] if rng.random() < P_WITHOUT else []
                if profile == "active-learning" and room_seats > 60:
                    extra += ["flat-panel-display*2", "table-inputs*2"]
                rows.append([building, f"{floor}{n:02d}", profile, str(room_seats),
                             " ".join(extra), " ".join(without)])  # fmt: skip
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the illustrative rooms.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "inventory" / "rooms.csv")
    args = parser.parse_args(argv)
    profiles = tomllib.loads((ROOT / "inventory" / "profiles.toml").read_text(encoding="utf-8"))
    seats = {p["id"]: tuple(p["seats"]) for p in profiles["profile"]}
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["building", "number", "profile", "seats", "extra", "without"])
    writer.writerows(rooms(seats))
    args.out.write_bytes(out.getvalue().encode("utf-8"))
    print(f"{args.out}: {out.getvalue().count(chr(10)) - 1} rooms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
