from __future__ import annotations

import json
from pathlib import Path

from aimotionlabs.models import MotionSpecManifest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "spec" / "motionspec-v0.1.schema.json"
SCHEMA_ID = (
    "https://raw.githubusercontent.com/eyeinthesky6/AI-Motion-Labs/"
    "main/spec/motionspec-v0.1.schema.json"
)


def build_schema() -> dict:
    schema = MotionSpecManifest.model_json_schema()
    schema["$id"] = SCHEMA_ID
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema


def main() -> None:
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(
        json.dumps(build_schema(), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {SCHEMA_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
