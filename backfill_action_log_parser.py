"""
Backfill Action_Log parser fields (safe by default: dry-run).

What this script can fix
- AI_Analysis_JSON for categories: 운동/음주/회복 (default)
  using the current quick-parser logic in app.py.
- Optional: Action_Time correction from explicit time text in User_Input.
  (Only when a clear HH:MM-like token exists.)

Usage
    python3 backfill_action_log_parser.py --dry-run
    python3 backfill_action_log_parser.py --apply --from-date 2026-02-01
    python3 backfill_action_log_parser.py --apply --fix-action-time
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials

try:
    import tomllib  # py3.11+

    _TOML = "tomllib"
except Exception:
    tomllib = None
    _TOML = ""

if tomllib is None:
    try:
        import toml  # py<=3.10 fallback

        _TOML = "toml"
    except Exception:
        toml = None


DEFAULT_SPREADSHEET_NAME = "Projekt_MBJS_DB"
DEFAULT_WORKSHEET_NAME = "Action_Log"
DEFAULT_CATEGORIES = ["운동", "음주", "회복"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill Action_Log parsing errors.")
    p.add_argument("--spreadsheet-name", default=DEFAULT_SPREADSHEET_NAME)
    p.add_argument("--worksheet-name", default=DEFAULT_WORKSHEET_NAME)
    p.add_argument("--secrets-path", default="", help="Optional path to secrets.toml")
    p.add_argument("--from-date", default="", help="YYYY-MM-DD (inclusive)")
    p.add_argument("--to-date", default="", help="YYYY-MM-DD (inclusive)")
    p.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="Comma-separated categories to reparse. default: 운동,음주,회복",
    )
    p.add_argument("--fix-action-time", action="store_true", help="Try to correct Action_Time from User_Input text")
    p.add_argument("--limit", type=int, default=0, help="Max rows to inspect (0=all)")
    p.add_argument("--dry-run", action="store_true", help="Preview changes only")
    p.add_argument("--apply", action="store_true", help="Apply changes to sheet")
    return p.parse_args()


def load_secrets(explicit_path: str = "") -> Dict[str, Any]:
    candidates: List[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    candidates.extend(
        [
            Path(".streamlit/secrets.toml"),
            Path(__file__).parent / ".streamlit/secrets.toml",
            Path.home() / ".streamlit/secrets.toml",
        ]
    )

    for c in candidates:
        if not c.exists():
            continue
        if _TOML == "tomllib":
            with open(c, "rb") as f:
                data = tomllib.load(f)
        elif _TOML == "toml":
            with open(c, "r", encoding="utf-8") as f:
                data = toml.load(f)
        else:
            raise RuntimeError("No TOML parser available. Install toml package or use Python 3.11+.")
        print(f"secrets loaded: {c}")
        return data
    raise FileNotFoundError("secrets.toml not found")


def connect_worksheet(spreadsheet_name: str, worksheet_name: str, sa_info: Dict[str, Any]):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open(spreadsheet_name)
    return sh.worksheet(worksheet_name)


def normalize_date_key(v: str) -> str:
    s = str(v or "").strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    try:
        d = dt.datetime.fromisoformat(s)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return ""


def in_date_range(date_key: str, from_key: str, to_key: str) -> bool:
    if not date_key:
        return False
    if from_key and date_key < from_key:
        return False
    if to_key and date_key > to_key:
        return False
    return True


def try_parse_json(s: str) -> Dict[str, Any]:
    t = str(s or "").strip()
    if not t:
        return {}
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        m = re.search(r"\{[\s\S]*\}", t)
        if m:
            try:
                obj = json.loads(m.group(0))
                return obj if isinstance(obj, dict) else {}
            except Exception:
                return {}
        return {}


def _sum_float(pattern: str, txt: str) -> float:
    vals = re.findall(pattern, txt, flags=re.IGNORECASE)
    if not vals:
        return 0.0
    total = 0.0
    for v in vals:
        try:
            if isinstance(v, tuple):
                v = v[0]
            total += float(v)
        except Exception:
            continue
    return total


def _extract_ml_for_keyword(txt: str, keyword: str) -> float:
    patterns = [
        rf"{keyword}[^0-9]{{0,10}}(\d+(?:\.\d+)?)\s*(?:ml|밀리|미리|cc)",
        rf"(\d+(?:\.\d+)?)\s*(?:ml|밀리|미리|cc)[^가-힣]{{0,4}}{keyword}",
    ]
    return sum(_sum_float(p, txt) for p in patterns)


def _extract_total_minutes(txt: str) -> int:
    mins = 0.0
    mins += _sum_float(r"(\d+(?:\.\d+)?)\s*(?:시간|hr|hour|hours|h)", txt) * 60.0
    mins += _sum_float(r"(\d+(?:\.\d+)?)\s*(?:분|min|minute|minutes|m)", txt)
    return int(round(mins))


def parse_log_quick_subset(category: str, user_text: str) -> Optional[Dict[str, Any]]:
    txt = str(user_text or "").strip()
    cat = str(category or "")
    if not txt:
        return None

    if "운동" in cat:
        mins = _extract_total_minutes(txt)
        if mins <= 0:
            km_m = re.search(r"(\d{1,2}(?:\.\d+)?)\s*km", txt, flags=re.IGNORECASE)
            if km_m:
                mins = int(max(10, round(float(km_m.group(1)) * 7)))
        if mins <= 0:
            mins = 20
        return {
            "activity_type": "exercise",
            "duration": int(mins),
            "time": int(mins),
            "summary": f"운동 기록 ({int(mins)}분)",
        }

    if "회복" in cat:
        mins = _extract_total_minutes(txt)
        cyc_m = re.search(r"(\d{1,2})\s*(세트|사이클)", txt, flags=re.IGNORECASE)
        cycles = int(cyc_m.group(1)) if cyc_m else 0
        if mins <= 0 and cycles > 0:
            mins = cycles * 20
        return {
            "activity_type": "recovery",
            "cycles": int(cycles),
            "duration": int(mins),
            "summary": f"회복 기록 ({int(mins)}분)" if mins > 0 else "회복 기록",
        }

    if "음주" in cat:
        soju_bottle = _sum_float(r"소주\s*(\d+(?:\.\d+)?)\s*병", txt)
        soju_glass = _sum_float(r"소주\s*(\d+(?:\.\d+)?)\s*잔", txt)
        beer_can = _sum_float(r"맥주\s*(\d+(?:\.\d+)?)\s*(?:캔|병)", txt)
        beer_glass = _sum_float(r"맥주\s*(\d+(?:\.\d+)?)\s*잔", txt)
        wine_bottle = _sum_float(r"와인\s*(\d+(?:\.\d+)?)\s*병", txt)
        wine_glass = _sum_float(r"와인\s*(\d+(?:\.\d+)?)\s*잔", txt)

        soju_ml = _extract_ml_for_keyword(txt, "소주")
        beer_ml = _extract_ml_for_keyword(txt, "맥주")
        wine_ml = _extract_ml_for_keyword(txt, "와인")

        drinks_f = 0.0
        drinks_f += soju_bottle * 7.0 + soju_glass
        drinks_f += beer_can * 1.5 + beer_glass
        drinks_f += wine_bottle * 5.0 + wine_glass
        drinks_f += (soju_ml / 51.4) + (beer_ml / 236.7) + (wine_ml / 150.0)
        drinks_f = max(0.0, drinks_f)

        drinks = int(round(drinks_f))
        if drinks == 0 and drinks_f > 0:
            drinks = 1
        calories = int(round(drinks_f * 100))

        alcohol_type = "기타"
        bucket_soju = soju_bottle * 360 + soju_glass * 50 + soju_ml
        bucket_beer = beer_can * 355 + beer_glass * 300 + beer_ml
        bucket_wine = wine_bottle * 750 + wine_glass * 150 + wine_ml
        mx = max(bucket_soju, bucket_beer, bucket_wine)
        if mx > 0:
            if mx == bucket_soju:
                alcohol_type = "소주"
            elif mx == bucket_beer:
                alcohol_type = "맥주"
            else:
                alcohol_type = "와인"

        return {
            "alcohol_type": alcohol_type,
            "standard_drinks": int(drinks),
            "calories": int(calories),
            "summary": f"음주 기록 ({int(drinks)}잔, 약 {int(calories)}kcal)",
        }

    return None


def canonical_json_str(obj: Dict[str, Any]) -> str:
    return json.dumps(obj or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def format_json_for_cell(obj: Dict[str, Any]) -> str:
    return json.dumps(obj or {}, ensure_ascii=False)


def parse_time_from_user_input(user_text: str) -> Optional[str]:
    txt = str(user_text or "")
    # 18:25, 9:05, 09시25분
    m = re.search(r"\b([01]?\d|2[0-3])\s*[:시]\s*([0-5]?\d)\b", txt)
    if not m:
        return None
    h = int(m.group(1))
    mm = int(m.group(2))
    return f"{h:02d}:{mm:02d}"


def valid_hhmm(v: str) -> bool:
    s = str(v or "").strip()
    return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", s))


def col_to_a1(n: int) -> str:
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def main() -> int:
    args = parse_args()
    if not args.dry_run and not args.apply:
        print("No mode selected. Defaulting to --dry-run.")
        args.dry_run = True
    if args.apply:
        args.dry_run = False

    secrets = load_secrets(args.secrets_path)
    sa = dict(secrets.get("gcp_service_account") or {})
    if not sa:
        raise ValueError("[gcp_service_account] missing in secrets.toml")
    sa["private_key"] = str(sa.get("private_key", "")).replace("\\n", "\n")

    ws = connect_worksheet(args.spreadsheet_name, args.worksheet_name, sa)
    values = ws.get_all_values()
    if not values:
        print("No rows found.")
        return 0

    hdr = values[0]
    idx = {name: i for i, name in enumerate(hdr)}
    required = ["Date", "Action_Time", "Category", "User_Input", "AI_Analysis_JSON"]
    missing = [c for c in required if c not in idx]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    from_key = normalize_date_key(args.from_date) if args.from_date else ""
    to_key = normalize_date_key(args.to_date) if args.to_date else ""
    cat_tokens = [x.strip() for x in str(args.categories or "").split(",") if x.strip()]
    if not cat_tokens:
        cat_tokens = DEFAULT_CATEGORIES[:]

    updates: List[Dict[str, Any]] = []
    inspected = 0
    changed_json = 0
    changed_time = 0

    for r_idx_1_based, row in enumerate(values[1:], start=2):
        if args.limit and inspected >= args.limit:
            break

        date_key = normalize_date_key(row[idx["Date"]] if idx["Date"] < len(row) else "")
        if not in_date_range(date_key, from_key, to_key):
            continue

        category = row[idx["Category"]] if idx["Category"] < len(row) else ""
        if not any(t in str(category) for t in cat_tokens):
            continue

        user_text = row[idx["User_Input"]] if idx["User_Input"] < len(row) else ""
        parsed = parse_log_quick_subset(category, user_text)
        if parsed is None:
            continue
        inspected += 1

        old_json_str = row[idx["AI_Analysis_JSON"]] if idx["AI_Analysis_JSON"] < len(row) else ""
        old_json = try_parse_json(old_json_str)

        if canonical_json_str(old_json) != canonical_json_str(parsed):
            col = idx["AI_Analysis_JSON"] + 1
            rng = f"{col_to_a1(col)}{r_idx_1_based}"
            new_text = format_json_for_cell(parsed)
            updates.append({"range": rng, "values": [[new_text]]})
            changed_json += 1
            print(f"[JSON] row {r_idx_1_based}: {category} / {user_text[:40]}")
            print(f"  old: {old_json_str[:140]}")
            print(f"  new: {new_text[:140]}")

        if args.fix_action_time:
            old_t = row[idx["Action_Time"]] if idx["Action_Time"] < len(row) else ""
            new_t = parse_time_from_user_input(user_text)
            if new_t and (not valid_hhmm(old_t) or old_t != new_t):
                col_t = idx["Action_Time"] + 1
                rng_t = f"{col_to_a1(col_t)}{r_idx_1_based}"
                updates.append({"range": rng_t, "values": [[new_t]]})
                changed_time += 1
                print(f"[TIME] row {r_idx_1_based}: {old_t} -> {new_t}")

    print("-" * 56)
    print(f"inspected: {inspected}")
    print(f"json changes: {changed_json}")
    print(f"time changes: {changed_time}")
    print(f"total cell updates: {len(updates)}")

    if args.dry_run:
        print("dry-run mode: no changes applied.")
        return 0

    if not updates:
        print("Nothing to update.")
        return 0

    ws.batch_update(updates, value_input_option="RAW")
    print("Applied updates successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
