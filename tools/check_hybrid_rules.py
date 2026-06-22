#!/usr/bin/env python3
"""Validate hybrid a11y detect/fix JSONL definitions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from a11y_agent.hybrid_rules import get_hybrid_rule_ids, load_hybrid_rules  # noqa: E402

EXPECTED_RULES = 16


def main() -> int:
    try:
        rules = load_hybrid_rules()
        ids = get_hybrid_rule_ids(rules)
        for idx, rule in enumerate(rules, start=1):
            contract = rule.get("出力契約", "")
            if isinstance(contract, str):
                json.loads(contract)
            else:
                json.dumps(contract, ensure_ascii=False)
        if len(rules) != EXPECTED_RULES:
            raise ValueError(f"expected {EXPECTED_RULES} rules, got {len(rules)}")
    except Exception as exc:
        print("status: FAIL")
        print(f"error: {exc}")
        return 1

    print("status: PASS")
    print(f"rules: {len(rules)}")
    print("ids:")
    for rid in ids:
        print(f"- {rid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
