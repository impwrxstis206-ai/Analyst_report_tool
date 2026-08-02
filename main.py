"""Entry point: run the researcher agent, then the researcher/analyst dialogue,
and save the resulting report for the fund manager."""

import os
import sys
from datetime import datetime

from dialogue import run_dialogue
from researcher import run_research

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        print(
            "ANTHROPIC_API_KEY (または ANTHROPIC_AUTH_TOKEN) が設定されていません。\n"
            "環境変数を設定するか `ant auth login` を実行してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[1/2] 調査役エージェントが相場情報を収集しています…", file=sys.stderr)
    raw_findings = run_research()

    print("[2/2] 調査役とアナリストが対話しています…", file=sys.stderr)
    transcript, final_report = run_dialogue(raw_findings)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dialogue_path = os.path.join(REPORTS_DIR, f"{timestamp}_dialogue.md")
    report_path = os.path.join(REPORTS_DIR, f"{timestamp}_report.md")

    with open(dialogue_path, "w", encoding="utf-8") as f:
        f.write("# 調査役 × アナリスト 対話ログ\n\n")
        for turn in transcript:
            speaker = "調査役エージェント" if turn["speaker"] == "researcher" else "ファンドアナリストエージェント"
            f.write(f"## {speaker}\n\n{turn['text']}\n\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(f"\n対話ログ: {dialogue_path}")
    print(f"最終レポート: {report_path}\n")
    print("=" * 60)
    print(final_report)


if __name__ == "__main__":
    main()
