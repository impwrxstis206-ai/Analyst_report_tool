"""EDINET API v2 helper: search and download official disclosure filings
(有価証券報告書・四半期報告書・臨時報告書・大量保有報告書 など).

Note: EDINET covers statutory filings mandated by the FIEA. It does NOT
include TDnet-only disclosures such as 決算短信 (quick earnings summaries)
or 中期経営計画 (mid-term management plans). Those have no official public
API and must be searched for on the web separately.

Usage:
    python edinet_lookup.py search "トヨタ自動車" --days 30
    python edinet_lookup.py search 7203 --days 30
    python edinet_lookup.py fetch S100ABCD
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

# Force UTF-8 output regardless of the console's active code page (Windows
# terminals often default to cp932, which cannot encode some characters and
# otherwise garbles Japanese text).
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

API_BASE = "https://api.edinet-fsa.go.jp/api/v2"

# Common docTypeCode -> label. Unknown codes fall back to a generic label
# rather than failing, since EDINET's code list is larger than this subset.
DOC_TYPE_LABELS = {
    "120": "有価証券報告書",
    "130": "訂正有価証券報告書",
    "140": "四半期報告書",
    "150": "訂正四半期報告書",
    "160": "半期報告書",
    "170": "訂正半期報告書",
    "180": "臨時報告書",
    "190": "訂正臨時報告書",
    "350": "大量保有報告書",
    "360": "訂正大量保有報告書",
}

DEFAULT_DOC_TYPES = ["120", "130", "140", "150", "160", "170", "180", "190", "350", "360"]


def _get_api_key() -> str:
    key = os.environ.get("EDINET_API_KEY")
    if not key:
        print(
            "EDINET_API_KEY が設定されていません。\n"
            "https://disclosure2.edinet-fsa.go.jp/ で無料登録し、発行されたAPIキーを\n"
            "環境変数 EDINET_API_KEY に設定してください。",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _request_json(path: str, params: dict) -> dict:
    url = f"{API_BASE}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search(query: str, days: int, doc_types: list[str]) -> None:
    api_key = _get_api_key()
    today = date.today()
    matched = []

    for offset in range(days):
        target_date = today - timedelta(days=offset)
        data = _request_json(
            "/documents.json",
            {
                "date": target_date.isoformat(),
                "type": "2",
                "Subscription-Key": api_key,
            },
        )
        for item in data.get("results", []):
            if item.get("docTypeCode") not in doc_types:
                continue
            filer = item.get("filerName") or ""
            sec_code = item.get("secCode") or ""
            if query not in filer and query not in sec_code:
                continue
            matched.append(item)

    if not matched:
        print(f"該当する開示書類が見つかりませんでした(検索語: {query}, 期間: 過去{days}日間)。")
        print("EDINETは決算短信・中期経営計画など取引所(TDnet)独自の開示は対象外です。")
        return

    for item in matched:
        label = DOC_TYPE_LABELS.get(item.get("docTypeCode"), f"その他(コード:{item.get('docTypeCode')})")
        print(f"docID: {item.get('docID')}")
        print(f"  種別: {label}")
        print(f"  提出者: {item.get('filerName')} (証券コード: {item.get('secCode')})")
        print(f"  提出日時: {item.get('submitDateTime')}")
        print(f"  概要: {item.get('docDescription')}")
        print()


def fetch(doc_id: str, out_dir: str) -> None:
    api_key = _get_api_key()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{doc_id}.pdf")

    url = (
        f"{API_BASE}/documents/{doc_id}?"
        + urllib.parse.urlencode({"type": "2", "Subscription-Key": api_key})
    )
    with urllib.request.urlopen(url, timeout=60) as resp:
        content = resp.read()

    with open(out_path, "wb") as f:
        f.write(content)

    print(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="企業名または証券コードで開示書類を検索")
    search_parser.add_argument("query", help="企業名の一部、または4桁の証券コード")
    search_parser.add_argument("--days", type=int, default=30, help="遡って検索する日数(デフォルト30日)")
    search_parser.add_argument(
        "--doc-types",
        nargs="*",
        default=DEFAULT_DOC_TYPES,
        help="対象とする書類種別コード(デフォルトは主要な報告書一式)",
    )

    fetch_parser = subparsers.add_parser("fetch", help="docIDを指定してPDFをダウンロード")
    fetch_parser.add_argument("doc_id", help="EDINETの書類管理番号(例: S100ABCD)")
    fetch_parser.add_argument(
        "--out-dir",
        default=os.path.join(os.path.dirname(__file__), "edinet_cache"),
        help="保存先ディレクトリ",
    )

    args = parser.parse_args()

    if args.command == "search":
        search(args.query, args.days, args.doc_types)
    elif args.command == "fetch":
        fetch(args.doc_id, args.out_dir)


if __name__ == "__main__":
    main()
