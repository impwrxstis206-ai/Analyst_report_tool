"""Agent 1: Researcher — broadly collects raw market information from the web."""

from datetime import date

from config import CATEGORIES, EFFORT, MODEL, get_client

SYSTEM_PROMPT = """\
あなたは「調査役エージェント」です。ファンドの意思決定に使うため、相場に関する情報をインターネットから
まんべんなく収集するのがあなたの仕事です。

対象カテゴリ:
{categories}

方針:
- 各カテゴリについて、直近の値動き・ニュース・イベントを幅広く調べてください。一つの情報源に偏らず、
  複数の情報源を横断してください。
- 数字(価格・変化率・金利水準など)は可能な限り具体的に記載してください。
- 出典(メディア名やURLなど)と情報の日付を明記してください。
- この段階では「重要かどうかの取捨選択」はまだ行わないでください。後工程のアナリストが選別するため、
  広く・網羅的に集めることを優先してください。
- 出力はカテゴリごとの見出しを立てたMarkdown形式にしてください。
"""


def run_research() -> str:
    """Run Agent 1 (researcher) and return its raw findings as Markdown text."""
    client = get_client()

    system_prompt = SYSTEM_PROMPT.format(categories="\n".join(f"- {c}" for c in CATEGORIES))
    messages = [
        {
            "role": "user",
            "content": (
                f"本日({date.today().isoformat()})時点での相場・マクロ経済情報を、"
                "上記カテゴリ全てについて調査してください。"
            ),
        }
    ]

    tools = [
        {"type": "web_search_20260209", "name": "web_search"},
        {"type": "web_fetch_20260209", "name": "web_fetch"},
    ]

    final_text_parts: list[str] = []

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=system_prompt,
            tools=tools,
            output_config={"effort": EFFORT},
            messages=messages,
        )

        if response.stop_reason == "refusal":
            raise RuntimeError(
                "調査エージェントのリクエストが安全性ポリシーにより拒否されました。"
            )

        for block in response.content:
            if block.type == "text":
                final_text_parts.append(block.text)

        if response.stop_reason == "pause_turn":
            # Server-side tool loop hit its round limit — resume by resending
            # the conversation as-is (do NOT append an extra user message).
            messages = [
                messages[0],
                {"role": "assistant", "content": response.content},
            ]
            continue

        break

    return "\n\n".join(final_text_parts)


if __name__ == "__main__":
    print(run_research())
