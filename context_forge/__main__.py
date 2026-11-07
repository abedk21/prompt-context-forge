"""CLI for compiling a safely partitioned prompt and a budget report."""
import argparse
import json
from pathlib import Path
from .engine import budget_frontier, compile_context
from .report import render


def main() -> None:
    p = argparse.ArgumentParser(description="Offline prompt context compiler")
    p.add_argument("command", choices=["demo"])
    p.add_argument("--scenario", type=Path, default=Path(__file__).resolve().parents[1] / "fixtures" / "scenario.json")
    p.add_argument("--out", type=Path, default=Path("examples/forge_report.html"))
    p.add_argument("--prompt-out", type=Path, default=Path("examples/compiled_prompt.txt"))
    a = p.parse_args()
    cfg = json.loads(a.scenario.read_text(encoding="utf-8"))
    result = compile_context(cfg)
    frontier = budget_frontier(cfg, [160, 240, 330, 500])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(render(result, frontier), encoding="utf-8")
    a.prompt_out.parent.mkdir(parents=True, exist_ok=True)
    a.prompt_out.write_text(result["prompt"], encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "prompt"}, indent=2))


if __name__ == "__main__":
    main()
