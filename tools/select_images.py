"""Resolve an explicitly requested build scope and its parent-image dependencies."""

import json
import sys
from pathlib import Path

IMAGES = Path(__file__).resolve().parent.parent / "images"


def select_images(requested: str) -> tuple[list[str], list[str]]:
    available = {p.parent.name for p in IMAGES.glob("*/Dockerfile")}
    selected = available if requested == "all" else {x.strip() for x in requested.split(",")}
    if not selected or not selected <= available:
        raise ValueError("unknown or empty base-image selection")
    selected = set(selected)
    for name in tuple(selected):
        if name.startswith("python-adk-"):
            selected.add(name.replace("python-adk-", "python-runtime-"))
    return (
        sorted(name for name in selected if not name.startswith("python-adk-")),
        sorted(name for name in selected if name.startswith("python-adk-")),
    )


if __name__ == "__main__":
    base, derived = select_images(sys.argv[1])
    print("base=" + json.dumps(base))
    print("derived=" + json.dumps(derived))
    print("has_derived=" + str(bool(derived)).lower())
