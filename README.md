# market-intel-agents

2体のAIエージェントが対話しながら相場レポートを作成するプロジェクトです。

- **調査役エージェント**: Web検索を使って、株式・為替・暗号資産・マクロ経済のニュースや値動きを幅広く収集します。
- **ファンドアナリストエージェント**: 調査役と対話しながら重要な情報を選別し、プレゼン形式を自分たちで決めた上で、あなた(ファンドマネージャー)向けの最終レポートを作成します。

実装方法は2通り用意しています。**通常はメイン方式(Claude Codeサブエージェント)を使ってください。**

## メイン方式: Claude Codeサブエージェント(推奨・追加課金なし)

Claude Code(Pro/Maxサブスク)にログインしていれば、追加のAPI課金なしで使えます。

### 一元管理の仕組み(ユーザーレベル登録)

サブエージェントと`/market-report`コマンドは、このプロジェクトフォルダではなく
**ユーザーレベル(`C:\Users\impwr\.claude\agents\` / `C:\Users\impwr\.claude\commands\`)** に登録して
あります。これにより、VS Codeでどのフォルダを開いていても(このプロジェクトを開いていなくても)
`/market-report` が使えます。今後別の調査エージェントを追加する場合も、同様にユーザーレベルに
置けば、フォルダを行き来する必要はありません。

ただし、サブエージェント実行時の作業フォルダは「その時Claude Codeで開いているフォルダ」になるため、
`.claude/agents/`内の指示ではこのプロジェクトのファイル(`edinet_lookup.py`、`reports/`)を
**すべてフルパス**(`C:\Users\impwr\Documents\market-intel-agents\...`)で参照するようにしてあります。

### 使い方

1. Claude Codeのチャットで `/market-report` と入力する(どのフォルダを開いていてもOK)
2. 調査役とアナリストが自動で対話し、最終レポートが
   `C:\Users\impwr\Documents\market-intel-agents\reports\` フォルダに保存される
3. 個別銘柄も調べたい場合は `/market-report トヨタ自動車` のように引数を付ける

構成ファイル(ユーザーレベル):

- `~/.claude/agents/market-researcher.md` — 調査役サブエージェントの定義(WebSearch/WebFetch/Bash/Readツール、`model: opus`指定)
- `~/.claude/agents/fund-analyst.md` — アナリストサブエージェントの定義(調査役の情報のみを根拠に判断、`model: opus`指定)
- `~/.claude/commands/market-report.md` — `/market-report` コマンドの本体。上記2つを呼び出し、3ラウンドの対話をさせ、レポートを保存する手順を定義

> 両サブエージェントは`model: opus`を指定しているため、メインの会話がSonnetでもOpusで動きます。Opusの方が精度は高いですが、Pro/Maxの利用枠の消費もSonnetより大きい点に注意してください。

### 出力ファイル

`C:\Users\impwr\Documents\market-intel-agents\reports\` フォルダに以下が保存されます。

- `YYYYMMDD_HHMMSS_dialogue.md` — 調査役とアナリストの対話ログ全文
- `YYYYMMDD_HHMMSS_report.md` — アナリストが最終的にまとめたレポート(これが読むべき成果物です)

### 個別銘柄の正式開示書類(EDINET連携)

`/market-report トヨタ自動車` のように引数を付けると、通常の4カテゴリに加えて、金融庁のEDINET API経由で
その銘柄の有価証券報告書・四半期報告書・臨時報告書・大量保有報告書も調べます(`edinet_lookup.py`)。

**セットアップ(無料)**

1. https://disclosure2.edinet-fsa.go.jp/ でユーザー登録(無料)
2. マイページからAPIキーを発行
3. 環境変数に設定

```bash
# Windows (PowerShell)
$env:EDINET_API_KEY = "発行されたキー"
```

**EDINETの限界(重要):** EDINETは金融商品取引法に基づく法定開示書類(有報・四半期報告書など)のみが対象です。
東証(TDnet)独自の「決算短信」「中期経営計画」は対象外で、公式APIも存在しません。これらは引き続き
WebSearch頼りになり、確実に拾える保証はありません。

---

## サブ方式: 単独Pythonスクリプト(API課金・自動化向け)

サブスクとは別にAnthropic APIの従量課金が必要です。その代わり、`python main.py` でいつでも自動実行でき、
将来的にスケジュール実行(毎日自動レポートなど)にも拡張しやすい構成です。

### セットアップ

```bash
pip install -r requirements.txt
```

APIキーを環境変数に設定してください(`ant auth login` でログイン済みなら不要です)。

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

### 実行方法

```bash
python main.py
```

こちらも同じく `reports/` フォルダに `dialogue.md` / `report.md` を保存します。

構成ファイル: `config.py` / `researcher.py` / `dialogue.py` / `main.py`

---

## 対象カテゴリ

デフォルトは以下の4分野です(両方式共通)。

- 株式(個別銘柄・主要指数)
- 為替(FX)
- 暗号資産
- マクロ経済全般

サブエージェント方式でカテゴリを変えたい場合は `~/.claude/agents/market-researcher.md` の本文を、
Pythonスクリプト方式の場合は `config.py` の `CATEGORIES` を編集してください。
