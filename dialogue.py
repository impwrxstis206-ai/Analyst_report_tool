"""Agent 2 + presentation: the Fund Analyst reviews Agent 1's raw findings, and
the two agents converse to decide on and produce the final presentation for
the fund manager (the user)."""

from config import EFFORT, MODEL, get_client

RESEARCHER_SYSTEM = """\
あなたは「調査役エージェント」です。すでにインターネットで相場・マクロ経済情報を幅広く収集し終えました。
これから「ファンドアナリストエージェント」と対話し、情報の背景や根拠を説明したり、追加の質問に答えたりします。

- 自分が集めた生の調査結果を根拠に、簡潔かつ具体的に答えてください。
- アナリストから重要度や解釈について聞かれたら、事実ベースで補足してください(重要度の最終判断はアナリスト側に委ねてください)。
- 発言は300〜500文字程度を目安に、要点を絞って話してください。
"""

ANALYST_SYSTEM = """\
あなたは「ファンドアナリストエージェント」です。調査役エージェントが集めた大量の生情報の中から、
ファンドマネージャー(人間)が本当に必要とする重要な情報だけを見極めるのがあなたの仕事です。

- ノイズ(重要度の低いニュースや重複情報)を切り捨て、投資判断に直結する情報を重視してください。
- 不明点や裏付けが弱い点は、調査役エージェントに質問して確認してください。
- 対話の終盤では、「ファンドマネージャーに提出するプレゼン形式」を自分たちで決めてください
  (例: Q&A形式、重要度ランキング形式、カテゴリ別サマリー形式など、内容に最も適した形式を選ぶこと)。
- 最終ターンでは、その形式に沿った完成レポートを、ファンドマネージャー宛てに日本語でMarkdown出力してください。
  レポートには根拠となる出典・数値を残しつつ、簡潔にまとめてください。
- 発言は300〜600文字程度を目安にしてください(最終ターンのレポートは除く)。
"""

Turn = dict[str, str]


def _format_transcript(transcript: list[Turn]) -> str:
    lines = []
    for turn in transcript:
        speaker = "調査役" if turn["speaker"] == "researcher" else "アナリスト"
        lines.append(f"【{speaker}】\n{turn['text']}")
    return "\n\n".join(lines)


def _call_persona(system_prompt: str, transcript: list[Turn], instruction: str) -> str:
    client = get_client()
    context = _format_transcript(transcript)
    user_content = f"{context}\n\n---\n{instruction}" if context else instruction

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=system_prompt,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": user_content}],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("エージェントの応答が安全性ポリシーにより拒否されました。")

    return "\n".join(block.text for block in response.content if block.type == "text")


def run_dialogue(raw_findings: str, rounds: int = 3) -> tuple[list[Turn], str]:
    """Run the researcher/analyst dialogue and return (transcript, final_report_markdown)."""
    transcript: list[Turn] = [{"speaker": "researcher", "text": raw_findings}]

    for round_index in range(1, rounds + 1):
        is_last = round_index == rounds

        analyst_instruction = (
            "上記の調査結果を精査し、重要な点への質問や、切り捨てて良いと思うノイズについて述べてください。"
            if round_index == 1
            else "調査役の回答を踏まえ、さらに深掘りするか、次の論点に移ってください。"
        )
        if is_last:
            analyst_instruction = (
                "これで議論は最後です。まずプレゼン形式をどう決めたか一言で述べたうえで、"
                "その形式に沿った完成レポートをファンドマネージャー宛てにMarkdownで出力してください。"
            )

        analyst_text = _call_persona(ANALYST_SYSTEM, transcript, analyst_instruction)
        transcript.append({"speaker": "analyst", "text": analyst_text})

        if is_last:
            break

        researcher_instruction = "アナリストからの質問・指摘に、事実に基づいて簡潔に回答してください。"
        researcher_text = _call_persona(RESEARCHER_SYSTEM, transcript, researcher_instruction)
        transcript.append({"speaker": "researcher", "text": researcher_text})

    final_report = transcript[-1]["text"]
    return transcript, final_report
