"""Export successful, explicitly labeled sample answers for the static Pages preview."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    report = json.loads((ROOT / "docs/evaluation-results.json").read_text())
    questions = ["How many vacation days do employees get?", "When do I need to submit my expense report?"]
    aliases = {}
    answers = {}
    for row in report["results"]:
        if row["question"] in questions and row["smoke_pass"] and row["mode"] == "generated":
            answer = {key: row[key] for key in ("answer", "sources", "mode", "elapsed_ms")}
            answer["sources"] = [{k: v for k, v in s.items() if k != "document_id"}
                                 for s in answer["sources"]]
            answers[aliases.get(row["question"], row["question"])] = answer
    if len(answers) != len(questions):
        raise SystemExit("Both prepared example questions must pass before exporting.")
    (ROOT / "frontend/demo.json").write_text(json.dumps({"prepared": True,
        "description": "Recorded CPU-model answers for a fictional sample; no live inference.",
        "answers": answers}, indent=2) + "\n", encoding="utf-8")
