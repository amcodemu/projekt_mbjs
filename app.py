import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import json
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re


st.set_page_config(page_title="Dr. MBJS", layout="wide", page_icon="🧬")

hide_streamlit_style = """
<style>
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    header {background-color: transparent !important;}
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1000px;
    }

    hr { margin-top: 1rem; margin-bottom: 1rem; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: transparent; border-bottom: none; padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #FFFFFF; border-radius: 25px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #E2E8F0;
        color: #64748B; font-weight: 700; font-size: 14px;
        flex-grow: 1; transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1A2B4D !important; color: #FFFFFF !important;
        border: none !important; box-shadow: 0 4px 6px -1px rgba(26,43,77,0.3) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: auto !important;
            flex: 1 1 auto !important;
            min-width: 0px !important;
        }
    }

    .strategy-box {
        background-color: #FFFFFF; padding: 15px; border-radius: 12px;
        color: #1E293B; font-size: 15px; line-height: 1.5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px;
    }
    .strategy-title {
        font-weight: 800; font-size: 16px; margin-bottom: 8px; display: block;
    }
    .workout-box { border: 2px solid #3B82F6; }
    .diet-box { border: 2px solid #10B981; }
    .recovery-box { border: 2px solid #F59E0B; }

    .time-badge {
        background-color: #1A2B4D; color: white; padding: 2px 10px;
        border-radius: 12px; font-size: 12px; font-weight: 600;
        vertical-align: middle; margin-left: 8px; display: inline-block;
        transform: translateY(-2px);
    }

    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stForm"] {
            padding-bottom: 60vh !important;
        }

        input[type="text"],
        input[type="date"],
        select {
            font-size: 16px !important;
        }

        input:focus,
        select:focus {
            scroll-margin-bottom: 50vh;
        }
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# [캐시 헬퍼 함수 - 원본 유지]
CACHE_DIR = "/tmp/mbjs_cache"

def save_checkin_cache(date_key, data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"checkin_{date_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_checkin_cache(date_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"checkin_{date_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except:
        return None


def save_dailyfive_cache(date_key, sprint_id, data):
    local_ok = False
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        local_ok = True
    except:
        local_ok = False

    sheet_ok = False
    try:
        sheet_ok = persist_dailyfive_to_sheet(date_key, sprint_id, data)
    except:
        sheet_ok = False

    return local_ok or sheet_ok

def save_trend_cache(date_key, data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"trend_{date_key}.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_trend_cache(date_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"trend_{date_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except:
        return None

def load_dailyfive_cache(date_key, sprint_id):
    try:
        cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass

    # /tmp 캐시에 없으면 시트에서 복원 시도
    try:
        from_sheet = load_dailyfive_from_sheet(date_key, sprint_id)
        if from_sheet:
            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(from_sheet, f, ensure_ascii=False, indent=2)
            except:
                pass
            return from_sheet
    except:
        pass

    return None

def save_xc_cache(date_key, sprint_id, data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"xc_{date_key}_{sprint_id}.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_xc_cache(date_key, sprint_id):
    try:
        cache_file = os.path.join(CACHE_DIR, f"xc_{date_key}_{sprint_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except:
        return None


def save_wrapup_cache(kind, cache_key, data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"{kind}_wrapup_{cache_key}.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def load_wrapup_cache(kind, cache_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"{kind}_wrapup_{cache_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except:
        return None


def invalidate_realtime_plan_cache(date_key):
    try:
        ai_generate_action_plan_cached.clear()
    except:
        pass
    try:
        for kind in ("daily", "weekly"):
            cache_file = os.path.join(CACHE_DIR, f"{kind}_wrapup_{date_key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
    except:
        pass



def clear_old_caches(keep_days=7):
    try:
        if not os.path.exists(CACHE_DIR):
            return
        now = get_current_kst()
        for filename in os.listdir(CACHE_DIR):
            # ✅ [FIX] startswith 사용 오류 수정
            if filename.startswith(("checkin_", "dailyfive_", "trend_", "xc_", "daily_wrapup_", "weekly_wrapup_")):
                filepath = os.path.join(CACHE_DIR, filename)
                file_dt = datetime.fromtimestamp(os.path.getmtime(filepath), tz=KST)
                if (now - file_dt).days > keep_days:
                    os.remove(filepath)
    except:
        pass

# [설정 및 상수 - 원본 유지]
if "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    OPENAI_API_KEY = ""

SHEET_NAME = "Projekt_MBJS_DB"
CALENDAR_IDS = {
    "Sports": "nc41q7u653f9na0nt55i2a8t14@group.calendar.google.com",
    "Termin": "u125ev7cv5du60n94crf4naqak@group.calendar.google.com"
}

KST = ZoneInfo("Asia/Seoul")
DEBUG_MODE = os.getenv("MBJS_DEBUG", "0") == "1"

LATE_MODE_START_HOUR = 20
LATE_MODE_START_MIN = 30  # 20:30 이후에는 장시간 운동 제안 금지를 위한 상수
DAY_WRAPUP_START_HOUR = 21
DAY_WRAPUP_START_MIN = 0  # 21:00 이후 신규 운동 제안 차단, 하루 마무리 모드
WRAPUP_SWITCH_HOUR = 23
DAY_RESET_HOUR = 5
DEFAULT_DAILY_KCAL_TARGET = 2000
XC_BASELINE_KG = 0.30
XC_MIN_KG = -0.20
XC_MAX_KG = 0.50

XC_ADJ = {
    "yesterday_no_workout": 0.10,
    "yesterday_kcal_mid_high": 0.07,
    "yesterday_kcal_very_high": 0.11,
    "yesterday_alcohol": 0.07,
    "streak_overeat_2d": 0.05,
    "streak_no_workout_2d": 0.06,
    "streak_alcohol_2d": 0.04,
    "sprint_behind": 0.07,
    "sprint_far_behind": 0.04,
    "sprint_ahead_relief": -0.05,
    "slot_evening_open_push": 0.12,
    "slot_lunch_open_push": 0.05,
    "slot_no_enabled_reality": -0.24,
    "slot_single_enabled_reality": -0.09,
    "bio_low_hrv": -0.06,
    "bio_very_low_hrv": -0.10,
    "bio_high_rhr": -0.06,
    "bio_very_high_rhr": -0.10,
    "bio_combined_risk": -0.05,
}

URGENCY_THRESHOLDS = {
    "high": 7,
    "medium": 4,
}


HUMANIZE_MAP = {
    # slot_id
    "lunch_micro": "점심 30분",
    "after_work_main": "퇴근 후 저녁(가능할 때)",
    "weekend_main": "주말 메인",

    # workout program codes
    "gym_quick_30": "헬스장 30분 퀵 세션(러닝+코어 중심)",
    "gym_full_120": "헬스장 2시간 풀 세션(유산소+근력)",
    "outdoor_run_60": "야외 러닝 60분(심폐 중심)",
    "walk_stairs": "걷기/계단 20분",
    "tennis_90": "테니스 90분",
}

NUTRITION_STOPWORDS = {
    "인분", "그릇", "공기", "마리", "캔", "병", "잔", "개", "세트", "조각", "컵",
    "섭취", "먹음", "먹었다", "먹었음", "먹기", "음식", "식사", "간식",
    "오늘", "점심", "저녁", "아침", "메뉴", "추가", "정도",
}

FOOD_ALIAS_MAP = {
    "후라이드치킨": "치킨",
    "치킨": "치킨",
    "라면": "라면",
    "떡국": "떡국",
    "비빔밥": "비빔밥",
    "쌀밥": "쌀밥",
    "밥": "밥",
    "콜라": "콜라",
    "햄버거": "햄버거",
    "피자": "피자",
    "김밥": "김밥",
}

BEVERAGE_TOKENS = {"콜라", "사이다", "주스", "음료"}

NUTRITION_FALLBACK_PROFILE = {
    # values are approximate per 1 serving unit
    "후라이드치킨": {"kcal": 1200.0, "protein": 72.0, "fat": 74.0, "carbs": 48.0},
    "치킨": {"kcal": 980.0, "protein": 64.0, "fat": 58.0, "carbs": 34.0},
    "콜라": {"kcal": 108.0, "protein": 0.0, "fat": 0.0, "carbs": 27.0},  # per 250ml
    "라면": {"kcal": 500.0, "protein": 10.0, "fat": 16.0, "carbs": 79.0},
    "쌀밥": {"kcal": 300.0, "protein": 5.7, "fat": 0.5, "carbs": 67.0},
    "비빔밥": {"kcal": 550.0, "protein": 19.0, "fat": 13.0, "carbs": 88.0},
    "떡국": {"kcal": 420.0, "protein": 14.0, "fat": 5.0, "carbs": 81.0},
}

PERSONA_SECRET_KEY = "COACH_PERSONA_CONTEXT"

COMMON_COACH_PERSONA_FALLBACK = """
[COMMON PERSONA]
- Coach identity: professional fitness and nutrition coach.
- Coaching style: warm but firm, action-focused.
- Language: Korean honorific style only.

[SAFETY]
- Do not diagnose disease.
- If severe warning signs are present, advise immediate medical evaluation.
""".strip()

NORTH_STAR_OBJECTIVE = (
    "This app exists to produce measurable behavior change every day, "
    "not just analysis or display."
)


def build_common_persona_context():
    try:
        txt = str(st.secrets.get(PERSONA_SECRET_KEY, "") or "").strip()
        if txt:
            return txt
        gcp_block = st.secrets.get("gcp_service_account", {}) or {}
        txt2 = str(gcp_block.get(PERSONA_SECRET_KEY, "") or "").strip()
        if txt2:
            return txt2
    except Exception:
        pass
    return COMMON_COACH_PERSONA_FALLBACK


def build_north_star_context():
    return f"""
[NORTH STAR]
- {NORTH_STAR_OBJECTIVE}
- Every section must end in concrete execution, not observation only.
- If uncertainty exists, still provide one best next action with clear time anchoring.
""".strip()



# ==========================================
# 백엔드 함수
# ==========================================

import re

def humanize_action_text(text: str) -> str:
    if not text:
        return text
    out = text

    # 따옴표로 감싼 경우/그냥 나온 경우 모두 커버
    for k, v in HUMANIZE_MAP.items():
        out = out.replace(f"'{k}'", v)
        out = out.replace(f"\"{k}\"", v)
        out = out.replace(k, v)

    # 모델이 토큰을 변형해서 내보내는 경우까지 커버
    loose_map = {
        "gym quick 30": "헬스장 30분 퀵 세션(러닝+코어 중심)",
        "gym full 120": "헬스장 2시간 풀 세션(유산소+근력)",
        "outdoor run 60": "야외 러닝 60분(심폐 중심)",
        "walk stairs": "걷기/계단 20분",
        "after work main": "퇴근 후 저녁(가능할 때)",
        "lunch micro": "점심 30분",
    }
    lowered = out.lower()
    for k, v in loose_map.items():
        if k in lowered:
            out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
            lowered = out.lower()

    # 혹시 남는 snake_case 토큰이 있으면 보기 좋게
    out = re.sub(r"\b([a-z]+_[a-z0-9_]+)\b", lambda m: m.group(1).replace("_", " "), out)
    out = out.replace("  ", " ").strip()
    return out


def build_dailyfive_status_text(date_key, sprint_id, df_action):
    daily_five = load_dailyfive_cache(date_key, sprint_id)
    if not daily_five or 'tasks' not in daily_five:
        return "Daily Five: None"

    today_logs = df_action[df_action['Date'] == date_key] if 'Date' in df_action.columns else df_action
    marks = collect_dailyfive_completion_marks(today_logs)
    done_rows = build_dailyfive_done_rows(daily_five.get("tasks", []), marks)
    done_map = {int(d.get("index", 0)): bool(d.get("done")) for d in done_rows}

    lines = ["[DAILY FIVE CHECKLIST]"]
    for idx, t in enumerate(daily_five['tasks'], start=1):
        title = str(t.get('title', '')).strip()
        done = bool(done_map.get(idx, False))

        mark = "✅" if done else "⬜"
        lines.append(f"{mark} ({t.get('task_id','')}) {title}")

    lines.append("Rule: Mark ✅ when Action_Log contains DF category with DF1~DF5 or legacy DF5 markers")
    return "\n".join(lines)


def collect_dailyfive_completion_marks(today_logs):
    marks = {
        "df_numbers": set(),
        "task_ids": set(),
        "inputs_compact": "",
        "inputs_upper": "",
    }
    if today_logs is None or today_logs.empty:
        return marks

    inputs = " ".join([str(x) for x in today_logs.get("User_Input", []).tolist()])
    marks["inputs_upper"] = inputs.upper()
    marks["inputs_compact"] = re.sub(r"\s+", "", marks["inputs_upper"])

    for _, r in today_logs.iterrows():
        cat = str(r.get("Category", "") or "").upper().strip()
        text = str(r.get("User_Input", "") or "")
        text_up = text.upper()
        text_compact = re.sub(r"\s+", "", text_up)

        # 신규 규칙: 카테고리=DF + DF1~DF5
        if cat == "DF":
            for m in re.finditer(r"(?<![A-Z0-9])DF\s*([1-5])(?!\d)", text_up):
                marks["df_numbers"].add(int(m.group(1)))

        # 레거시 호환: DF5:TASK_1 / DF5:TASK1
        for m in re.finditer(r"DF5:TASK[_-]?([1-5])(?!\d)", text_compact):
            marks["task_ids"].add(f"TASK_{int(m.group(1))}")

    return marks


def is_dailyfive_task_done(index, tid, title, marks):
    idx = int(index)
    tid_up = str(tid or "").upper().strip()
    title_up = str(title or "").upper().strip()
    inputs_up = str((marks or {}).get("inputs_upper", "") or "")
    inputs_compact = str((marks or {}).get("inputs_compact", "") or "")
    df_numbers = set((marks or {}).get("df_numbers", set()) or set())
    task_ids = set((marks or {}).get("task_ids", set()) or set())

    if idx in df_numbers:
        return True

    if tid_up and tid_up in task_ids:
        return True

    if tid_up and f"DF5:{tid_up}" in inputs_compact:
        return True

    if title_up and ("DF5:" in inputs_up):
        compact_title = re.sub(r"\s+", "", title_up)
        if len(compact_title) >= 6 and compact_title in inputs_compact:
            return True
    return False


def build_dailyfive_done_rows(tasks, marks):
    rows = []
    df_numbers = set((marks or {}).get("df_numbers", set()) or set())
    task_ids = set((marks or {}).get("task_ids", set()) or set())

    for idx, t in enumerate((tasks or []), start=1):
        tid = str(t.get("task_id", "")).upper().strip()
        title = str(t.get("title", "")).strip()
        title_up = title.upper()
        done = is_dailyfive_task_done(idx, tid, title_up, marks)

        evidence = ""
        if idx in df_numbers:
            evidence = f"DF{idx}"
        elif tid and tid in task_ids:
            evidence = f"DF5:{tid}"
        elif title and ("DF5:" in str((marks or {}).get("inputs_upper", "") or "")):
            evidence = "DF5:title_match"

        rows.append({
            "index": idx,
            "task_id": tid,
            "title": title,
            "done": bool(done),
            "evidence": evidence,
        })
    return rows


def get_daily_five_completion(date_key, sprint_id, df_action):
    daily_five = load_dailyfive_cache(date_key, sprint_id)
    if not daily_five or "tasks" not in daily_five:
        return {
            "has_plan": False,
            "completed": 0,
            "total": 0,
            "completion_rate": 0.0,
        }

    tasks = daily_five.get("tasks", []) or []
    total = len(tasks)
    if total == 0:
        return {
            "has_plan": True,
            "completed": 0,
            "total": 0,
            "completion_rate": 0.0,
        }

    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return {
            "has_plan": True,
            "completed": 0,
            "total": total,
            "completion_rate": 0.0,
        }

    today_logs = df_action[df_action["Date"] == date_key] if "Date" in df_action.columns else df_action
    marks = collect_dailyfive_completion_marks(today_logs)
    done_rows = build_dailyfive_done_rows(tasks, marks)
    completed = sum(1 for d in done_rows if d.get("done"))
    completion_rate = float(completed / total) if total > 0 else 0.0

    try:
        sync_dailyfive_completion_to_sheet(date_key, sprint_id, done_rows)
    except:
        pass
    try:
        sync_daily_sprint_progress_completion(
            date_key=date_key,
            sprint_id=sprint_id,
            completed=completed,
            total=total,
            completion_rate=completion_rate,
        )
    except:
        pass

    return {
        "has_plan": True,
        "completed": int(completed),
        "total": int(total),
        "completion_rate": completion_rate,
    }


def get_current_kst():
    # 앱 전체에서 KST aware datetime만 사용
    return datetime.now(KST)


def get_dashboard_subpage():
    try:
        q = st.experimental_get_query_params()
        return str((q.get("dash", [""])[0]) or "").strip().lower()
    except:
        return ""


def set_dashboard_subpage(page_name=""):
    try:
        if page_name:
            st.experimental_set_query_params(dash=str(page_name))
        else:
            st.experimental_set_query_params()
    except:
        pass


def normalize_context_for_cache(context_str):
    import re
    normalized = re.sub(r'\(\d{2}:\d{2}\)', '(TIME)', context_str)
    normalized = re.sub(r'- \d{2}:\d{2}', '- TIME', normalized)
    return normalized

def get_mission_date_key():
    now_kst = get_current_kst()
    if now_kst.hour < DAY_RESET_HOUR:
        return (now_kst - timedelta(days=1)).strftime('%Y-%m-%d')
    return now_kst.strftime('%Y-%m-%d')


def is_wrapup_window(now_kst=None):
    now_kst = now_kst or get_current_kst()
    t = now_kst.time()
    return (t >= time(WRAPUP_SWITCH_HOUR, 0)) or (t < time(DAY_RESET_HOUR, 0))


def resolve_wrapup_kind(date_key, now_kst=None):
    if not is_wrapup_window(now_kst):
        return None
    try:
        dt = datetime.strptime(date_key, "%Y-%m-%d")
    except:
        return "daily"
    # 일요일 밤(및 월요일 05:00 이전 동일 date_key)에는 weekly wrapup 우선
    return "weekly" if dt.weekday() == 6 else "daily"


def get_daily_kcal_target():
    try:
        mission = get_active_mission()
        if mission and mission.get("daily_calories"):
            return int(mission.get("daily_calories"))
    except:
        pass
    try:
        v = st.secrets.get("DAILY_KCAL_TARGET", None)
        if v is not None:
            return int(v)
    except:
        pass
    return int(DEFAULT_DAILY_KCAL_TARGET)

@st.cache_resource
def get_db_connection(worksheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    if "gcp_service_account" in st.secrets:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    return gspread.authorize(creds).open(SHEET_NAME).worksheet(worksheet_name)

@st.cache_data(ttl=900)
def fetch_sheet_data(worksheet_name):
    try:
        sheet = get_db_connection(worksheet_name)
        return sheet.get_all_records()
    except Exception as e:
        print(f"⚠️ API Error ({worksheet_name}): {e}")
        return []

def parse_korean_datetime(dt_str):
    try:
        dt_str = str(dt_str).replace('.', '').strip()
        parts = dt_str.split()
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        ampm = parts[3]
        time_parts = parts[4].split(':')
        hour, minute = int(time_parts[0]), int(time_parts[1])

        if ampm == "오후" and hour != 12:
            hour += 12
        if ampm == "오전" and hour == 12:
            hour = 0
        return datetime(year, month, day, hour, minute)
    except:
        return None

@st.cache_data(ttl=3600)
def get_active_mission():
    try:
        records = fetch_sheet_data("Missions")
        if not records:
            return None

        for row in records:
            if row['Status'] == '진행중':
                return {
                    'mission_id': row['Mission_ID'], 'name': row['Name'],
                    'start_date': datetime.strptime(row['Start_Date'], '%Y-%m-%d').replace(tzinfo=KST),
                    'end_date': datetime.strptime(row['End_Date'], '%Y-%m-%d').replace(tzinfo=KST),
                    'start_weight': float(row['Start_Wt']), 'target_weight': float(row['Target_Wt']),
                    'daily_calories': int(row['Daily_Cal'])
                }
        return None
    except:
        return None

@st.cache_data(ttl=3600)
def get_mission_rules(mission_id):
    try:
        records = fetch_sheet_data("Mission_Rules")
        rules = {}
        if not records:
            return rules

        for row in records:
            if row['Mission_ID'] == mission_id:
                try:
                    rules[row['Rule_Type']] = json.loads(row['Rule_Value'])
                except:
                    rules[row['Rule_Type']] = row['Rule_Value']
        return rules
    except:
        return {}

SPRINT_DAILY_TASKS_DEFAULT_HEADERS = [
    "Date", "Sprint_ID", "Task_ID", "Category", "Priority",
    "Title", "Description", "Why", "Urgency_Level", "Daily_Message", "Today_Training_Mode",
    "Completed", "Completed_At", "Completion_Source", "Completion_Evidence", "Created_At",
]

DAILY_SPRINT_PROGRESS_DEFAULT_HEADERS = [
    "Date", "Sprint_ID", "Completed", "Total", "Completion_Rate",
    "XC_Value_KG", "Urgency_Level", "Pace_Status", "Weight_Current",
    "Trend_Weight",
    "Start_Weight_KG", "Prev_Start_Weight_KG", "Prev_XC_KG",
    "Actual_Change_KG", "XC_Gap_KG", "XC_Achievement_PCT",
    "Summary_JSON", "Updated_At",
]


def _safe_int(v, default=0):
    try:
        return int(float(v))
    except:
        return default


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


def _to_boolish(v):
    s = str(v).strip().lower()
    return s in {"1", "true", "t", "y", "yes", "done", "완료"}


def _safe_date_key(v):
    try:
        return datetime.strptime(str(v).strip(), "%Y-%m-%d").date()
    except:
        return None


def get_start_weight_kg_for_date(date_key):
    """
    해당 날짜의 아침 체중(Health_Log의 당일 첫 기록)을 우선 사용.
    당일 값이 없으면 date_key 이전 최근 기록으로 fallback.
    """
    try:
        records = fetch_sheet_data("Health_Log")
        if not records:
            return None
        df = pd.DataFrame(records)
        if df.empty or ("Date" not in df.columns) or ("Weight" not in df.columns):
            return None

        df["Date_Clean"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df["Weight_num"] = pd.to_numeric(df["Weight"], errors="coerce")
        df = df.dropna(subset=["Date_Clean", "Weight_num"])
        if df.empty:
            return None

        day_df = df[df["Date_Clean"] == str(date_key)]
        if not day_df.empty:
            return float(day_df.iloc[0]["Weight_num"])

        df = df[df["Date_Clean"] <= str(date_key)]
        if not df.empty:
            return float(df.iloc[-1]["Weight_num"])
        return None
    except Exception as e:
        print("start weight load error:", e)
        return None


def _get_prev_progress_row(rows, sprint_id, date_key):
    current_d = _safe_date_key(date_key)
    if current_d is None:
        return None
    sprint_id_str = str(sprint_id)
    picked = None
    picked_d = None
    for r in (rows or []):
        if str(r.get("Sprint_ID", "")).strip() != sprint_id_str:
            continue
        rd = _safe_date_key(r.get("Date", ""))
        if rd is None or rd >= current_d:
            continue
        if (picked_d is None) or (rd > picked_d):
            picked = r
            picked_d = rd
    return picked


def get_prev_xc_feedback(sprint_id, date_key):
    """
    전일(정확히는 date_key 이전 최근일)의 XC_Gap_KG를 반환.
    양수면 전일 xC 미달.
    """
    try:
        rows = fetch_sheet_data("Daily_Sprint_Progress")
        prev = _get_prev_progress_row(rows, sprint_id, date_key)
        if not prev:
            return {"date": None, "gap_kg": None}
        gap = _safe_float(prev.get("XC_Gap_KG"), None)
        if gap is None:
            prev_xc = _safe_float(prev.get("Prev_XC_KG"), None)
            actual = _safe_float(prev.get("Actual_Change_KG"), None)
            if (prev_xc is not None) and (actual is not None):
                gap = float(prev_xc) - float(actual)
        return {
            "date": str(prev.get("Date", "")).strip() or None,
            "gap_kg": (round(float(gap), 3) if gap is not None else None),
        }
    except Exception as e:
        print("prev xc feedback load error:", e)
        return {"date": None, "gap_kg": None}


def _get_or_init_headers(sheet, default_headers):
    try:
        headers = [str(x).strip() for x in (sheet.row_values(1) or [])]
        if not headers:
            sheet.update("A1", [default_headers], value_input_option="RAW")
            return list(default_headers)

        changed = False
        for h in default_headers:
            if h not in headers:
                headers.append(h)
                changed = True
        if changed:
            sheet.update("A1", [headers], value_input_option="RAW")
        return headers
    except:
        return list(default_headers)


def _a1_col(idx):
    out = ""
    n = int(idx)
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def _append_rows_by_headers(sheet, headers, row_dicts):
    rows = []
    for d in row_dicts:
        rows.append([d.get(h, "") for h in headers])
    if rows:
        sheet.append_rows(rows, value_input_option="RAW")


def load_dailyfive_from_sheet(date_key, sprint_id):
    try:
        records = fetch_sheet_data("Sprint_Daily_Tasks")
        sprint_id_str = str(sprint_id)
        rows = [
            r for r in (records or [])
            if str(r.get("Date", "")).strip() == str(date_key)
            and str(r.get("Sprint_ID", "")).strip() == sprint_id_str
        ]
        if not rows:
            return None

        rows = sorted(rows, key=lambda x: _safe_int(x.get("Priority", 999), 999))
        tasks = []
        for r in rows:
            tasks.append({
                "task_id": str(r.get("Task_ID", "")).strip() or f"task_{len(tasks)+1}",
                "category": str(r.get("Category", "")).strip() or "diet",
                "priority": _safe_int(r.get("Priority", len(tasks)+1), len(tasks)+1),
                "title": str(r.get("Title", "")).strip(),
                "description": str(r.get("Description", "")).strip(),
                "why": str(r.get("Why", "")).strip(),
                "completed": _to_boolish(r.get("Completed", "")),
            })

        daily_message = ""
        urgency_level = "medium"
        today_training_mode = ""
        for r in rows:
            if not daily_message and str(r.get("Daily_Message", "")).strip():
                daily_message = str(r.get("Daily_Message", "")).strip()
            if str(r.get("Urgency_Level", "")).strip():
                urgency_level = str(r.get("Urgency_Level", "")).strip()
            if not today_training_mode and str(r.get("Today_Training_Mode", "")).strip():
                today_training_mode = str(r.get("Today_Training_Mode", "")).strip().lower()

        return {
            "tasks": tasks,
            "daily_message": daily_message,
            "urgency_level": urgency_level,
            "today_training_mode": today_training_mode,
        }
    except Exception as e:
        print("load dailyfive sheet error:", e)
        return None


def persist_dailyfive_to_sheet(date_key, sprint_id, daily_five):
    try:
        if not daily_five or "tasks" not in daily_five:
            return False

        sheet = get_db_connection("Sprint_Daily_Tasks")
        headers = _get_or_init_headers(sheet, SPRINT_DAILY_TASKS_DEFAULT_HEADERS)

        # 이미 해당 일자/스프린트 데이터가 있으면 중복 저장하지 않음
        existing = fetch_sheet_data("Sprint_Daily_Tasks")
        sprint_id_str = str(sprint_id)
        if any(
            str(r.get("Date", "")).strip() == str(date_key)
            and str(r.get("Sprint_ID", "")).strip() == sprint_id_str
            for r in (existing or [])
        ):
            return True

        created_at = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
        urgency = str(daily_five.get("urgency_level", "") or "")
        msg = str(daily_five.get("daily_message", "") or "")
        mode = str(daily_five.get("today_training_mode", "") or "").strip().lower()
        rows = []
        for i, task in enumerate((daily_five.get("tasks", []) or []), start=1):
            rows.append({
                "Date": str(date_key),
                "Sprint_ID": sprint_id_str,
                "Task_ID": str(task.get("task_id", "")).strip() or f"task_{i}",
                "Category": str(task.get("category", "")).strip(),
                "Priority": _safe_int(task.get("priority", i), i),
                "Title": str(task.get("title", "")).strip(),
                "Description": str(task.get("description", "")).strip(),
                "Why": str(task.get("why", "")).strip(),
                "Urgency_Level": urgency,
                "Daily_Message": msg,
                "Today_Training_Mode": mode,
                "Completed": "0",
                "Completed_At": "",
                "Completion_Source": "",
                "Completion_Evidence": "",
                "Created_At": created_at,
            })

        if not rows:
            rows.append({
                "Date": str(date_key),
                "Sprint_ID": sprint_id_str,
                "Task_ID": "",
                "Category": "",
                "Priority": "",
                "Title": "",
                "Description": "",
                "Why": "",
                "Urgency_Level": urgency,
                "Daily_Message": msg,
                "Today_Training_Mode": mode,
                "Completed": "0",
                "Completed_At": "",
                "Completion_Source": "",
                "Completion_Evidence": "",
                "Created_At": created_at,
            })

        _append_rows_by_headers(sheet, headers, rows)
        try:
            fetch_sheet_data.clear()
        except:
            pass
        return True
    except Exception as e:
        print("persist dailyfive sheet error:", e)
        return False


def sync_dailyfive_completion_to_sheet(date_key, sprint_id, done_rows):
    try:
        if not done_rows:
            return False

        sheet = get_db_connection("Sprint_Daily_Tasks")
        headers = _get_or_init_headers(sheet, SPRINT_DAILY_TASKS_DEFAULT_HEADERS)
        rows = sheet.get_all_records()
        sprint_id_str = str(sprint_id)
        now_str = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")

        done_by_tid = {}
        done_by_idx = {}
        for d in done_rows:
            tid = str(d.get("task_id", "")).upper().strip()
            idx = _safe_int(d.get("index", 0), 0)
            if tid:
                done_by_tid[tid] = d
            if idx > 0:
                done_by_idx[idx] = d

        updated = 0
        for row_num, r in enumerate(rows, start=2):
            if (
                str(r.get("Date", "")).strip() != str(date_key)
                or str(r.get("Sprint_ID", "")).strip() != sprint_id_str
            ):
                continue

            row_tid = str(r.get("Task_ID", "")).upper().strip()
            row_idx = _safe_int(r.get("Priority", 0), 0)
            d = done_by_tid.get(row_tid) or done_by_idx.get(row_idx)
            if not d:
                continue

            existing_done = _to_boolish(r.get("Completed", ""))
            new_done = bool(d.get("done")) or existing_done
            evidence = str(d.get("evidence", "") or "").strip()

            row_map = {h: r.get(h, "") for h in headers}
            changed = False

            completed_val = "1" if new_done else "0"
            if str(row_map.get("Completed", "")).strip() != completed_val:
                row_map["Completed"] = completed_val
                changed = True

            if new_done:
                if not str(row_map.get("Completed_At", "")).strip():
                    row_map["Completed_At"] = now_str
                    changed = True
                if not str(row_map.get("Completion_Source", "")).strip():
                    row_map["Completion_Source"] = "action_log_df_marker"
                    changed = True
                if evidence and str(row_map.get("Completion_Evidence", "")).strip() != evidence:
                    row_map["Completion_Evidence"] = evidence
                    changed = True

            if changed:
                end_col = _a1_col(len(headers))
                values = [row_map.get(h, "") for h in headers]
                sheet.update(
                    f"A{row_num}:{end_col}{row_num}",
                    [values],
                    value_input_option="RAW",
                )
                updated += 1

        if updated > 0:
            try:
                fetch_sheet_data.clear()
            except:
                pass
        return updated > 0
    except Exception as e:
        print("sync dailyfive completion error:", e)
        return False


def sync_daily_sprint_progress_completion(date_key, sprint_id, completed, total, completion_rate):
    try:
        sheet = get_db_connection("Daily_Sprint_Progress")
        headers = _get_or_init_headers(sheet, DAILY_SPRINT_PROGRESS_DEFAULT_HEADERS)
        rows = sheet.get_all_records()
        sprint_id_str = str(sprint_id)
        now_str = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")

        target_row_num = None
        for idx, r in enumerate(rows, start=2):
            if (
                str(r.get("Date", "")).strip() == str(date_key)
                and str(r.get("Sprint_ID", "")).strip() == sprint_id_str
            ):
                target_row_num = idx
                break

        if target_row_num:
            row = rows[target_row_num - 2]
            row_map = {h: row.get(h, "") for h in headers}
            row_map["Date"] = str(date_key)
            row_map["Sprint_ID"] = sprint_id_str
            row_map["Completed"] = int(completed)
            row_map["Total"] = int(total)
            row_map["Completion_Rate"] = round(float(completion_rate), 4)
            row_map["Updated_At"] = now_str

            end_col = _a1_col(len(headers))
            values = [row_map.get(h, "") for h in headers]
            sheet.update(
                f"A{target_row_num}:{end_col}{target_row_num}",
                [values],
                value_input_option="RAW",
            )
        else:
            row_map = {h: "" for h in headers}
            row_map["Date"] = str(date_key)
            row_map["Sprint_ID"] = sprint_id_str
            row_map["Completed"] = int(completed)
            row_map["Total"] = int(total)
            row_map["Completion_Rate"] = round(float(completion_rate), 4)
            row_map["Updated_At"] = now_str
            values = [row_map.get(h, "") for h in headers]
            sheet.append_row(values, value_input_option="RAW")

        try:
            fetch_sheet_data.clear()
        except:
            pass
        return True
    except Exception as e:
        print("sync sprint progress completion error:", e)
        return False


def persist_daily_sprint_progress(date_key, sprint_id, daily_state, daily_five_status, sprint_progress=None):
    try:
        if not sprint_id:
            return False
        sheet = get_db_connection("Daily_Sprint_Progress")
        headers = _get_or_init_headers(sheet, DAILY_SPRINT_PROGRESS_DEFAULT_HEADERS)
        rows = sheet.get_all_records()
        sprint_id_str = str(sprint_id)
        target_row_num = None
        for idx, r in enumerate(rows, start=2):
            if (
                str(r.get("Date", "")).strip() == str(date_key)
                and str(r.get("Sprint_ID", "")).strip() == sprint_id_str
            ):
                target_row_num = idx
                break

        xc_obj = (daily_state or {}).get("xc", {}) or {}
        urgency_obj = (daily_state or {}).get("urgency", {}) or {}
        trend_obj = (daily_state or {}).get("trend", {}) or {}
        fallback_w = _safe_float((sprint_progress or {}).get("weight_current"), None)
        start_weight = get_start_weight_kg_for_date(date_key)
        if start_weight is None and fallback_w is not None:
            start_weight = float(fallback_w)

        prev_row = _get_prev_progress_row(rows, sprint_id_str, date_key)
        prev_start_weight = _safe_float((prev_row or {}).get("Start_Weight_KG"), None)
        prev_xc = _safe_float((prev_row or {}).get("XC_Value_KG"), None)

        actual_change = None
        xc_gap = None
        xc_ach_pct = None
        if (prev_start_weight is not None) and (start_weight is not None):
            actual_change = float(prev_start_weight) - float(start_weight)
        if (prev_xc is not None) and (actual_change is not None):
            xc_gap = float(prev_xc) - float(actual_change)
            if float(prev_xc) != 0:
                xc_ach_pct = (float(actual_change) / float(prev_xc)) * 100.0

        row_data = {
            "Date": str(date_key),
            "Sprint_ID": sprint_id_str,
            "Completed": _safe_int((daily_five_status or {}).get("completed", 0), 0),
            "Total": _safe_int((daily_five_status or {}).get("total", 0), 0),
            "Completion_Rate": round(_safe_float((daily_five_status or {}).get("completion_rate", 0.0), 0.0), 4),
            "XC_Value_KG": round(_safe_float(xc_obj.get("xc_value_kg", 0.0), 0.0), 3),
            "Urgency_Level": str(urgency_obj.get("level", "") or ""),
            "Pace_Status": str((sprint_progress or {}).get("pace_status", "") or ""),
            "Weight_Current": (
                round(_safe_float((sprint_progress or {}).get("weight_current"), 0.0), 3)
                if sprint_progress else ""
            ),
            "Trend_Weight": round(_safe_float(trend_obj.get("trend_weight", 0.0), 0.0), 3) if trend_obj else "",
            "Start_Weight_KG": (round(float(start_weight), 3) if start_weight is not None else ""),
            "Prev_Start_Weight_KG": (round(float(prev_start_weight), 3) if prev_start_weight is not None else ""),
            "Prev_XC_KG": (round(float(prev_xc), 3) if prev_xc is not None else ""),
            "Actual_Change_KG": (round(float(actual_change), 3) if actual_change is not None else ""),
            "XC_Gap_KG": (round(float(xc_gap), 3) if xc_gap is not None else ""),
            "XC_Achievement_PCT": (round(float(xc_ach_pct), 1) if xc_ach_pct is not None else ""),
            "Summary_JSON": json.dumps({
                "xc_reason": xc_obj.get("xc_reason", []),
                "today_logs_n": len((daily_state or {}).get("today_logs", []) or []),
                "available_slots": (daily_state or {}).get("available_slots", []),
                "calc": {
                    "start_weight": start_weight,
                    "prev_start_weight": prev_start_weight,
                    "prev_xc": prev_xc,
                    "actual_change": actual_change,
                    "xc_gap": xc_gap,
                    "xc_achievement_pct": xc_ach_pct,
                },
            }, ensure_ascii=False),
            "Updated_At": get_current_kst().strftime("%Y-%m-%d %H:%M:%S"),
        }

        values = [row_data.get(h, "") for h in headers]
        if target_row_num:
            end_col = _a1_col(len(headers))
            sheet.update(
                f"A{target_row_num}:{end_col}{target_row_num}",
                [values],
                value_input_option="RAW"
            )
        else:
            sheet.append_row(values, value_input_option="RAW")

        try:
            fetch_sheet_data.clear()
        except:
            pass
        return True
    except Exception as e:
        print("persist sprint progress sheet error:", e)
        return False


BAD_FOOD_KEYS = ["야식", "라면", "치킨", "피자", "햄버거", "과자", "디저트", "빵", "떡", "면", "버거"]
# 필요하면 더 정교화: "적정선" 음식은 제외 키워드로 관리 가능

def _has_any(text, keys):
    t = (text or "").lower()
    return any(k.lower() in t for k in keys)


def compute_day_score_detail(date_key, df_action):
    """
    return: dict(score, factors, stats)
    score 대략 -60~+80 범위
    - 키워드 규칙(음주/정크/운동) 유지
    - 섭취 kcal 및 탄단지 밸런스 반영
    - 사우나 수행 시 충분한 감점(막장지수 완화)
    """
    out = {
        "score": 0,
        "factors": [],
        "stats": {
            "intake_kcal": 0,
            "carb_ratio": None,
            "protein_ratio": None,
            "fat_ratio": None,
            "sauna_count": 0,
            "supplement_count": 0,
        },
    }
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out  # 데이터 없으면 중립

    day = df_action[df_action["Date"] == date_key].copy()
    if day.empty:
        return out  # 기록 없으면 '모름'이지만, 3일 합산이니 일단 0(중립)로 둡니다

    cat_text = " ".join(day.get("Category", "").astype(str).tolist())
    inp_text = " ".join(day.get("User_Input", "").astype(str).tolist())

    has_alcohol = "음주" in cat_text
    has_workout = "운동" in cat_text
    has_bad_food = _has_any(inp_text, BAD_FOOD_KEYS)

    intake_kcal = 0
    carbs_g = 0.0
    protein_g = 0.0
    fat_g = 0.0
    sauna_count = 0
    supplement_count = 0

    for _, r in day.iterrows():
        category = str(r.get("Category", "") or "")
        user_input = str(r.get("User_Input", "") or "")

        if ("사우나" in category) or ("사우나" in user_input):
            sauna_count += 1

        if "영양제" in category:
            supp_n = 0
            try:
                js_s = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
                supp_n = _safe_int(js_s.get("count", 0), 0)
            except:
                supp_n = 0
            # count가 비어 있어도 영양제 로그 1건은 최소 1개로 간주
            supplement_count += max(1, supp_n)

        if "섭취" not in category:
            continue
        try:
            js = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
        except:
            js = {}
        intake_kcal += _safe_int(js.get("calories", 0), 0)
        carbs_g += _safe_float(js.get("carbs", 0.0), 0.0)
        protein_g += _safe_float(js.get("protein", 0.0), 0.0)
        fat_g += _safe_float(js.get("fat", 0.0), 0.0)

    # 기록 공백 페널티(가벼움)
    # - 하루 로그가 1개 이하이면 방치로 +5
    low_logging = len(day) <= 1

    score = 0
    factors = []
    def add_factor(name, points, detail=""):
        if points == 0:
            return
        factors.append({"name": name, "points": int(points), "detail": detail})

    if has_alcohol:
        score += 30
        add_factor("음주", +30, "음주 기록")
    if has_bad_food:
        score += 15
        add_factor("정크키워드", +15, "고위험 음식 키워드")
    if has_workout:
        score -= 20
        add_factor("운동 수행", -20, "운동 카테고리 기록")
    if low_logging:
        score += 5
        add_factor("저기록 페널티", +5, "로그 1개 이하")

    # 시너지: 술+야식 같이 터지면 추가 벌점
    if has_alcohol and has_bad_food:
        score += 10
        add_factor("음주+정크 시너지", +10, "동시 발생")

    # kcal 기반 가감(고칼로리/저칼로리 극단 리스크 반영)
    if intake_kcal >= 2800:
        score += 20
        add_factor("섭취 kcal", +20, f"{intake_kcal}kcal (과다)")
    elif intake_kcal >= 2300:
        score += 12
        add_factor("섭취 kcal", +12, f"{intake_kcal}kcal (높음)")
    elif intake_kcal >= 1800:
        score += 5
        add_factor("섭취 kcal", +5, f"{intake_kcal}kcal (중상)")
    elif intake_kcal >= 1200:
        score -= 4
        add_factor("섭취 kcal", -4, f"{intake_kcal}kcal (적정)")
    elif intake_kcal > 0:
        score += 2
        add_factor("섭취 kcal", +2, f"{intake_kcal}kcal (저섭취)")

    # 탄단지 밸런스 가감(값이 있는 날만)
    macro_kcal = (carbs_g * 4.0) + (protein_g * 4.0) + (fat_g * 9.0)
    if macro_kcal > 0:
        carb_ratio = (carbs_g * 4.0) / macro_kcal
        protein_ratio = (protein_g * 4.0) / macro_kcal
        fat_ratio = (fat_g * 9.0) / macro_kcal
        out["stats"]["carb_ratio"] = float(carb_ratio)
        out["stats"]["protein_ratio"] = float(protein_ratio)
        out["stats"]["fat_ratio"] = float(fat_ratio)

        if protein_ratio < 0.18:
            score += 8
            add_factor("단백질 비율", +8, f"{protein_ratio*100:.0f}% (낮음)")
        elif 0.25 <= protein_ratio <= 0.40:
            score -= 3
            add_factor("단백질 비율", -3, f"{protein_ratio*100:.0f}% (양호)")

        if carb_ratio > 0.65:
            score += 4
            add_factor("탄수화물 비율", +4, f"{carb_ratio*100:.0f}% (높음)")
        if fat_ratio > 0.40:
            score += 4
            add_factor("지방 비율", +4, f"{fat_ratio*100:.0f}% (높음)")

        balanced = (0.20 <= protein_ratio <= 0.40) and (0.30 <= carb_ratio <= 0.60) and (0.15 <= fat_ratio <= 0.35)
        if balanced:
            score -= 4
            add_factor("탄단지 밸런스", -4, "균형 구간")

    # 사우나 수행일은 충분히 감점
    if sauna_count > 0:
        sauna_bonus = min(20, 12 + (sauna_count - 1) * 4)
        score -= sauna_bonus
        add_factor("사우나 보정", -sauna_bonus, f"{sauna_count}회")

    # 영양제 1개당 -5 완화(일일 상한 30점)
    if supplement_count > 0:
        supp_bonus = min(30, supplement_count * 5)
        score -= supp_bonus
        add_factor("영양제 보정", -supp_bonus, f"{supplement_count}개")

    out["score"] = int(score)
    out["factors"] = factors
    out["stats"]["intake_kcal"] = int(intake_kcal)
    out["stats"]["sauna_count"] = int(sauna_count)
    out["stats"]["supplement_count"] = int(supplement_count)
    return out


def compute_day_score(date_key, df_action):
    return int((compute_day_score_detail(date_key, df_action) or {}).get("score", 0))

def compute_makjang_3day_score(today_key, df_action):
    """
    0~100
    50 = 중립(운동X/음주X/식사 적정선)
    """
    d0 = today_key
    d1 = (datetime.strptime(today_key, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (datetime.strptime(today_key, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")

    d0d = compute_day_score_detail(d0, df_action)
    d1d = compute_day_score_detail(d1, df_action)
    d2d = compute_day_score_detail(d2, df_action)

    ds0 = int(d0d.get("score", 0))
    ds1 = int(d1d.get("score", 0))
    ds2 = int(d2d.get("score", 0))
    w0, w1, w2 = 0.5, 0.3, 0.2

    raw = 50 + (w0*ds0 + w1*ds1 + w2*ds2)
    score = int(round(max(0, min(100, raw))))

    weighted_factors = []
    for dkey, dres, w in [("d0", d0d, w0), ("d1", d1d, w1), ("d2", d2d, w2)]:
        for f in (dres.get("factors", []) or []):
            weighted_factors.append({
                "day": dkey,
                "name": str(f.get("name", "")),
                "points": int(f.get("points", 0)),
                "weighted_points": round(float(f.get("points", 0)) * w, 2),
                "detail": str(f.get("detail", "")),
            })

    return {
        "score": score,
        "raw_score": float(raw),
        "baseline": 50,
        "d0": {
            "date": d0,
            "day_score": ds0,
            "weight": w0,
            "weighted_contribution": round(ds0 * w0, 2),
            "factors": d0d.get("factors", []),
            "stats": d0d.get("stats", {}),
        },
        "d1": {
            "date": d1,
            "day_score": ds1,
            "weight": w1,
            "weighted_contribution": round(ds1 * w1, 2),
            "factors": d1d.get("factors", []),
            "stats": d1d.get("stats", {}),
        },
        "d2": {
            "date": d2,
            "day_score": ds2,
            "weight": w2,
            "weighted_contribution": round(ds2 * w2, 2),
            "factors": d2d.get("factors", []),
            "stats": d2d.get("stats", {}),
        },
        "weighted_factors": weighted_factors,
        "method": "50 + weighted(day_scores)",
    }


def render_makjang_score_drilldown(mj):
    if not mj:
        st.info("막장지수 데이터가 없습니다.")
        return

    day_rows = []
    for key, label in [("d0", "오늘"), ("d1", "어제"), ("d2", "그제")]:
        d = mj.get(key, {}) or {}
        day_rows.append({
            "구간": label,
            "date": str(d.get("date", "")),
            "day_score": float(d.get("day_score", 0)),
            "weight": float(d.get("weight", 0)),
            "weighted_contribution": float(d.get("weighted_contribution", 0)),
        })
    day_df = pd.DataFrame(day_rows)

    st.caption(
        f"공식: baseline {int(mj.get('baseline', 50))} + "
        f"가중합 {float(mj.get('raw_score', 50)) - int(mj.get('baseline', 50)):.2f} "
        f"= {int(mj.get('score', 0))}"
    )

    st.markdown("**일자별 원점수**")
    day_chart_df = day_df[["구간", "day_score"]].set_index("구간")
    st.bar_chart(day_chart_df)
    st.dataframe(
        day_df[["구간", "date", "day_score", "weight"]],
        width="stretch",
        hide_index=True,
    )

    wf = mj.get("weighted_factors", []) or []
    if wf:
        agg = {}
        for r in wf:
            name = str(r.get("name", "")).strip() or "기타"
            agg[name] = agg.get(name, 0.0) + float(r.get("weighted_points", 0.0))

        factor_rows = [{"요인": k, "가중점수": round(v, 2)} for k, v in agg.items()]
        factor_df = pd.DataFrame(factor_rows)
        factor_df["절대기여"] = factor_df["가중점수"].abs()
        factor_df = factor_df.sort_values("절대기여", ascending=False)

        st.markdown("**요인별 총 기여도(3일 가중합 기준)**")

        pos_df = factor_df[factor_df["가중점수"] > 0].copy()
        neg_df = factor_df[factor_df["가중점수"] < 0].copy()

        c_pos, c_neg = st.columns([1, 1])
        with c_pos:
            st.caption("악화 요인 (+)")
            if pos_df.empty:
                st.write("-")
            else:
                st.bar_chart(pos_df.set_index("요인")[["가중점수"]])

        with c_neg:
            st.caption("완화 요인 (-)")
            if neg_df.empty:
                st.write("-")
            else:
                neg_chart_df = neg_df.copy()
                neg_chart_df["완화기여"] = neg_chart_df["가중점수"].abs()
                st.bar_chart(neg_chart_df.set_index("요인")[["완화기여"]])

        factor_view = factor_df[["요인", "가중점수"]].copy()
        factor_view["방향"] = factor_view["가중점수"].apply(lambda x: "악화(+)" if x > 0 else "완화(-)" if x < 0 else "중립")
        st.dataframe(factor_view, width="stretch", hide_index=True)

    with st.expander("세부 로그(일자별 점수 근거)"):
        for key, label in [("d0", "오늘"), ("d1", "어제"), ("d2", "그제")]:
            d = mj.get(key, {}) or {}
            st.markdown(f"**{label} ({d.get('date','-')}) / day_score {d.get('day_score', 0)}**")
            stats = d.get("stats", {}) or {}
            if stats:
                kcal = stats.get("intake_kcal", 0)
                sauna_n = stats.get("sauna_count", 0)
                p = stats.get("protein_ratio")
                c = stats.get("carb_ratio")
                f = stats.get("fat_ratio")
                ratio_txt = "-"
                if (p is not None) and (c is not None) and (f is not None):
                    ratio_txt = f"탄:{c*100:.0f}% 단:{p*100:.0f}% 지:{f*100:.0f}%"
                st.caption(f"kcal={kcal}, 탄단지={ratio_txt}, 사우나={sauna_n}회")
            factors = d.get("factors", []) or []
            if not factors:
                st.write("- 중립(가감점 없음)")
            else:
                for f in factors:
                    pts = int(f.get("points", 0))
                    sign = "+" if pts >= 0 else ""
                    nm = str(f.get("name", "요인"))
                    dt = str(f.get("detail", ""))
                    st.write(f"- {nm}: {sign}{pts} ({dt})")


# ==========================================
# [Sprint 관리 함수]
# ==========================================

@st.cache_data(ttl=3600)
def get_active_sprint():
    try:
        records = fetch_sheet_data("Sprints")
        if not records:
            return None

        for sprint in records:
            if sprint.get('Status', '').lower().strip() == 'active':
                return {
                    'sprint_id': sprint['Sprint_ID'],
                    'name': sprint['Name'],
                    'start_date': datetime.strptime(sprint['Start_Date'], '%Y-%m-%d').replace(tzinfo=KST),
                    'end_date': datetime.strptime(sprint['End_Date'], '%Y-%m-%d').replace(tzinfo=KST),
                    'duration_days': int(sprint['Duration_Days']),
                    'description': sprint.get('Description', '')
                }
        return None
    except Exception as e:
        print(f"Error getting active sprint: {e}")
        return None

@st.cache_data(ttl=3600)
def get_sprint_goals(sprint_id):
    try:
        all_goals = fetch_sheet_data("Sprint_Goals")
        goals = {}
        for goal in all_goals:
            if goal['Sprint_ID'] == sprint_id:
                metric_type = goal['Metric_Type']
                goals[metric_type] = {
                    'goal_id': goal['Goal_ID'],
                    'start_value': float(goal['Start_Value']),
                    'target_value': float(goal['Target_Value']),
                    'unit': goal['Unit'],
                    'priority': int(goal['Priority'])
                }
        return goals
    except Exception as e:
        print(f"Error getting sprint goals: {e}")
        return {}


def _safe_parse_ymd(s):
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except:
        return None


def _latest_weight_on_or_before(df_health, cutoff_date):
    if df_health is None or df_health.empty:
        return None
    if ("Date" not in df_health.columns) or ("Weight" not in df_health.columns):
        return None
    df = df_health.copy()
    df["Date_Clean"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df["Weight_num"] = pd.to_numeric(df["Weight"], errors="coerce")
    df = df.dropna(subset=["Date_Clean", "Weight_num"])
    if df.empty:
        return None
    if cutoff_date is not None:
        df = df[df["Date_Clean"] <= cutoff_date]
    if df.empty:
        return None
    df = df.sort_values(["Date_Clean"])
    return float(df.iloc[-1]["Weight_num"])


def auto_close_ended_sprints():
    """
    종료일이 지난 active sprint를 done으로 자동 전환하고,
    목표 달성 여부(success/fail)를 Sprints 시트에 기록한다.
    """
    try:
        sh_s = get_db_connection("Sprints")
        sh_h = get_db_connection("Health_Log")
        sh_g = get_db_connection("Sprint_Goals")
    except Exception as e:
        print("auto close sprint: sheet open error:", e)
        return 0

    try:
        headers = [str(x).strip() for x in (sh_s.row_values(1) or [])]
        if not headers:
            return 0

        required_extra = ["Result", "Final_Wt", "Closed_At"]
        changed_header = False
        for c in required_extra:
            if c not in headers:
                headers.append(c)
                changed_header = True
        if changed_header:
            sh_s.update("A1", [headers], value_input_option="RAW")

        col_idx = {h: i + 1 for i, h in enumerate(headers)}
        if "Status" not in col_idx or "End_Date" not in col_idx or "Sprint_ID" not in col_idx:
            return 0

        rows = sh_s.get_all_records()
        if not rows:
            return 0

        goals_raw = pd.DataFrame(sh_g.get_all_records())
        target_by_sprint = {}
        if not goals_raw.empty and ("Metric_Type" in goals_raw.columns):
            g = goals_raw.copy()
            g["Metric_Type"] = g["Metric_Type"].astype(str).str.strip().str.lower()
            g = g[g["Metric_Type"] == "weight"]
            for _, r in g.iterrows():
                sid = str(r.get("Sprint_ID", "")).strip()
                if not sid:
                    continue
                tgt = _safe_float(r.get("Target_Value"), None)
                if tgt is not None:
                    target_by_sprint[sid] = float(tgt)

        df_health = pd.DataFrame(sh_h.get_all_records())
        today_kst = get_current_kst().date()
        now_str = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")

        updated = 0
        for row_num, r in enumerate(rows, start=2):
            status = str(r.get("Status", "")).strip().lower()
            if status != "active":
                continue

            end_date = _safe_parse_ymd(r.get("End_Date", ""))
            if not end_date:
                continue
            if today_kst <= end_date:
                continue

            sprint_id = str(r.get("Sprint_ID", "")).strip()
            target_wt = target_by_sprint.get(sprint_id)
            final_wt = _latest_weight_on_or_before(df_health, end_date)

            if (target_wt is not None) and (final_wt is not None):
                result = "success" if final_wt <= target_wt else "fail"
            else:
                result = "unknown"

            try:
                sh_s.update_cell(row_num, col_idx["Status"], "done")
                sh_s.update_cell(row_num, col_idx["Result"], result)
                sh_s.update_cell(row_num, col_idx["Final_Wt"], f"{final_wt:.1f}" if final_wt is not None else "")
                sh_s.update_cell(row_num, col_idx["Closed_At"], now_str)
                updated += 1
            except Exception as e:
                print("auto close sprint: update row error:", e)

        if updated > 0:
            try:
                fetch_sheet_data.clear()
                get_active_sprint.clear()
                get_sprint_goals.clear()
            except:
                pass
        return updated
    except Exception as e:
        print("auto close sprint error:", e)
        return 0


def run_daily_sprint_rollover_once():
    """
    같은 날짜에는 한 번만 자동 종료 판정을 수행한다.
    """
    try:
        today_key = get_current_kst().strftime("%Y-%m-%d")
        if st.session_state.get("_sprint_rollover_checked_date") == today_key:
            return 0
        st.session_state["_sprint_rollover_checked_date"] = today_key
        return auto_close_ended_sprints()
    except:
        return 0


def ensure_sprint_sheet_headers():
    """
    Sprint 관련 시트의 필수 헤더를 선제적으로 동기화한다.
    """
    synced = False
    try:
        sh_tasks = get_db_connection("Sprint_Daily_Tasks")
        _get_or_init_headers(sh_tasks, SPRINT_DAILY_TASKS_DEFAULT_HEADERS)
        synced = True
    except Exception as e:
        print("ensure headers error (Sprint_Daily_Tasks):", e)

    try:
        sh_progress = get_db_connection("Daily_Sprint_Progress")
        _get_or_init_headers(sh_progress, DAILY_SPRINT_PROGRESS_DEFAULT_HEADERS)
        synced = True
    except Exception as e:
        print("ensure headers error (Daily_Sprint_Progress):", e)

    return synced


def run_sheet_schema_sync_once():
    """
    같은 날짜에는 한 번만 시트 헤더 동기화를 수행한다.
    """
    try:
        today_key = get_current_kst().strftime("%Y-%m-%d")
        if st.session_state.get("_sheet_schema_sync_checked_date") == today_key:
            return False
        st.session_state["_sheet_schema_sync_checked_date"] = today_key
        return ensure_sprint_sheet_headers()
    except:
        return False

def ewma(values, alpha=0.35):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    m = vals[0]
    for x in vals[1:]:
        m = alpha * x + (1 - alpha) * m
    return m

def compute_weight_trend_for_date(df_health, date_key, lookback_days=21, alpha=0.35):
    if df_health is None or df_health.empty:
        return None

    df = df_health.copy()
    df["Date_Clean"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["Date_Clean"])

    end_dt = datetime.strptime(date_key, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=lookback_days)

    df = df[(df["Date_Clean"] >= start_dt.strftime("%Y-%m-%d")) & (df["Date_Clean"] <= date_key)].copy()
    if df.empty:
        return None

    df["Weight_num"] = pd.to_numeric(df.get("Weight", 0), errors="coerce")
    df = df.dropna(subset=["Weight_num"])
    if df.empty:
        return None

    df = df.sort_values(["Date_Clean"])
    df_last = df.groupby("Date_Clean", as_index=False).tail(1)

    weights = df_last["Weight_num"].tolist()
    trend = ewma(weights, alpha=alpha)

    return {
        "trend_weight": float(trend) if trend is not None else None,
        "alpha": alpha,
        "lookback_days": lookback_days,
        "n_points": int(len(weights)),
        "start_date": df_last["Date_Clean"].iloc[0],
        "end_date": df_last["Date_Clean"].iloc[-1],
    }

def get_or_create_daily_trend(date_key, df_health):
    cached = load_trend_cache(date_key)
    if cached and cached.get("trend_weight") is not None:
        return cached

    computed = compute_weight_trend_for_date(df_health, date_key, lookback_days=21, alpha=0.35)
    if computed and computed.get("trend_weight") is not None:
        computed["computed_at_kst"] = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
        save_trend_cache(date_key, computed)
        clear_old_caches()
        return computed

    return None

def calculate_sprint_progress(sprint, current_weight, trend_weight=None):
    if not sprint:
        return None

    try:
        now = get_current_kst()
        sprint_days = max(1, int(sprint.get('duration_days', 1)))
        days_passed_raw = max(0, (now - sprint['start_date']).days)
        days_passed = min(days_passed_raw, sprint_days)
        days_remaining = max(0, (sprint['end_date'] - now).days)

        goals = get_sprint_goals(sprint['sprint_id'])
        if 'weight' not in goals:
            return None

        weight_goal = goals['weight']
        total_loss = weight_goal['start_value'] - weight_goal['target_value']
        daily_target = total_loss / sprint_days
        expected_weight = weight_goal['start_value'] - (daily_target * days_passed)

        pace_weight = trend_weight if (trend_weight is not None) else current_weight
        actual_delta = pace_weight - expected_weight

        if actual_delta < -0.2:
            pace_status = 'ahead'
        elif actual_delta > 0.2:
            pace_status = 'behind'
        else:
            pace_status = 'on-track'

        remaining_loss = pace_weight - weight_goal['target_value']
        required_daily_pace = remaining_loss / max(1, days_remaining)

        return {
            'sprint': sprint,
            'day': min(sprint_days, days_passed + 1),
            'days_remaining': days_remaining,
            'progress_pct': (days_passed / sprint_days) * 100,
            'weight_start': weight_goal['start_value'],
            'weight_target': weight_goal['target_value'],
            'weight_current': current_weight,
            'weight_trend': trend_weight,
            'weight_expected': expected_weight,
            'weight_delta': actual_delta,
            'pace_status': pace_status,
            'required_daily_pace': required_daily_pace,
            'daily_target': daily_target,
            # ✅ [FIX] 메시지/남은kg 계산을 trend(= pace_weight) 기준으로 통일하기 위한 값
            'pace_weight': pace_weight,
        }
    except Exception as e:
        print(f"Error calculating sprint progress: {e}")
        return None

def get_or_create_daily_xc(date_key, sprint, daily_state):
    if not sprint:
        return None

    cached = load_xc_cache(date_key, sprint["sprint_id"])
    if cached and cached.get("xc_value_kg") is not None:
        return cached

    goals = get_sprint_goals(sprint["sprint_id"])
    if "weight" not in goals:
        return None

    weight_goal = goals["weight"]
    total_loss = weight_goal["start_value"] - weight_goal["target_value"]
    daily_target = total_loss / sprint["duration_days"]
    xc_state = dict(daily_state or {})
    xc_state["prev_xc_feedback"] = get_prev_xc_feedback(sprint["sprint_id"], date_key)
    slots_raw = list((daily_state or {}).get("available_slots", []) or [])
    slots_for_xc = []
    for s in slots_raw:
        ss = dict(s)
        reason = str(ss.get("reason_disabled") or "")
        # xC는 아침 1회 기준치이므로, 시간 경과로만 막힌 슬롯은 복원해 계산한다.
        if (not bool(ss.get("enabled"))) and (
            ("11시 이후" in reason) or ("21:00 이후" in reason) or ("해당 날짜는 이미 종료" in reason)
        ):
            ss["enabled"] = True
            ss["reason_disabled"] = ""
        slots_for_xc.append(ss)
    xc_state["available_slots"] = slots_for_xc
    xc = compute_xc(daily_target, xc_state)

    computed = {
        "xc_value_kg": float(xc["xc_value_kg"]),
        "xc_reason": xc["xc_reason"],
        "daily_target": float(daily_target),
        "date_key": date_key,
        "sprint_id": sprint["sprint_id"],
        "computed_at_kst": get_current_kst().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_xc_cache(date_key, sprint["sprint_id"], computed)
    clear_old_caches()
    return computed



def get_sprint_context(current_weight):
    sprint = get_active_sprint()
    if not sprint:
        return None

    progress = calculate_sprint_progress(sprint, current_weight)
    return progress

# ==========================================
# ✅ [FIX] Calendar: 이벤트를 start/end 포함 구조로 반환
# ==========================================

def _safe_parse_event_dt(v):
    if not v:
        return None
    # Google returns ISO string, maybe with Z or +09:00
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except:
        return None

def get_today_calendar_events(date_key=None):
    """
    반환 형태:
    {
      "Sports": [{"title":..., "start_dt":..., "end_dt":..., "is_all_day": False}],
      "Termin": [...]
    }
    """
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        service = build('calendar', 'v3', credentials=creds)

        if date_key:
            try:
                target_date = datetime.strptime(date_key, "%Y-%m-%d").date()
            except Exception:
                target_date = get_current_kst().date()
        else:
            target_date = get_current_kst().date()

        start_kst = datetime.combine(target_date, time(0, 0), tzinfo=KST)
        end_kst = start_kst + timedelta(days=1)

        timeMin = start_kst.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
        timeMax = end_kst.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

        evts = {"Sports": [], "Termin": []}

        for name, cid in CALENDAR_IDS.items():
            items = service.events().list(
                calendarId=cid,
                timeMin=timeMin, timeMax=timeMax,
                singleEvents=True, orderBy='startTime'
            ).execute().get('items', [])

            for i in items:
                start_raw = i['start'].get('dateTime')
                end_raw = i['end'].get('dateTime')
                is_all_day = False

                if start_raw:
                    start_dt = _safe_parse_event_dt(start_raw).astimezone(KST)
                    end_dt = _safe_parse_event_dt(end_raw).astimezone(KST) if end_raw else (start_dt + timedelta(hours=1))
                else:
                    # all-day event (date)
                    is_all_day = True
                    d = i['start'].get('date')
                    # all-day -> 00:00 ~ 24:00 KST
                    start_dt = datetime.fromisoformat(d).replace(tzinfo=KST)
                    end_dt = start_dt + timedelta(days=1)

                evts[name].append({
                    'title': i.get('summary', 'No Title'),
                    'start_dt': start_dt,
                    'end_dt': end_dt,
                    'is_all_day': is_all_day,
                })

        return evts
    except Exception as e:
        print("calendar fetch error:", e)
        return {"Sports": [], "Termin": []}

def _overlaps(a_start, a_end, b_start, b_end):
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    return latest_start < earliest_end

def build_available_slots(date_key, cal_evts):
    """
    ✅ [FIX] Hard Gate: AI에 캘린더 원문을 주지 않고,
    enabled 슬롯만 주기 위한 슬롯 생성기
    """
    dt = datetime.strptime(date_key, "%Y-%m-%d")
    is_weekday = dt.weekday() < 5

    now_kst = get_current_kst()  # ✅ 현재 시각
    lunch_plan_cutoff = time(11, 0)  # ✅ 11시 넘으면 점심계획 포기
    day_wrapup_cutoff = time(DAY_WRAPUP_START_HOUR, DAY_WRAPUP_START_MIN)  # ✅ 21시 이후 신규 제안 차단

    # windows (KST aware)
    day_start = datetime.combine(dt.date(), time(0,0), tzinfo=KST)
    lunch_start = datetime.combine(dt.date(), time(11,30), tzinfo=KST)
    lunch_end = datetime.combine(dt.date(), time(13,0), tzinfo=KST)
    evening_start = datetime.combine(dt.date(), time(19,0), tzinfo=KST)
    evening_end = datetime.combine(dt.date(), time(23,59), tzinfo=KST)

    termin_events = cal_evts.get("Termin", []) or []

    def has_termin_overlap(win_start, win_end):
        for e in termin_events:
            es = e['start_dt']
            ee = e['end_dt']
            if _overlaps(es, ee, win_start, win_end):
                return True
        return False

    # tag-based forced blocking
    lunch_tagged = False
    dinner_tagged = False
    for e in termin_events:
        title = str(e.get("title", "") or "")
        t = re.sub(r"\s+", "", title)
        if ("점심" in t) or ("점:" in t) or t.startswith("점"):
            lunch_tagged = True
        if ("저녁" in t) or ("저:" in t) or t.startswith("저"):
            dinner_tagged = True

    is_past_date = now_kst.date() > dt.date()
    lunch_blocked = has_termin_overlap(lunch_start, lunch_end) or lunch_tagged
    lunch_too_late = is_past_date or ((now_kst.date() == dt.date()) and (now_kst.time() >= lunch_plan_cutoff))
    evening_blocked = has_termin_overlap(evening_start, evening_end) or dinner_tagged
    day_wrapup_mode = is_past_date or ((now_kst.date() == dt.date()) and (now_kst.time() >= day_wrapup_cutoff))

    slots = []

    if is_weekday:
        slots.append({
            "slot_id": "lunch_micro",
            "label": "점심 30분",
            "start": lunch_start.strftime("%H:%M"),
            "end": lunch_end.strftime("%H:%M"),
            "enabled": (not lunch_blocked) and (not lunch_too_late),
            "allowed_types": ["walk_stairs", "gym_quick_30"],
            "notes": "이동 15분+샤워 30분 고려 시 운동 30분만 가능",
            "reason_disabled": 
                ("점심 태그/점심시간 일정(Termin)으로 막힘" if lunch_blocked else
                "해당 날짜는 이미 종료되어 신규 제안을 차단" if is_past_date else
                "11시 이후라 점심시간 계획은 폐기" if lunch_too_late else
            ""
        )
    })
        slots.append({
            "slot_id": "after_work_main",
            "label": "저녁 메인",
            "start": "19:00",
            "end": "23:59",
            "enabled": (not evening_blocked) and (not day_wrapup_mode),
            "allowed_types": ["gym_full_120", "outdoor_run_60"],
            "notes": "저녁 약속 또는 21:00 이후에는 신규 운동 제안 불가(일부 가능 없음)",
            "reason_disabled":
                ("저녁 태그 또는 19:00~23:59 일정(Termin)과 겹쳐서 저녁 운동 불가" if evening_blocked else
                 "해당 날짜는 이미 종료되어 신규 제안을 차단" if is_past_date else
                 "21:00 이후에는 하루 마무리 모드로 전환되어 신규 운동 제안을 차단" if day_wrapup_mode else
                 "")
        })
    else:
        # 주말은 일단 여유 슬롯 1개(필요 최소)
        slots.append({
            "slot_id": "weekend_main",
            "label": "주말 메인",
            "start": "09:00",
            "end": "21:00",
            "enabled": not day_wrapup_mode,
            "allowed_types": ["gym_full_120", "outdoor_run_60", "tennis_90"],
            "notes": "주말도 21:00 이후에는 신규 운동 제안 대신 마무리 코칭",
            "reason_disabled":
                ("해당 날짜는 이미 종료되어 신규 제안을 차단" if is_past_date else
                 "21:00 이후에는 하루 마무리 모드로 전환되어 신규 운동 제안을 차단" if day_wrapup_mode else
                 "")
        })

    return slots

def slots_to_compact_text(slots):
    # 디버그/표시용 (AI에는 JSON으로)
    lines = []
    for s in slots:
        ok = "ENABLED" if s["enabled"] else "DISABLED"
        lines.append(f"- {s['slot_id']}({s['start']}-{s['end']}): {ok} | {','.join(s['allowed_types'])}")
    return "\n".join(lines)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def get_phase(now_kst):
    h = now_kst.hour
    if h < 10:
        return "morning"
    if h < 13:
        return "midday"
    if h < 18:
        return "afternoon"
    if h < 21:
        return "evening"
    return "night"


def _parse_hhmm(t):
    try:
        hh, mm = str(t).split(":")
        return int(hh), int(mm)
    except:
        return None, None


def _meal_bucket_by_time(action_time):
    hh, _ = _parse_hhmm(action_time)
    if hh is None:
        return None
    if hh < 11:
        return "breakfast"
    if hh < 16:
        return "lunch"
    return "dinner"


def summarize_day_logs(df_action, date_key):
    out = {
        "breakfast_done": False,
        "lunch_done": False,
        "dinner_done": False,
        "last_meal_time": None,
        "worked_out_today": False,
        "workout_minutes_today": 0,
        "kcal_est_today": 0,
        "meals_count_today": 0,
        "today_logs": [],
    }
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out

    day = df_action[df_action["Date"] == date_key].copy()
    if day.empty:
        return out

    if "Action_Time" in day.columns:
        day = day.sort_values("Action_Time")

    last_meal_minutes = -1
    for _, r in day.iterrows():
        action_time = str(r.get("Action_Time", "") or "")
        category = str(r.get("Category", "") or "")
        user_input = str(r.get("User_Input", "") or "")

        out["today_logs"].append(f"[{action_time}] {category}: {user_input}")

        if "운동" in category:
            out["worked_out_today"] = True
            try:
                js = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
                out["workout_minutes_today"] += int(js.get("time", js.get("duration", 0)) or 0)
            except:
                pass

        if "섭취" in category:
            out["meals_count_today"] += 1
            try:
                js = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
                out["kcal_est_today"] += int(js.get("calories", 0) or 0)
            except:
                pass

            bucket = _meal_bucket_by_time(action_time)
            if bucket == "breakfast":
                out["breakfast_done"] = True
            elif bucket == "lunch":
                out["lunch_done"] = True
            elif bucket == "dinner":
                out["dinner_done"] = True

            hh, mm = _parse_hhmm(action_time)
            if hh is not None:
                mins = hh * 60 + (mm or 0)
                if mins >= last_meal_minutes:
                    last_meal_minutes = mins
                    out["last_meal_time"] = action_time

    return out


def summarize_day_facts(df_action, day_key):
    y = summarize_day_logs(df_action, day_key)
    alcohol = False
    if df_action is not None and (not df_action.empty) and ("Date" in df_action.columns):
        day = df_action[df_action["Date"] == day_key]
        if not day.empty and "Category" in day.columns:
            alcohol = day["Category"].astype(str).str.contains("음주", na=False).any()
    return {
        "worked_out": bool(y["worked_out_today"]),
        "kcal_est": int(y["kcal_est_today"]),
        "alcohol": bool(alcohol),
    }


def summarize_yesterday(df_action, yesterday_key):
    facts = summarize_day_facts(df_action, yesterday_key)
    return {
        "worked_out_yesterday": bool(facts["worked_out"]),
        "kcal_est_yesterday": int(facts["kcal_est"]),
        "alcohol_yesterday": bool(facts["alcohol"]),
    }


def summarize_yesterday_workout_review(df_action, date_key):
    yesterday_key = (datetime.strptime(date_key, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    out = {
        "date": yesterday_key,
        "had_workout": False,
        "workout_count": 0,
        "total_minutes": 0,
        "intensity_hint": "none",
        "focus_tags": [],
        "exercise_logs": [],
    }
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out

    day = df_action[df_action["Date"] == yesterday_key].copy()
    if day.empty:
        return out
    if "Action_Time" in day.columns:
        day = day.sort_values("Action_Time")

    focus = set()
    for _, r in day.iterrows():
        category = str(r.get("Category", "") or "")
        if "운동" not in category:
            continue
        out["had_workout"] = True
        out["workout_count"] += 1

        action_time = str(r.get("Action_Time", "") or "")
        user_input = str(r.get("User_Input", "") or "")
        if user_input:
            out["exercise_logs"].append(f"[{action_time}] {user_input}")

        try:
            js = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
            out["total_minutes"] += int(js.get("time", js.get("duration", 0)) or 0)
        except:
            pass

        t = user_input.lower()
        if any(k in t for k in ["3대", "스쿼트", "벤치", "데드", "웨이트", "근력"]):
            focus.add("strength")
        if any(k in t for k in ["하이록스", "인터벌", "러닝", "유산소", "싸이클"]):
            focus.add("conditioning")
        if any(k in t for k in ["플랭크", "코어", "크리스 크로스", "크런치"]):
            focus.add("core")
        if any(k in t for k in ["스트레칭", "요가", "사우나", "회복"]):
            focus.add("recovery")

    out["focus_tags"] = sorted(focus)
    out["exercise_logs"] = out["exercise_logs"][:4]

    total_minutes = int(out["total_minutes"] or 0)
    if not out["had_workout"]:
        out["intensity_hint"] = "none"
    elif total_minutes >= 120:
        out["intensity_hint"] = "high"
    elif total_minutes >= 60:
        out["intensity_hint"] = "medium"
    else:
        out["intensity_hint"] = "low"
    return out


def infer_training_mode(yesterday_workout_review, available_slots):
    y = yesterday_workout_review or {}
    enabled_slots = [s for s in (available_slots or []) if s.get("enabled")]
    enabled_count = len(enabled_slots)

    if not y.get("had_workout", False):
        return "push" if enabled_count >= 1 else "build"

    hint = str(y.get("intensity_hint", "none") or "none").lower()
    if hint == "high":
        return "recovery"
    if hint == "medium":
        return "build"
    return "push" if enabled_count >= 2 else "build"


def summarize_recent_backlog(df_action, date_key):
    d1 = (datetime.strptime(date_key, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (datetime.strptime(date_key, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")
    f1 = summarize_day_facts(df_action, d1)
    f2 = summarize_day_facts(df_action, d2)

    overeat_days = int((f1["kcal_est"] >= 2200) + (f2["kcal_est"] >= 2200))
    no_workout_days = int((not f1["worked_out"]) + (not f2["worked_out"]))
    alcohol_days = int(f1["alcohol"] + f2["alcohol"])

    return {
        "kcal_yesterday": int(f1["kcal_est"]),
        "kcal_d2": int(f2["kcal_est"]),
        "overeat_days_last2": int(overeat_days),
        "no_workout_days_last2": int(no_workout_days),
        "alcohol_days_last2": int(alcohol_days),
    }


def build_recent_action_evidence(df_action, date_key, lookback_days=2):
    out = {
        "date_keys": [],
        "today_logs": [],
        "recent_logs_newest_first": [],
        "repeat_bad_food_days": 0,
        "repeat_bad_food_tags": [],
    }
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out

    try:
        base = datetime.strptime(date_key, "%Y-%m-%d")
    except:
        return out

    keys = [(base - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0, lookback_days + 1)]
    out["date_keys"] = list(keys)

    day = df_action[df_action["Date"].isin(keys)].copy()
    if day.empty:
        return out

    if "Action_Time" not in day.columns:
        day["Action_Time"] = ""

    day = day.sort_values(["Date", "Action_Time"], ascending=[False, False], na_position="last")

    for _, r in day.iterrows():
        d = str(r.get("Date", "") or "")
        t = str(r.get("Action_Time", "") or "")
        c = str(r.get("Category", "") or "")
        u = str(r.get("User_Input", "") or "")
        line = f"[{d} {t}] {c}: {u}".strip()
        out["recent_logs_newest_first"].append(line)
        if d == date_key:
            out["today_logs"].append(f"[{t}] {c}: {u}".strip())

    bad_days = 0
    bad_tags = set()
    for dk in keys:
        sub = day[day["Date"] == dk]
        if sub.empty:
            continue
        txt = " ".join(sub.get("User_Input", "").astype(str).tolist())
        hit = False
        for k in BAD_FOOD_KEYS:
            if k in txt:
                hit = True
                bad_tags.add(k)
        if hit:
            bad_days += 1

    out["repeat_bad_food_days"] = int(bad_days)
    out["repeat_bad_food_tags"] = sorted(bad_tags)
    return out


def extract_calendar_flags(date_key, cal_evts):
    dt = datetime.strptime(date_key, "%Y-%m-%d").replace(tzinfo=KST)
    lunch_start = dt.replace(hour=11, minute=30)
    lunch_end = dt.replace(hour=13, minute=0)
    dinner_start = dt.replace(hour=19, minute=0)
    dinner_end = dt.replace(hour=23, minute=59)

    lunch_overlap = False
    dinner_overlap = False
    lunch_tag = False
    dinner_tag = False

    for e in (cal_evts.get("Termin", []) or []):
        title = str(e.get("title", "") or "")
        title_compact = re.sub(r"\s+", "", title.lower())
        es = e.get("start_dt")
        ee = e.get("end_dt")
        if es is not None and ee is not None:
            if _overlaps(es, ee, lunch_start, lunch_end):
                lunch_overlap = True
            if _overlaps(es, ee, dinner_start, dinner_end):
                dinner_overlap = True

        if ("점심" in title_compact) or ("점:" in title_compact) or title_compact.startswith("점"):
            lunch_tag = True
        if ("저녁" in title_compact) or ("저:" in title_compact) or title_compact.startswith("저"):
            dinner_tag = True

    return {
        "lunch_appointment": bool(lunch_overlap or lunch_tag),
        "dinner_appointment": bool(dinner_overlap or dinner_tag),
    }


def compute_xc(daily_target, daily_state):
    """
    xC: 오늘 달성해야 할 목표 변화량(kg)
    - 아침 1회 생성 후 하루 고정되는 '메이크업 타깃'
    - 어제 미이행/과섭취는 오늘 xC를 상향
    - 일정/컨디션 제약은 현실 범위로 하향
    - final: clamp(base + adjustments, XC_MIN_KG, XC_MAX_KG)
    """
    baseline = float(globals().get("XC_BASELINE_KG", 0.30))
    xc_min = float(globals().get("XC_MIN_KG", -0.20))
    xc_max = float(globals().get("XC_MAX_KG", 0.50))
    w = globals().get("XC_ADJ", {}) or {}

    raw_target = float(daily_target) if daily_target is not None else baseline
    base_xc = clamp(max(raw_target, baseline), 0.10, 0.45)
    adj = 0.0
    reasons = [f"base_from_daily_target={base_xc:.2f}"]

    ys = daily_state.get("yesterday_summary", {}) or {}
    rb = daily_state.get("recent_backlog", {}) or {}
    cf = daily_state.get("calendar_flags", {}) or {}
    slots = daily_state.get("available_slots", []) or []
    sprint_state = daily_state.get("sprint", {}) or {}
    bio = daily_state.get("bio_signal", {}) or {}

    if not ys.get("worked_out_yesterday", False):
        v = float(w.get("yesterday_no_workout", 0.08))
        adj += v
        reasons.append(f"+{v:.2f}:yesterday_no_workout_makeup")

    ykcal = int(ys.get("kcal_est_yesterday", 0) or 0)
    if ykcal >= 2600:
        v = float(w.get("yesterday_kcal_very_high", 0.10))
        adj += v
        reasons.append(f"+{v:.2f}:yesterday_high_kcal_makeup")
    elif ykcal >= 2200:
        v = float(w.get("yesterday_kcal_mid_high", 0.06))
        adj += v
        reasons.append(f"+{v:.2f}:yesterday_mid_high_kcal_makeup")

    if ys.get("alcohol_yesterday", False):
        v = float(w.get("yesterday_alcohol", 0.06))
        adj += v
        reasons.append(f"+{v:.2f}:yesterday_alcohol_makeup")

    if int(rb.get("overeat_days_last2", 0) or 0) >= 2:
        v = float(w.get("streak_overeat_2d", 0.05))
        adj += v
        reasons.append(f"+{v:.2f}:overeat_two_day_streak")
    if int(rb.get("no_workout_days_last2", 0) or 0) >= 2:
        v = float(w.get("streak_no_workout_2d", 0.05))
        adj += v
        reasons.append(f"+{v:.2f}:no_workout_two_day_streak")
    if int(rb.get("alcohol_days_last2", 0) or 0) >= 2:
        v = float(w.get("streak_alcohol_2d", 0.04))
        adj += v
        reasons.append(f"+{v:.2f}:alcohol_two_day_streak")

    pace_status = str(sprint_state.get("pace_status") or "")
    weight_delta = float(sprint_state.get("weight_delta") or 0.0)
    if pace_status == "behind":
        v = float(w.get("sprint_behind", 0.06))
        adj += v
        reasons.append(f"+{v:.2f}:sprint_behind")
        if weight_delta >= 0.6:
            v2 = float(w.get("sprint_far_behind", 0.04))
            adj += v2
            reasons.append(f"+{v2:.2f}:sprint_far_behind")
    elif pace_status == "ahead":
        v = float(w.get("sprint_ahead_relief", -0.04))
        adj += v
        reasons.append(f"{v:+.2f}:sprint_ahead_relief")

    enabled_count = sum(1 for s in slots if s.get("enabled"))
    after_work_open = _slot_enabled(slots, "after_work_main")
    lunch_open = _slot_enabled(slots, "lunch_micro")

    if after_work_open and not cf.get("dinner_appointment", False):
        v = float(w.get("slot_evening_open_push", 0.10))
        adj += v
        reasons.append(f"+{v:.2f}:evening_slot_open_push")
    elif lunch_open:
        v = float(w.get("slot_lunch_open_push", 0.04))
        adj += v
        reasons.append(f"+{v:.2f}:lunch_slot_open_push")

    if enabled_count == 0:
        v = float(w.get("slot_no_enabled_reality", -0.22))
        adj += v
        reasons.append(f"{v:+.2f}:no_enabled_slot_reality")
    elif enabled_count == 1:
        v = float(w.get("slot_single_enabled_reality", -0.08))
        adj += v
        reasons.append(f"{v:+.2f}:single_slot_reality")

    hrv = bio.get("hrv")
    rhr = bio.get("rhr")
    try:
        hrv = float(hrv) if hrv is not None else None
    except:
        hrv = None
    try:
        rhr = float(rhr) if rhr is not None else None
    except:
        rhr = None

    severe_bio = False
    if hrv is not None:
        if hrv <= 30:
            v = float(w.get("bio_very_low_hrv", -0.10))
            adj += v
            severe_bio = True
            reasons.append(f"{v:+.2f}:very_low_hrv_safety")
        elif hrv <= 34:
            v = float(w.get("bio_low_hrv", -0.06))
            adj += v
            reasons.append(f"{v:+.2f}:low_hrv_safety")
    if rhr is not None:
        if rhr >= 80:
            v = float(w.get("bio_very_high_rhr", -0.10))
            adj += v
            severe_bio = True
            reasons.append(f"{v:+.2f}:very_high_rhr_safety")
        elif rhr >= 74:
            v = float(w.get("bio_high_rhr", -0.06))
            adj += v
            reasons.append(f"{v:+.2f}:high_rhr_safety")
    if severe_bio and (hrv is not None and hrv <= 30) and (rhr is not None and rhr >= 80):
        v = float(w.get("bio_combined_risk", -0.05))
        adj += v
        reasons.append(f"{v:+.2f}:combined_bio_risk")

    # 전일 xC 미달분 carry-over
    prev_feedback = daily_state.get("prev_xc_feedback", {}) or {}
    prev_gap = prev_feedback.get("gap_kg")
    try:
        prev_gap = float(prev_gap) if prev_gap is not None else None
    except:
        prev_gap = None
    if (prev_gap is not None) and (prev_gap > 0):
        carry = min(0.15, prev_gap * 0.7)
        adj += carry
        reasons.append(f"+{carry:.2f}:carry_over_from_prev_xc_gap({prev_gap:.2f}kg)")

    xc = clamp(base_xc + adj, xc_min, xc_max)
    return {
        "xc_value_kg": float(xc),
        "xc_reason": reasons,
    }


def compute_urgency(daily_state):
    score = 0
    reasons = []
    xc_val = float((daily_state.get("xc", {}) or {}).get("xc_value_kg") or 0.0)
    ys = daily_state.get("yesterday_summary", {}) or {}
    sprint_state = daily_state.get("sprint", {}) or {}
    slots = daily_state.get("available_slots", []) or []

    if xc_val >= 0.40:
        score += 3
        reasons.append("+3:xc_high_push")
    elif xc_val >= 0.32:
        score += 2
        reasons.append("+2:xc_mid_high_push")
    elif xc_val < 0:
        score += 2
        reasons.append("+2:damage_control_day")

    if not ys.get("worked_out_yesterday", False):
        score += 2
        reasons.append("+2:yesterday_no_workout")

    ykcal = int(ys.get("kcal_est_yesterday", 0) or 0)
    if ykcal >= 2600:
        score += 3
        reasons.append("+3:yesterday_kcal_very_high")
    elif ykcal >= 2200:
        score += 2
        reasons.append("+2:yesterday_kcal_high")

    if ys.get("alcohol_yesterday", False):
        score += 1
        reasons.append("+1:yesterday_alcohol")

    if str(sprint_state.get("pace_status") or "") == "behind":
        score += 2
        reasons.append("+2:sprint_behind")

    enabled_count = sum(1 for s in slots if s.get("enabled"))
    if enabled_count == 0:
        score += 2
        reasons.append("+2:no_enabled_slot")
    elif enabled_count == 1:
        score += 1
        reasons.append("+1:single_slot")

    th = globals().get("URGENCY_THRESHOLDS", {}) or {}
    high_th = int(th.get("high", 7))
    medium_th = int(th.get("medium", 4))

    if score >= high_th:
        level = "high"
    elif score >= medium_th:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "score": int(score), "reason": reasons}


def build_daily_state(
    date_key,
    now_kst,
    df_action,
    cal_evts,
    available_slots,
    sprint_progress=None,
    trend_weight=None,
    current_hrv=None,
    current_rhr=None,
):
    """
    daily_state schema (요약):
    - date_key, now_kst, phase, late_mode
    - calendar_flags: lunch_appointment, dinner_appointment
    - meal_done: breakfast_done, lunch_done, dinner_done, last_meal_time
    - workout_done: worked_out_today, workout_minutes_today
    - intake_today: kcal_est_today, meals_count_today
    - yesterday_summary: worked_out_yesterday, kcal_est_yesterday, alcohol_yesterday
    - yesterday_workout_review: had_workout, total_minutes, intensity_hint, focus_tags, exercise_logs
    - recent_backlog: 최근 2일 누적 과섭취/무운동/음주
    - sprint: pace_status, weight_delta, required_daily_pace, daily_target
    - bio_signal: hrv, rhr
    - trend: trend_weight, linear_expected_weight
    - xc: xc_value_kg, xc_reason
    - urgency: level, score, reason
    - available_slots, today_logs
    """
    yesterday_key = (datetime.strptime(date_key, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    today = summarize_day_logs(df_action, date_key)
    yesterday = summarize_yesterday(df_action, yesterday_key)
    yesterday_workout_review = summarize_yesterday_workout_review(df_action, date_key)
    recent_backlog = summarize_recent_backlog(df_action, date_key)
    calendar_flags = extract_calendar_flags(date_key, cal_evts)

    meal_done = {
        "breakfast_done": bool(today["breakfast_done"]),
        "lunch_done": bool(today["lunch_done"]),
        "dinner_done": bool(today["dinner_done"]),
        "last_meal_time": today["last_meal_time"],
    }
    workout_done = {
        "worked_out_today": bool(today["worked_out_today"]),
        "workout_minutes_today": int(today["workout_minutes_today"]),
    }
    intake_today = {
        "kcal_est_today": int(today["kcal_est_today"]),
        "meals_count_today": int(today["meals_count_today"]),
    }
    kcal_target_today = int(get_daily_kcal_target())
    kcal_delta = int(intake_today["kcal_est_today"] - kcal_target_today)
    if kcal_delta >= 150:
        kcal_balance_status = "over"
    elif kcal_delta <= -250:
        kcal_balance_status = "under"
    else:
        kcal_balance_status = "within"
    intake_today["kcal_target_today"] = kcal_target_today
    intake_today["kcal_delta_today"] = kcal_delta
    intake_today["kcal_balance_status"] = kcal_balance_status

    daily_target = None
    linear_expected_weight = None
    if sprint_progress:
        daily_target = sprint_progress.get("daily_target")
        linear_expected_weight = sprint_progress.get("weight_expected")

    state = {
        "date_key": date_key,
        "now_kst": now_kst.isoformat(),
        "phase": get_phase(now_kst),
        "late_mode": (now_kst.hour > LATE_MODE_START_HOUR) or (now_kst.hour == LATE_MODE_START_HOUR and now_kst.minute >= LATE_MODE_START_MIN),
        "calendar_flags": calendar_flags,
        "meal_done": meal_done,
        "workout_done": workout_done,
        "intake_today": intake_today,
        "yesterday_summary": yesterday,
        "yesterday_workout_review": yesterday_workout_review,
        "recent_backlog": recent_backlog,
        "sprint": {
            "pace_status": (sprint_progress.get("pace_status") if sprint_progress else None),
            "weight_delta": (float(sprint_progress.get("weight_delta")) if sprint_progress and sprint_progress.get("weight_delta") is not None else None),
            "required_daily_pace": (float(sprint_progress.get("required_daily_pace")) if sprint_progress and sprint_progress.get("required_daily_pace") is not None else None),
            "daily_target": (float(sprint_progress.get("daily_target")) if sprint_progress and sprint_progress.get("daily_target") is not None else None),
        },
        "bio_signal": {
            "hrv": (float(current_hrv) if current_hrv is not None else None),
            "rhr": (float(current_rhr) if current_rhr is not None else None),
        },
        "trend": {
            "trend_weight": (float(trend_weight) if trend_weight is not None else None),
            "linear_expected_weight": (float(linear_expected_weight) if linear_expected_weight is not None else None),
        },
        "available_slots": available_slots or [],
        "today_logs": list(today["today_logs"] or []),
    }
    state["xc"] = compute_xc(daily_target, state)
    state["urgency"] = compute_urgency(state)
    return state


def _slot_enabled(slots, slot_id):
    for s in (slots or []):
        if s.get("slot_id") == slot_id:
            return bool(s.get("enabled"))
    return False


def _sanitize_plan_lines(text):
    if not text:
        return ""

    cleaned = []
    seen = set()
    for raw in str(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)

        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(line)

    return "\n".join(cleaned).strip()


def _enforce_evidence_quality(text, daily_state):
    if not text:
        return False
    logs = daily_state.get("today_logs", []) or []
    # 로그가 적은 날은 evidence gate를 완화한다.
    if len(logs) < 2:
        return True
    log_hits = 0
    for lg in logs:
        if len(lg) < 8:
            continue
        # 로그 문장 앞부분이 포함되는지 확인
        probe = lg[:12]
        if probe in text:
            log_hits += 1
        if log_hits >= 2:
            break

    numeric_hit = bool(re.search(r"\d+(\.\d+)?\s*(kg|kcal|분|%)", text))
    return (log_hits >= 2) and numeric_hit


def _is_action_oriented_text(text):
    if not text:
        return False
    low = str(text).lower()
    action_markers = [
        "실행", "고정", "차단", "기록", "준비", "시작", "마무리",
        "하십시오", "하세요", "하십시", "must", "do now",
    ]
    return any(m in low for m in action_markers)


def build_forced_next_action_from_state(daily_state):
    slots = daily_state.get("available_slots", []) or []
    enabled = [s for s in slots if s.get("enabled")]
    if enabled:
        s = enabled[0]
        label = str(s.get("label") or s.get("slot_id") or "다음 슬롯")
        start = str(s.get("start") or "")
        end = str(s.get("end") or "")
        return f"지금 확정 행동: {label}({start}-{end}) 기준으로 운동 1회를 캘린더/할 일 목록에 즉시 고정하고 실행하십시오."
    return "지금 확정 행동: 오늘은 추가 섭취를 종료하고, 내일 첫 활성 슬롯 운동 1회를 캘린더에 즉시 고정하십시오."


def validate_action_plan_output(result, daily_state):
    if not isinstance(result, dict):
        return result

    text = str(result.get("next_actions", "") or "")
    warns = str(result.get("warnings", "") or "")
    analysis = str(result.get("current_analysis", "") or "")

    text = text.replace("초저녁", "저녁")
    warns = warns.replace("초저녁", "저녁")
    analysis = analysis.replace("초저녁", "저녁")

    text = _sanitize_plan_lines(text)
    if not text:
        text = "AI 응답이 비어 있습니다. 다시 생성해 주세요."
    if not _is_action_oriented_text(text):
        text = f"{text}\n{build_forced_next_action_from_state(daily_state)}".strip()

    result["current_analysis"] = humanize_action_text(analysis)
    result["next_actions"] = humanize_action_text(text)
    result["warnings"] = warns.strip()
    return result


def apply_calorie_consistency_guard(result, daily_state):
    if not isinstance(result, dict):
        return result

    intake = (daily_state or {}).get("intake_today", {}) or {}
    kcal_now = _safe_int(intake.get("kcal_est_today", 0), 0)
    kcal_target = _safe_int(intake.get("kcal_target_today", DEFAULT_DAILY_KCAL_TARGET), DEFAULT_DAILY_KCAL_TARGET)
    kcal_delta = kcal_now - kcal_target
    workout = (daily_state or {}).get("workout_done", {}) or {}
    worked_out_today = bool(workout.get("worked_out_today", False))
    workout_minutes = _safe_int(workout.get("workout_minutes_today", 0), 0)

    high_intake_absolute = kcal_now >= int(max(kcal_target + 150, 1900))
    low_activity = (not worked_out_today) or (workout_minutes < 20)
    overeat_risk = (kcal_delta >= 120) or (high_intake_absolute and low_activity)
    if not overeat_risk:
        return result

    positive_tokens = [
        "안정적", "컨트롤", "잘하셨", "좋습니다", "양호", "문제없", "완벽", "괜찮",
    ]

    analysis = str(result.get("current_analysis", "") or "")
    actions = str(result.get("next_actions", "") or "")
    warnings = str(result.get("warnings", "") or "").strip()

    def has_positive(text):
        low = str(text).lower()
        return any(t in low for t in positive_tokens)

    if has_positive(analysis):
        analysis = (
            f"현재 섭취량은 약 {kcal_now}kcal로, 일일 기준 {kcal_target}kcal 대비 "
            f"{kcal_delta}kcal 초과입니다. 식사 패턴을 안정적이라고 보기 어렵습니다."
        )

    if has_positive(actions):
        actions = (
            f"지금부터 추가 섭취를 즉시 차단하십시오. 오늘 섭취량 {kcal_now}kcal는 "
            f"일일 기준 {kcal_target}kcal를 {kcal_delta}kcal 초과했습니다. "
            "남은 시간은 수분 섭취와 수면 복구에 집중하십시오."
        )

    if kcal_delta >= 0:
        warn_line = (
            f"일일 칼로리 기준({kcal_target}kcal) 대비 {kcal_delta}kcal 초과 상태입니다. "
            "오늘은 추가 섭취 차단이 최우선입니다."
        )
    else:
        warn_line = (
            f"현재 섭취량 {kcal_now}kcal 자체가 높은 편이며 활동량({workout_minutes}분)이 낮습니다. "
            "지금부터 추가 섭취를 차단하고 수면 복구에 집중하십시오."
        )
    if warn_line not in warnings:
        warnings = f"{warnings}\n{warn_line}".strip() if warnings else warn_line

    result["current_analysis"] = analysis
    result["next_actions"] = actions
    result["warnings"] = warnings
    return result


def apply_prev_xc_gap_warning(result, daily_state):
    if not isinstance(result, dict):
        return result
    prev_feedback = (daily_state or {}).get("prev_xc_feedback", {}) or {}
    gap = _safe_float(prev_feedback.get("gap_kg"), None)
    if (gap is None) or (float(gap) <= 0):
        return result

    date_txt = str(prev_feedback.get("date") or "어제")
    warn_line = (
        f"{date_txt} xC 미달분이 {float(gap):.2f}kg 남아 있습니다. "
        "오늘은 계획 이탈 없이 강행 모드로 진행하십시오."
    )
    warns = str(result.get("warnings", "") or "").strip()
    if warn_line not in warns:
        warns = f"{warns}\n{warn_line}".strip() if warns else warn_line
    result["warnings"] = warns
    return result


def format_ai_error_message(e):
    msg = str(e or "").strip()
    low = msg.lower()
    if ("insufficient_quota" in low) or ("error code: 429" in low) or ("quota" in low):
        return "OpenAI API 한도(429) 문제입니다. 결제/프로젝트 키를 확인해 주세요."
    if ("model" in low) and (("not found" in low) or ("does not exist" in low) or ("permission" in low)):
        return "모델 접근 권한 오류입니다. 사용 가능한 모델로 변경이 필요합니다."
    if not msg:
        return "AI 호출 오류가 발생했습니다."
    return f"AI 호출 오류: {msg[:220]}"


def build_rule_based_action_plan(daily_state):
    lines = [
        "AI 응답 생성에 실패했습니다. 1-2분 후 다시 생성해 주세요.",
        f"North Star: {NORTH_STAR_OBJECTIVE}",
        "현재 시점 의사결정은 daily_state 기준 사실 데이터로 다시 평가됩니다.",
        build_forced_next_action_from_state(daily_state),
    ]
    xc = (daily_state.get("xc", {}) or {}).get("xc_value_kg")
    if xc is not None:
        lines.append(f"참고 지표: 오늘 xC는 {float(xc):.1f}kg 기준입니다.")
    return "\n".join(lines)


# ==========================================
# AI 생성부 (Daily Five / Check-in / Action Plan)
# ==========================================

@st.cache_data(ttl=3600*24)
def ai_generate_daily_five(date_key, sprint, current_status, context):
    if not sprint:
        return None

    progress = calculate_sprint_progress(sprint, current_status['weight'])
    if not progress:
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)
    dt = datetime.strptime(date_key, '%Y-%m-%d')
    weekday = "Weekday (Work 06-19)" if dt.weekday() < 5 else "Weekend (Free)"

    # ✅ [FIX] calendar 원문 대신 slots만 전달
    slots = context.get("available_slots", [])
    slots_json = json.dumps(slots, ensure_ascii=False)
    yesterday_review = context.get("yesterday_workout_review")
    if not yesterday_review:
        try:
            df_action = pd.DataFrame(get_db_connection("Action_Log").get_all_records())
            yesterday_review = summarize_yesterday_workout_review(df_action, date_key)
        except:
            yesterday_review = {
                "date": "",
                "had_workout": False,
                "workout_count": 0,
                "total_minutes": 0,
                "intensity_hint": "none",
                "focus_tags": [],
                "exercise_logs": [],
            }
    default_mode = infer_training_mode(yesterday_review, slots)
    yesterday_review_json = json.dumps(yesterday_review, ensure_ascii=False)

    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()

    prompt = f"""
{persona_context}
{north_star_context}

역할: Sprint Daily Five 에디터
언어: 한국어

[섹션 목표]
- 2주 스프린트 달성을 위해 오늘 반드시 해야 할 핵심 5가지를 제시합니다.
- 5개 과제는 스프린트 목표와 직접 연결되어야 합니다.
- 우선순위, 실행성, 동기 부여를 분명하게 표현합니다.

[입력 사실]
Sprint: {sprint['name']} (Day {progress['day']}/{sprint['duration_days']})
Goal Loss: {progress['weight_start'] - progress['weight_target']:.1f}kg
Current Loss: {progress['weight_start'] - progress['weight_current']:.1f}kg
Expected Loss: {progress['weight_start'] - progress['weight_expected']:.1f}kg
Pace: {progress['pace_status']}
Date: {date_key} ({weekday})
HRV: {current_status['hrv']} | RHR: {current_status['rhr']} | Weight: {current_status['weight']:.1f}kg
AVAILABLE_SLOTS(JSON): {slots_json}
YESTERDAY_WORKOUT_REVIEW(JSON): {yesterday_review_json}
DEFAULT_TRAINING_MODE: {default_mode}

[작성 원칙]
- available_slots 사실과 모순되지 않아야 합니다.
- 표현과 전략은 자율적으로 구성하십시오.
- 5개 모두 구체적이고 실행 가능한 과제로 작성하십시오.
- 어제 운동 기록이 있으면 강점 1개 + 보완점 1개를 daily_message에 짧게 반영하십시오.
- today_training_mode는 오늘의 기본 방향(soft anchor)으로 제시하십시오.
- json 객체 1개만 출력하십시오.

[OUTPUT FORMAT - JSON ONLY]
{{
  "tasks": [
    {{
      "task_id": "task_1",
      "category": "workout/diet/recovery",
      "priority": 1,
      "title": "...",
      "description": "...",
      "why": "..."
    }}
  ],
  "daily_message": "...",
  "urgency_level": "high/medium/low",
  "today_training_mode": "recovery/build/push"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        for i, task in enumerate(result.get('tasks', [])):
            if 'task_id' not in task:
                task['task_id'] = f"task_{i+1}"

        mode = str(result.get("today_training_mode", "") or "").strip().lower()
        if mode not in {"recovery", "build", "push"}:
            mode = default_mode
        result["today_training_mode"] = mode

        return result

    except Exception as e:
        print(f"Error generating daily five: {e}")
        return None


def calculate_mission_status(current_weight):
    mission = get_active_mission()

    if not mission:
        return {
            'active': False, 'message': '데이터 로딩 중...',
            'name': 'Loading...', 'mission_id': '0',
            'current_weight': current_weight, 'target_weight': current_weight,
            'start_weight': current_weight, 'days_remaining': 0, 'days_passed': 0,
            'progress_pct': 0, 'weight_progress_pct': 0, 'daily_calories': 2000,
            'actual_loss': 0, 'target_loss': 0
        }

    now = get_current_kst()
    total_days = (mission['end_date'] - mission['start_date']).days
    days_passed = max(0, (now - mission['start_date']).days)
    days_remaining = max(0, (mission['end_date'] - now).days)
    target_loss = mission['start_weight'] - mission['target_weight']
    actual_loss = mission['start_weight'] - current_weight

    return {
        'active': True, 'mission_id': mission['mission_id'], 'name': mission['name'],
        'days_remaining': days_remaining, 'days_passed': days_passed,
        'progress_pct': min(100, max(0, (days_passed / total_days) * 100)) if total_days > 0 else 0,
        'weight_progress_pct': min(100, max(0, (actual_loss / target_loss) * 100)) if target_loss > 0 else 0,
        'target_weight': mission['target_weight'], 'start_weight': mission['start_weight'],
        'current_weight': current_weight, 'daily_calories': mission['daily_calories'],
        'actual_loss': actual_loss, 'target_loss': target_loss
    }

def validate_mission_rules(mission_id, category, user_input):
    rules = get_mission_rules(mission_id)
    violations = []
    if '음주' in category and 'alcohol_ban' in rules:
        ban_rule = rules['alcohol_ban']
        now_kst = get_current_kst()
        if now_kst.month == ban_rule.get('month'):
            violations.append({'type': 'alcohol_ban', 'severity': ban_rule.get('penalty', 'warning'), 'message': f"🚫 Dry Feb 위반! {now_kst.month}월은 금주입니다."})
    return violations

def analyze_patterns(df_health, df_action):
    patterns = []
    if df_health.empty or df_action.empty:
        return patterns
    try:
        if not df_action[df_action['Category'].str.contains('음주', na=False)].empty:
            patterns.append({'message': '최근 음주 기록이 있습니다. 수면 질 저하 주의.'})
    except:
        pass
    return patterns

def get_today_intake_stats(df_action, date_key):
    """
    오늘 섭취(칼로리 추정치) 합계와 섭취 로그 횟수.
    ai_parse_log가 Action_Log의 AI_Analysis_JSON에 calories를 넣는다는 가정.
    """
    total_cal = 0
    n_meals = 0

    if df_action is None or df_action.empty:
        return {"calories": 0, "meals": 0}

    if "Date" not in df_action.columns:
        return {"calories": 0, "meals": 0}

    today_df = df_action[df_action["Date"] == date_key]
    if today_df.empty:
        return {"calories": 0, "meals": 0}

    for _, r in today_df.iterrows():
        try:
            cat = str(r.get("Category", ""))
            if "섭취" not in cat:
                continue

            n_meals += 1
            js = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
            total_cal += int(js.get("calories", 0) or 0)
        except:
            # JSON 깨짐/누락이면 칼로리는 0 처리, 섭취횟수는 이미 카운트됨
            pass

    return {"calories": int(total_cal), "meals": int(n_meals)}


def prepare_full_context(df_health, df_action, current_weight, is_morning_fixed=False):
    now_kst = get_current_kst()
    mission = calculate_mission_status(current_weight)

    today_date_key = (now_kst - timedelta(days=1)).strftime('%Y-%m-%d') if now_kst.hour < 5 else now_kst.strftime('%Y-%m-%d')

    five_days_ago = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=5)).strftime('%Y-%m-%d')
    recent_logs = df_action[df_action['Date'] >= five_days_ago].copy()
    if is_morning_fixed:
        recent_logs = recent_logs[recent_logs['Date'] < today_date_key]

    if not recent_logs.empty:
        dates_in_range = pd.date_range(start=five_days_ago, end=today_date_key, freq='D').strftime('%Y-%m-%d').tolist()
        logs_by_date = []
        for date_str in dates_in_range:
            date_logs = recent_logs[recent_logs['Date'] == date_str]
            if date_logs.empty:
                logs_text = "(기록 없음)"
            else:
                logs_text = "\n".join([f"• [{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in date_logs.sort_values('Action_Time').iterrows()])
            logs_by_date.append(f"[{date_str}]\n{logs_text}")
        recent_logs_text = "\n\n".join(logs_by_date)
    else:
        recent_logs_text = "기록 없음"

    cutoff = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    df_h_30 = df_health[df_health['Date'] >= cutoff].copy()

    for c in ['HRV', 'RHR']:
        if c in df_h_30.columns:
            df_h_30[c] = pd.to_numeric(df_h_30[c], errors='coerce')

    hrv_avg = df_h_30.tail(7)['HRV'].mean() if not df_h_30.empty else 0
    rhr_avg = df_h_30.tail(7)['RHR'].mean() if not df_h_30.empty else 0

    sleep_info = "No sleep data."
    if not df_h_30.empty:
        last = df_h_30.iloc[-1]
        actual_sleep_duration = last.get('Sleep_duration', 0)
        sleep_info = f"Last Sleep: {actual_sleep_duration}h"

    patterns = analyze_patterns(df_h_30, df_action[df_action['Date'] >= cutoff])
    ptn_txt = "\n".join([p['message'] for p in patterns]) if patterns else "None"

    return f"""
[USER] Age:36, Male, Mission:{mission.get('name', 'N/A')}, Wt:{current_weight}kg

[LOGS (Last 5 Days)]
{recent_logs_text}

[TODAY: {today_date_key}]
[STATS] HRV:{hrv_avg:.1f}, RHR:{rhr_avg:.1f}
[SLEEP] {sleep_info}
[PATTERNS] {ptn_txt}
"""

@st.cache_data(ttl=3600*24)
def ai_generate_daily_checkin(date_key, hrv, rhr, weight, morning_context, calendar_str):
    client = OpenAI(api_key=OPENAI_API_KEY)
    dt = datetime.strptime(date_key, '%Y-%m-%d')
    wc = "Workday(06-19 Work). No heavy gym during work." if dt.weekday() < 5 else "Weekend. Free."
    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()

    prompt = f"""
{persona_context}
{north_star_context}

역할: Daily Check-in 에디터
언어: 한국어 존댓말

[섹션 목표]
- 조간신문 1면+사설처럼, 오늘 컨디션이 왜 이런지 최근 기록 기반으로 해석합니다.
- 오늘 하루를 어떤 기조로 운영해야 하는지 큰 방향을 제시합니다.

[입력 사실]
Data: {morning_context}
Vitals: {date_key}, HRV:{hrv}, RHR:{rhr}, Wt:{weight}
Schedule: {calendar_str}
Constraint: {wc}

[출력 원칙]
- 입력 사실과 모순되지 마십시오.
- 해석과 코칭 표현은 자율적으로 구성하십시오.
- json 객체 1개만 출력하십시오.

Output JSON: {{
  "condition_signal": "Green/Yellow/Red",
  "headline": "오늘 컨디션 한 문장 헤드라인",
  "headline_reason": "헤드라인 근거 1줄",
  "analysis": "왜 이런 상태인지 설명",
  "mission_workout": "오늘 운동 운영 기조",
  "mission_diet": "오늘 식단 운영 기조",
  "mission_recovery": "오늘 회복 운영 기조"
}}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        return {
            "condition_signal": "Yellow",
            "headline": "생성 오류",
            "headline_reason": "모델/네트워크 오류로 생성 실패",
            "analysis": str(e),
            "mission_workout": "-",
            "mission_diet": "-",
            "mission_recovery": "-"
        }

@st.cache_data(ttl=900)
def ai_generate_action_plan_cached(hrv, rhr, weight, date_key, slots_key, activity_sig, today_activities, available_slots):
    result = ai_generate_action_plan_internal(
        hrv, rhr, weight,
        list(today_activities or []),
        available_slots
    )
    # 실패 응답은 캐시에 남기지 않는다.
    if (result or {}).get("fallback_mode") == "ai_error":
        raise RuntimeError("non-cacheable-action-plan-failure")
    return result

def ai_generate_action_plan_internal(hrv, rhr, weight, today_activities, available_slots):
    client = OpenAI(api_key=OPENAI_API_KEY)
    now_kst = get_current_kst()

    try:
        sheet_health = get_db_connection("Health_Log")
        sheet_action = get_db_connection("Action_Log")
        df_health = pd.DataFrame(sheet_health.get_all_records())
        df_action = pd.DataFrame(sheet_action.get_all_records())
    except:
        df_health = pd.DataFrame()
        df_action = pd.DataFrame()

    date_key = get_mission_date_key()
    sprint = None
    progress = None
    trend_weight = None
    try:
        sprint = get_active_sprint()
    except:
        sprint = None

    if sprint and (not df_health.empty):
        try:
            trend = get_or_create_daily_trend(date_key, df_health)
            trend_weight = trend["trend_weight"] if trend else None
        except:
            trend_weight = None

        try:
            progress = calculate_sprint_progress(sprint, weight, trend_weight=trend_weight)
        except:
            progress = None

    cal_evts = {"Sports": [], "Termin": []}
    try:
        cal_evts = get_today_calendar_events(date_key)
    except:
        cal_evts = {"Sports": [], "Termin": []}

    if not available_slots:
        available_slots = build_available_slots(date_key, cal_evts)

    daily_state = build_daily_state(
        date_key=date_key,
        now_kst=now_kst,
        df_action=df_action,
        cal_evts=cal_evts,
        available_slots=available_slots,
        sprint_progress=progress,
        trend_weight=trend_weight,
        current_hrv=hrv,
        current_rhr=rhr,
    )
    if sprint:
        try:
            fixed_xc = get_or_create_daily_xc(date_key, sprint, daily_state)
            if fixed_xc and (fixed_xc.get("xc_value_kg") is not None):
                daily_state["xc"] = {
                    "xc_value_kg": float(fixed_xc.get("xc_value_kg")),
                    "xc_reason": list(fixed_xc.get("xc_reason", []) or []),
                }
                daily_state["urgency"] = compute_urgency(daily_state)
        except Exception:
            pass
        try:
            daily_state["prev_xc_feedback"] = get_prev_xc_feedback(sprint["sprint_id"], date_key)
        except Exception:
            daily_state["prev_xc_feedback"] = {"date": None, "gap_kg": None}
    else:
        daily_state["prev_xc_feedback"] = {"date": None, "gap_kg": None}

    tomorrow_key = (datetime.strptime(date_key, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_slots = []
    try:
        tomorrow_events = get_today_calendar_events(tomorrow_key)
        tomorrow_slots = build_available_slots(tomorrow_key, tomorrow_events)
    except:
        tomorrow_slots = []
    tomorrow_enabled_slots = [s for s in (tomorrow_slots or []) if s.get("enabled")]

    daily_five_status = {
        "has_plan": False,
        "completed": 0,
        "total": 0,
        "completion_rate": 0.0,
    }
    try:
        if sprint:
            daily_five_status = get_daily_five_completion(date_key, sprint["sprint_id"], df_action)
    except:
        pass

    daily_five_plan = {}
    try:
        if sprint:
            daily_five_plan = load_dailyfive_cache(date_key, sprint["sprint_id"]) or {}
    except:
        daily_five_plan = {}

    try:
        if sprint:
            persist_daily_sprint_progress(
                date_key=date_key,
                sprint_id=sprint["sprint_id"],
                daily_state=daily_state,
                daily_five_status=daily_five_status,
                sprint_progress=progress,
            )
    except:
        pass

    sprint_status = {
        "has_sprint": bool(progress),
        "pace_status": (progress.get("pace_status") if progress else None),
        "weight_delta": (
            float(progress.get("weight_delta"))
            if progress and (progress.get("weight_delta") is not None)
            else None
        ),
        "required_daily_pace": (
            float(progress.get("required_daily_pace"))
            if progress and (progress.get("required_daily_pace") is not None)
            else None
        ),
    }
    no_workout_today = not bool((daily_state.get("workout_done", {}) or {}).get("worked_out_today", False))
    behind_pace = sprint_status.get("pace_status") == "behind"
    daily_five_zero_done = bool(daily_five_status.get("has_plan")) and int(daily_five_status.get("completed", 0)) == 0
    urgency_obj = daily_state.get("urgency", {}) or {}
    urgency_level = str(urgency_obj.get("level") or "low")
    xc_obj = daily_state.get("xc", {}) or {}
    xc_value = xc_obj.get("xc_value_kg")
    try:
        xc_value = float(xc_value) if xc_value is not None else None
    except:
        xc_value = None
    xc_inverse_day = (xc_value is not None) and (xc_value < 0)
    xc_high_push = (xc_value is not None) and (xc_value >= 0.40)

    if xc_inverse_day:
        coaching_mode = "damage_control"
    elif urgency_level == "high" or xc_high_push or (no_workout_today and (behind_pace or daily_five_zero_done)):
        coaching_mode = "recovery_lockdown"
    else:
        coaching_mode = "normal"

    recent_evidence = build_recent_action_evidence(df_action, date_key, lookback_days=2)
    today_logs_full = list((daily_state.get("today_logs", []) or []))
    if (not today_logs_full) and today_activities:
        today_logs_full = list(today_activities)

    logs_text_today = "\n".join([f"- {x}" for x in today_logs_full]) if today_logs_full else "- (기록 없음)"
    recent_logs_all = list(recent_evidence.get("recent_logs_newest_first", []) or [])
    logs_text_recent = "\n".join([f"- {x}" for x in recent_logs_all]) if recent_logs_all else "- (기록 없음)"
    repeat_bad_food_days = int(recent_evidence.get("repeat_bad_food_days", 0) or 0)
    repeat_bad_food_tags_json = json.dumps(recent_evidence.get("repeat_bad_food_tags", []), ensure_ascii=False)
    daily_state_json = json.dumps(daily_state, ensure_ascii=False, indent=2)
    sprint_status_json = json.dumps(sprint_status, ensure_ascii=False, indent=2)
    daily_five_status_json = json.dumps(daily_five_status, ensure_ascii=False, indent=2)
    yesterday_workout_review = daily_state.get("yesterday_workout_review", {}) or {}
    yesterday_workout_review_json = json.dumps(yesterday_workout_review, ensure_ascii=False, indent=2)
    prev_xc_feedback = daily_state.get("prev_xc_feedback", {}) or {}
    prev_xc_feedback_json = json.dumps(prev_xc_feedback, ensure_ascii=False, indent=2)
    tomorrow_slots_json = json.dumps(tomorrow_slots, ensure_ascii=False, indent=2)
    xc_reason_json = json.dumps(xc_obj.get("xc_reason", []), ensure_ascii=False)
    urgency_json = json.dumps(urgency_obj, ensure_ascii=False)
    intake_obj = daily_state.get("intake_today", {}) or {}
    kcal_now = _safe_int(intake_obj.get("kcal_est_today", 0), 0)
    kcal_target_today = _safe_int(intake_obj.get("kcal_target_today", DEFAULT_DAILY_KCAL_TARGET), DEFAULT_DAILY_KCAL_TARGET)
    kcal_delta_today = _safe_int(intake_obj.get("kcal_delta_today", kcal_now - kcal_target_today), kcal_now - kcal_target_today)
    kcal_balance_status = str(intake_obj.get("kcal_balance_status", "within") or "within")
    daily_five_mode = str((daily_five_plan or {}).get("today_training_mode", "") or "").strip().lower()
    if daily_five_mode not in {"recovery", "build", "push"}:
        daily_five_mode = infer_training_mode(yesterday_workout_review, available_slots)
    training_anchor = {
        "mode": daily_five_mode,
        "is_soft_anchor": True,
        "source": "daily_five_or_yesterday_review",
    }
    training_anchor_json = json.dumps(training_anchor, ensure_ascii=False)
    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()

    prompt = f"""
{persona_context}
{north_star_context}

역할: 실시간 코칭 에디터
언어: 한국어 존댓말

[섹션 목표]
- Action Plan은 '속보'처럼 지금 시점 행동을 안내해야 합니다.
- Daily Check-in의 큰 방향을 바탕으로, 지금 당장 실행 가능한 코칭을 만듭니다.
- xC와 스프린트 마일스톤 달성 확률을 높이는 방향으로 제안합니다.
- 응원, 독려, 경고 톤은 상황에 맞게 자율적으로 사용하십시오.
- 이 섹션의 최우선 목적은 분석 전시가 아니라 행동 변화 유도입니다.

[중요 원칙]
- daily_state 사실과 모순되지 마십시오.
- 캘린더 원문이 아니라 available_slots를 사실로 사용하십시오.
- available_slots에서 enabled=true 운동 슬롯이 하나도 없으면 신규 운동을 제안하지 말고, 하루 마무리 코칭만 제시하십시오.
- 오늘 xC 수치를 반드시 본문에 명시하고, 행동 강도 판단의 근거로 사용하십시오.
- 칼로리 판단은 intake_today.kcal_target_today 기준으로 수행하십시오.
- intake_today.kcal_est_today가 kcal_target_today를 120kcal 이상 초과했거나, 절대 섭취량이 높은데 활동량이 낮으면 절대 '안정적/컨트롤 양호'라고 쓰지 마십시오.
- 최근 로그는 D-2, D-1, D0(오늘)까지 모두 참고하십시오.
- 코칭 문장은 최신 로그(특히 오늘의 가장 최근 이벤트)를 우선 근거로 작성하십시오.
- 같은 고위험 식사 패턴이 2일 이상 반복되면 warnings에 강한 경고를 포함하십시오(모욕/인신공격 금지).
- 로그가 적어도 판단을 포기하지 말고, 현재 데이터로 최선의 실행안을 제시하십시오.
- 코드 토큰(gym_quick_30 등)을 노출하지 마십시오.
- json 객체 1개만 출력하십시오.

[COACHING_CONTEXT]
- heuristic_mode: {coaching_mode}
- xc_value_kg: {xc_value}
- xc_reason: {xc_reason_json}
- urgency: {urgency_json}
- intake_kcal_today: {kcal_now}
- kcal_target_today: {kcal_target_today}
- kcal_delta_today: {kcal_delta_today}
- kcal_balance_status: {kcal_balance_status}
- repeat_bad_food_days_d2_to_d0: {repeat_bad_food_days}
- repeat_bad_food_tags: {repeat_bad_food_tags_json}

[YESTERDAY_WORKOUT_REVIEW]
{yesterday_workout_review_json}

[PREV_XC_FEEDBACK]
{prev_xc_feedback_json}
- gap_kg가 양수면 전일 xC 미달입니다.
- 해당 경우 warnings에 1문장 경고를 포함하십시오.

[TRAINING_ANCHOR]
{training_anchor_json}
- training_anchor.mode는 오늘 코칭의 기본 방향(soft anchor)입니다.
- 다만 시간/슬롯/컨디션 등 현실 데이터가 바뀌면 mode를 유연하게 조정할 수 있습니다.
- mode를 조정했다면 next_actions에 이유를 1문장으로 명시하십시오.

[SPRINT_STATUS]
{sprint_status_json}

[DAILY_FIVE_STATUS]
{daily_five_status_json}

[DAILY_STATE]
{daily_state_json}

[TOMORROW_SLOTS]
date_key: {tomorrow_key}
enabled_count: {len(tomorrow_enabled_slots)}
{tomorrow_slots_json}

[TODAY_LOG_EVIDENCE_FULL]
{logs_text_today}

[RECENT_LOG_EVIDENCE_D2_D1_D0_NEWEST_FIRST]
{logs_text_recent}

[OUTPUT FORMAT - JSON]
{{
  "current_analysis": "현재 상황 해석 (1~3문장)",
  "next_actions": "즉시 실행 가능한 코칭 본문. 여러 줄 가능.",
  "warnings": "리스크/경고가 있으면 작성, 없으면 빈 문자열"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result = validate_action_plan_output(result, daily_state)
        result = apply_prev_xc_gap_warning(result, daily_state)
        result = apply_calorie_consistency_guard(result, daily_state)

        now_kst2 = get_current_kst()
        result['generated_at'] = now_kst2.strftime('%H:%M')
        result['generated_hours_left'] = 24 - now_kst2.hour
        return result
    except Exception as e:
        print("action plan error:", e)
        fallback = {
            "current_analysis": "AI 호출 실패로 규칙 기반 플랜으로 전환했습니다.",
            "next_actions": build_rule_based_action_plan(daily_state),
            "warnings": format_ai_error_message(e),
            "fallback_mode": "ai_error",
        }
        fallback = validate_action_plan_output(fallback, daily_state)
        fallback = apply_prev_xc_gap_warning(fallback, daily_state)
        fallback = apply_calorie_consistency_guard(fallback, daily_state)
        now_kst2 = get_current_kst()
        return {
            "current_analysis": fallback.get("current_analysis", "AI 호출 실패"),
            "next_actions": fallback.get("next_actions", "데이터 부족으로 오늘은 판단 불가"),
            "warnings": fallback.get("warnings", ""),
            "generated_at": now_kst2.strftime('%H:%M'),
            "generated_hours_left": 24 - now_kst2.hour
        }

def ai_generate_action_plan(hrv, rhr, weight, full_context, today_activities, available_slots):
    slots_key = json.dumps(available_slots, ensure_ascii=False, sort_keys=True)
    activity_items = list(today_activities or [])
    activity_sig = "|".join(activity_items[:20])
    date_key = get_mission_date_key()
    try:
        return ai_generate_action_plan_cached(
            hrv, rhr, weight,
            date_key,
            slots_key,
            activity_sig,
            tuple(activity_items),
            available_slots
        )
    except Exception:
        # 캐시 우회 1회 실행 (실패 결과 비캐시)
        return ai_generate_action_plan_internal(
            hrv, rhr, weight,
            list(today_activities),
            available_slots
        )


def _safe_json_obj(raw):
    if isinstance(raw, dict):
        return raw
    try:
        obj = json.loads(raw or "{}")
        if isinstance(obj, dict):
            return obj
        return {}
    except:
        return {}


def _extract_minutes_from_text(text):
    txt = str(text or "")
    mins = 0
    for m in re.finditer(r"(\d{1,3})\s*(분|min|minute)", txt, flags=re.IGNORECASE):
        try:
            mins += int(m.group(1))
        except:
            pass
    return int(mins)


def summarize_action_range(df_action, start_key, end_key):
    out = {
        "start_date": start_key,
        "end_date": end_key,
        "log_count": 0,
        "meals_count": 0,
        "intake_kcal": 0,
        "carbs_g": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "workout_sessions": 0,
        "workout_minutes": 0,
        "alcohol_logs": 0,
        "recovery_minutes": 0,
        "sauna_count": 0,
        "supplement_count": 0,
        "notes_count": 0,
        "df_marks": [],
        "evidence_logs": [],
    }
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out

    date_series = pd.to_datetime(df_action["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    in_range = df_action[(date_series >= start_key) & (date_series <= end_key)].copy()
    if in_range.empty:
        return out

    sort_cols = [c for c in ["Date", "Action_Time"] if c in in_range.columns]
    if sort_cols:
        in_range = in_range.sort_values(sort_cols, na_position="last")

    marks = set()
    for _, r in in_range.iterrows():
        out["log_count"] += 1
        category = str(r.get("Category", "") or "")
        text = str(r.get("User_Input", "") or "").strip()
        tm = str(r.get("Action_Time", "") or "").strip()
        js = _safe_json_obj(r.get("AI_Analysis_JSON", "{}"))

        if len(out["evidence_logs"]) < 16:
            out["evidence_logs"].append(f"[{tm or '--:--'}] {category}: {text}")

        if "섭취" in category:
            out["meals_count"] += 1
            out["intake_kcal"] += _safe_int(js.get("calories", 0), 0)
            out["carbs_g"] += _safe_float(js.get("carbs", 0.0), 0.0)
            out["protein_g"] += _safe_float(js.get("protein", 0.0), 0.0)
            out["fat_g"] += _safe_float(js.get("fat", 0.0), 0.0)

        if "운동" in category:
            out["workout_sessions"] += 1
            dur = _safe_int(js.get("duration", js.get("time", 0)), 0)
            if dur <= 0:
                dur = _extract_minutes_from_text(text)
            out["workout_minutes"] += int(dur)

        if "음주" in category:
            out["alcohol_logs"] += 1

        if "회복" in category:
            rec_min = _safe_int(js.get("duration", 0), 0)
            if rec_min <= 0:
                rec_min = _extract_minutes_from_text(text)
            out["recovery_minutes"] += int(rec_min)
            if ("사우나" in category) or ("사우나" in text):
                out["sauna_count"] += 1

        if "영양제" in category:
            supp_n = _safe_int(js.get("count", 0), 0)
            if supp_n <= 0:
                supp_list = js.get("supplements")
                if isinstance(supp_list, list):
                    supp_n = len(supp_list)
            out["supplement_count"] += int(max(1, supp_n))

        if "노트" in category:
            out["notes_count"] += 1

        up_cat = category.upper()
        up_text = text.upper()
        if "DF" in up_cat or ("DF" in up_text):
            marks_raw = js.get("df_marks", [])
            if isinstance(marks_raw, list):
                for m in marks_raw:
                    t = str(m or "").strip().upper()
                    if re.fullmatch(r"DF[1-5]", t):
                        marks.add(t)
            for m in re.finditer(r"(?<![A-Z0-9])DF\s*([1-5])(?!\d)", up_text):
                marks.add(f"DF{int(m.group(1))}")

    out["df_marks"] = sorted(marks)
    return out


def summarize_health_for_day(df_health, date_key, current_weight, current_hrv, current_rhr):
    out = {
        "weight": _safe_float(current_weight, 0.0),
        "hrv": _safe_float(current_hrv, 0.0),
        "rhr": _safe_float(current_rhr, 0.0),
    }
    if df_health is None or df_health.empty or "Date" not in df_health.columns:
        return out
    df = df_health.copy()
    df["Date_Key"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    day = df[df["Date_Key"] == date_key]
    if day.empty:
        return out
    row = day.iloc[-1]
    out["weight"] = _safe_float(row.get("Weight", out["weight"]), out["weight"])
    out["hrv"] = _safe_float(row.get("HRV", out["hrv"]), out["hrv"])
    out["rhr"] = _safe_float(row.get("RHR", out["rhr"]), out["rhr"])
    return out


def summarize_health_range(df_health, start_key, end_key, current_weight, current_hrv, current_rhr):
    out = {
        "start_date": start_key,
        "end_date": end_key,
        "start_weight": None,
        "end_weight": _safe_float(current_weight, 0.0),
        "weight_change_kg": None,
        "avg_hrv": _safe_float(current_hrv, 0.0),
        "avg_rhr": _safe_float(current_rhr, 0.0),
    }
    if df_health is None or df_health.empty or "Date" not in df_health.columns:
        return out

    df = df_health.copy()
    df["Date_Key"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    in_range = df[(df["Date_Key"] >= start_key) & (df["Date_Key"] <= end_key)].copy()
    if in_range.empty:
        return out

    in_range["Weight_num"] = pd.to_numeric(in_range.get("Weight", 0), errors="coerce")
    in_range["HRV_num"] = pd.to_numeric(in_range.get("HRV", 0), errors="coerce")
    in_range["RHR_num"] = pd.to_numeric(in_range.get("RHR", 0), errors="coerce")
    in_range = in_range.sort_values("Date_Key")

    w_valid = in_range["Weight_num"].dropna()
    if not w_valid.empty:
        out["start_weight"] = float(w_valid.iloc[0])
        out["end_weight"] = float(w_valid.iloc[-1])
        out["weight_change_kg"] = float(out["start_weight"] - out["end_weight"])
    hrv_valid = in_range["HRV_num"].dropna()
    rhr_valid = in_range["RHR_num"].dropna()
    if not hrv_valid.empty:
        out["avg_hrv"] = float(hrv_valid.mean())
    if not rhr_valid.empty:
        out["avg_rhr"] = float(rhr_valid.mean())
    return out


def _get_tomorrow_slots(date_key):
    try:
        d = datetime.strptime(date_key, "%Y-%m-%d") + timedelta(days=1)
        t_key = d.strftime("%Y-%m-%d")
        t_ev = get_today_calendar_events(t_key)
        t_slots = build_available_slots(t_key, t_ev)
        t_enabled = [s for s in (t_slots or []) if s.get("enabled")]
        return t_key, t_slots, t_enabled
    except:
        return "", [], []


def _pick_next_action_from_slots(enabled_slots):
    if not enabled_slots:
        return "내일 07:30에 체중을 측정하고, 오전 중 10분 걷기 1회를 먼저 실행하십시오."
    s = enabled_slots[0]
    label = str(s.get("label") or s.get("slot_id") or "다음 가용 슬롯")
    start = str(s.get("start") or "")
    allowed = list(s.get("allowed_types", []) or [])
    action_txt = ""
    if allowed:
        first = str(allowed[0] or "")
        action_txt = HUMANIZE_MAP.get(first, humanize_action_text(first))
    if action_txt:
        return f"내일 {label}({start})에 {action_txt} 1회를 먼저 실행하십시오."
    return f"내일 {label}({start})에 운동 1회를 먼저 실행하십시오."


def build_daily_wrapup_payload(
    date_key,
    now_kst,
    df_health,
    df_action,
    current_weight,
    current_hrv,
    current_rhr,
    cal_evts,
    available_slots,
    sprint=None,
    sprint_progress=None,
    trend_weight=None,
    xc=None,
):
    action_summary = summarize_action_range(df_action, date_key, date_key)
    health_summary = summarize_health_for_day(df_health, date_key, current_weight, current_hrv, current_rhr)
    day_score_detail = compute_day_score_detail(date_key, df_action)
    tomorrow_key, tomorrow_slots, tomorrow_enabled = _get_tomorrow_slots(date_key)

    daily_five_status = {"has_plan": False, "completed": 0, "total": 0, "completion_rate": 0.0}
    daily_five_titles = []
    prev_xc_feedback = {"date": None, "gap_kg": None}
    if sprint:
        try:
            daily_five_status = get_daily_five_completion(date_key, sprint["sprint_id"], df_action)
        except:
            pass
        try:
            five_plan = load_dailyfive_cache(date_key, sprint["sprint_id"]) or {}
            for t in list(five_plan.get("tasks", []) or [])[:5]:
                title = str(t.get("title", "") or "").strip()
                if title:
                    daily_five_titles.append(title)
        except:
            pass
        try:
            prev_xc_feedback = get_prev_xc_feedback(sprint["sprint_id"], date_key)
        except:
            pass

    enabled_slots = [s for s in (available_slots or []) if s.get("enabled")]
    disabled_slots = [s for s in (available_slots or []) if not s.get("enabled")]
    payload = {
        "kind": "daily",
        "date_key": date_key,
        "generated_at_kst": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
        "health": health_summary,
        "action_summary": action_summary,
        "makjang_day_score": {
            "score": int(day_score_detail.get("score", 0)),
            "factors": list(day_score_detail.get("factors", []) or [])[:8],
        },
        "xc": {
            "value_kg": (_safe_float((xc or {}).get("xc_value_kg"), 0.0) if xc else None),
            "reason": list((xc or {}).get("xc_reason", []) or []) if xc else [],
        },
        "sprint": {
            "active": bool(sprint),
            "pace_status": (sprint_progress.get("pace_status") if sprint_progress else None),
            "weight_delta": (_safe_float(sprint_progress.get("weight_delta"), 0.0) if sprint_progress else None),
            "required_daily_pace": (_safe_float(sprint_progress.get("required_daily_pace"), 0.0) if sprint_progress else None),
            "daily_five_status": daily_five_status,
            "daily_five_titles": daily_five_titles,
        },
        "calendar": {
            "enabled_slots": enabled_slots,
            "disabled_slots": disabled_slots,
            "today_events_count": {
                "sports": len((cal_evts or {}).get("Sports", []) or []),
                "termin": len((cal_evts or {}).get("Termin", []) or []),
            },
            "tomorrow_key": tomorrow_key,
            "tomorrow_slots": tomorrow_slots,
            "tomorrow_enabled_slots": tomorrow_enabled,
        },
        "prev_xc_feedback": prev_xc_feedback,
        "trend_weight": (_safe_float(trend_weight, 0.0) if trend_weight is not None else None),
    }
    return payload


def build_weekly_wrapup_payload(
    date_key,
    now_kst,
    df_health,
    df_action,
    current_weight,
    current_hrv,
    current_rhr,
    sprint=None,
    sprint_progress=None,
):
    end_dt = datetime.strptime(date_key, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=6)
    start_key = start_dt.strftime("%Y-%m-%d")
    end_key = end_dt.strftime("%Y-%m-%d")

    action_summary = summarize_action_range(df_action, start_key, end_key)
    health_summary = summarize_health_range(df_health, start_key, end_key, current_weight, current_hrv, current_rhr)

    day_scores = []
    for i in range(7):
        dk = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
        dd = compute_day_score_detail(dk, df_action)
        day_scores.append({"date": dk, "score": int(dd.get("score", 0))})

    payload = {
        "kind": "weekly",
        "week_start": start_key,
        "week_end": end_key,
        "generated_at_kst": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
        "action_summary": action_summary,
        "health": health_summary,
        "day_scores": day_scores,
        "sprint": {
            "active": bool(sprint),
            "pace_status": (sprint_progress.get("pace_status") if sprint_progress else None),
            "weight_delta": (_safe_float(sprint_progress.get("weight_delta"), 0.0) if sprint_progress else None),
            "required_daily_pace": (_safe_float(sprint_progress.get("required_daily_pace"), 0.0) if sprint_progress else None),
        },
    }
    return payload


def build_rule_based_wrapup(kind, payload):
    now_kst = get_current_kst()
    action = (payload or {}).get("action_summary", {}) or {}
    intake = int(action.get("intake_kcal", 0))
    workouts = int(action.get("workout_sessions", 0))
    minutes = int(action.get("workout_minutes", 0))
    alcohol_n = int(action.get("alcohol_logs", 0))
    meals = int(action.get("meals_count", 0))
    supp_n = int(action.get("supplement_count", 0))

    praise = ""
    warning = ""
    critique = ""
    next_action = ""

    if kind == "daily":
        df_stat = (((payload or {}).get("sprint", {}) or {}).get("daily_five_status", {}) or {})
        df_done = int(df_stat.get("completed", 0))
        df_total = int(df_stat.get("total", 0))
        xc_val = (((payload or {}).get("xc", {}) or {}).get("value_kg"))
        prev_gap = (((payload or {}).get("prev_xc_feedback", {}) or {}).get("gap_kg"))

        if workouts > 0 or df_done >= 2 or (intake >= 1000 and intake <= 2200):
            praise = f"오늘은 기록 기반 실행이 남아 있습니다. 운동 {workouts}회({minutes}분), DF {df_done}/{df_total}는 유지 자산입니다."
        if alcohol_n > 0:
            warning = f"음주 기록 {alcohol_n}건이 확인됩니다. 내일 컨디션 하락을 전제로 보수 운영이 필요합니다."
        elif workouts <= 0 and intake >= 1800:
            warning = "섭취 대비 활동량이 부족합니다. 이 패턴이 2일 연속이면 스프린트 미달 위험이 급증합니다."
        if meals <= 1:
            critique = "식사 기록이 너무 적어 실제 섭취가 과소평가될 가능성이 큽니다. 기록 정확도를 먼저 복구하십시오."
        elif workouts <= 0:
            critique = "오늘 행동 변화가 충분하지 않았습니다. 일정 탓보다 실행 우선순위 배치가 문제였습니다."
        else:
            critique = "실행은 있었지만 강도 또는 일관성이 목표 대비 부족할 수 있습니다."

        if (prev_gap is not None) and (_safe_float(prev_gap, 0.0) > 0):
            warning = (warning + " " if warning else "") + f"전일 xC 미달분 {_safe_float(prev_gap, 0.0):.2f}kg가 남아 있습니다."
        if xc_val is not None:
            critique = f"{critique} 오늘 xC 기준은 {float(xc_val):.1f}kg였습니다."

        tomorrow_enabled = (((payload or {}).get("calendar", {}) or {}).get("tomorrow_enabled_slots", []) or [])
        next_action = _pick_next_action_from_slots(tomorrow_enabled)
    else:
        health = (payload or {}).get("health", {}) or {}
        wchg = health.get("weight_change_kg")
        if (wchg is not None) and (float(wchg) > 0):
            praise = f"주간 체중 변화 {float(wchg):.2f}kg 감소는 의미 있는 진전입니다."
        if workouts <= 2:
            warning = "주간 운동 빈도가 낮습니다. 다음 주는 최소 3회 고정 슬롯이 필요합니다."
        if intake >= 14000:
            critique = "주간 섭취량이 높아 누적 적자를 만들지 못했습니다. 외식 구간의 의사결정 실패가 원인입니다."
        else:
            critique = "이번 주는 실행 강도 편차가 컸습니다. 좋은 날과 무너진 날의 격차를 줄여야 합니다."
        next_action = "다음 주 월요일 07:30에 체중 측정 후, 점심 또는 퇴근 슬롯 중 1개를 먼저 확정하십시오."

    overview = (
        f"기록 기준 요약: 섭취 {intake}kcal, 식사 {meals}회, 운동 {workouts}회({minutes}분), "
        f"영양제 {supp_n}개, 음주 {alcohol_n}건."
    )

    return {
        "kind": kind,
        "overview": overview.strip(),
        "praise": str(praise or "").strip(),
        "warning": str(warning or "").strip(),
        "critique": str(critique or "").strip(),
        "next_action": str(next_action or "").strip(),
        "generated_at": now_kst.strftime("%H:%M"),
        "fallback_mode": "rule_based",
    }


def _normalize_wrapup_result(result, kind):
    out = dict(result or {})
    out["kind"] = kind
    out["overview"] = str(out.get("overview", "") or "").strip()
    out["praise"] = str(out.get("praise", "") or "").strip()
    out["warning"] = str(out.get("warning", "") or "").strip()
    out["critique"] = str(out.get("critique", "") or "").strip()
    out["next_action"] = str(out.get("next_action", "") or "").strip()
    out["generated_at"] = str(out.get("generated_at", "") or "").strip() or get_current_kst().strftime("%H:%M")
    return out


def ai_generate_wrapup(kind, payload):
    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    client = OpenAI(api_key=OPENAI_API_KEY)

    if kind == "weekly":
        role_txt = "Weekly Wrap-up 에디터"
        goal_txt = (
            "- 일요일 밤 기준 주간 회고를 작성합니다.\n"
            "- 칭찬은 근거가 있을 때만 작성하고, 없으면 빈 문자열로 두십시오.\n"
            "- 다음 주 첫 행동은 시간 앵커를 포함한 1개 실행안으로 제시하십시오."
        )
    else:
        role_txt = "Daily Wrap-up 에디터"
        goal_txt = (
            "- 오늘 하루를 종합 평가합니다.\n"
            "- 칭찬할 근거가 없으면 praise는 빈 문자열로 두십시오.\n"
            "- 경고/비판은 회피하지 말고 행동 변화 관점에서 분명히 작성하십시오.\n"
            "- 내일 첫 행동은 시간/행동/분량이 포함된 1개 실행안으로 제시하십시오."
        )

    prompt = f"""
{persona_context}
{north_star_context}

역할: {role_txt}
언어: 한국어 존댓말

[섹션 목표]
{goal_txt}

[입력 사실(JSON)]
{payload_json}

[출력 원칙]
- 사실 데이터와 모순되지 마십시오.
- 의료 진단은 하지 마십시오.
- 공허한 일반론을 피하고, 수치 근거를 최소 1개 포함하십시오.
- json 객체 1개만 출력하십시오.

[OUTPUT FORMAT - JSON]
{{
  "overview": "하루/주간 총평 2~4문장",
  "praise": "칭찬할 근거가 있으면 작성, 없으면 빈 문자열",
  "warning": "경고 문장(없으면 빈 문자열)",
  "critique": "비판/원인 진단 1~2문장",
  "next_action": "다음 실행 1개(시간 포함)"
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        result["generated_at"] = get_current_kst().strftime("%H:%M")
        return _normalize_wrapup_result(result, kind)
    except Exception as e:
        fb = build_rule_based_wrapup(kind, payload)
        fb["warning"] = (str(fb.get("warning", "") or "").strip() + "\n" + format_ai_error_message(e)).strip()
        fb["fallback_mode"] = "ai_error"
        return _normalize_wrapup_result(fb, kind)


def get_or_create_wrapup(kind, cache_key, payload):
    cached = load_wrapup_cache(kind, cache_key)
    if cached:
        return cached
    result = ai_generate_wrapup(kind, payload)
    if (result or {}).get("fallback_mode") != "ai_error":
        save_wrapup_cache(kind, cache_key, result)
        clear_old_caches()
    return result


def render_wrapup_block(kind, wrapup, xc=None):
    title = "🌙 Daily Wrap-up" if kind == "daily" else "📅 Weekly Wrap-up"
    label = "내일 첫 행동" if kind == "daily" else "다음 주 첫 행동"
    st.markdown(
        f"""<h3 style="margin-bottom: 10px;">{title} <span class="time-badge">{wrapup.get('generated_at', get_current_kst().strftime('%H:%M'))} 기준</span></h3>""",
        unsafe_allow_html=True,
    )
    if xc and (xc.get("xc_value_kg") is not None):
        st.caption(f"🎯 xC(오늘 기대 변화량): {float(xc.get('xc_value_kg')):.1f}kg")

    with st.container(border=True):
        st.markdown(f"**📊 종합 평가:** {wrapup.get('overview', '-')}")
        praise = str(wrapup.get("praise", "") or "").strip()
        if praise:
            st.success(f"✅ 칭찬: {praise}")
        warning = str(wrapup.get("warning", "") or "").strip()
        if warning:
            st.warning(f"⚠️ 경고: {warning}")
        critique = str(wrapup.get("critique", "") or "").strip()
        if critique:
            st.markdown(f"**🧨 비판/진단:** {critique}")
        next_action = str(wrapup.get("next_action", "") or "").strip()
        if next_action:
            st.markdown(f"**🧭 {label}:** {next_action}")

def ai_parse_log(category, user_text, log_time, ref_data=""):
    client = OpenAI(api_key=OPENAI_API_KEY)

    MY_SUPPLEMENTS = {
        "마그네슘": "마그네슘 135mg",
        "밀크시슬": "SAT 실리빈 150mg+아티초크 150mg+커큐민 150mg",
        "락토핏": "유산균 20억 CFU + 아연 2.55mg",
        "오메가3": "EPA+DHA 1000mg + 비타민E 11mg",
        "비타민D3": "비타민D 100µg"
    }

    if "영양제" in category:
        matched_info = []
        for name, detail in MY_SUPPLEMENTS.items():
            if name in user_text:
                matched_info.append(detail)

        info_str = "\n".join(matched_info) if matched_info else "정보 없음"

        system_role = f"""
Supplement tracker.
Refer to the master list if available:
{info_str}

Output JSON: {{
  "supplements": ["이름1", "이름2"],
  "count": int,
  "details": "{info_str}",
  "summary": "영양제 X종 복용 (함량 포함)"
}}
"""
    elif "섭취" in category:
        system_role = """
Nutritionist. Estimate calories/macros based on standard Korean servings.
Output JSON: {"calories": int, "food_name": "str", "macros": "탄:xx 단:xx 지:xx", "summary": "str"}
"""
    elif "음주" in category:
        system_role = """
Alcohol consumption tracker.
[Conversion] 소주 1병=7잔, 맥주 1캔=1.5잔, 와인 1병=5잔
Output JSON: {
  "alcohol_type": "소주/맥주/와인",
  "standard_drinks": int,
  "calories": int,
  "summary": "소주 2병 (14잔, 1400kcal)"
}
"""
    elif "회복" in category:
        system_role = """
Recovery activity tracker.
[Sauna] 1 cycle = 20분 (사우나10분+샤워2분+cold plunge 3분+휴식5분)
Output JSON: {
  "activity_type": "sauna/meditation/massage",
  "cycles": int (사우나만),
  "duration": int,
  "summary": "사우나 2사이클 (36분)"
}
"""
    elif "노트" in category:
        system_role = """
Health condition analyzer.
Output JSON: {
  "symptoms": ["증상1"],
  "stress_level": "high/medium/low",
  "summary": "요약"
}
"""
    else:
        system_role = "Health Logger. Output JSON with summary field."

    prompt = f"User logged [{category}] at [{log_time}]. Text: '{user_text}'. {system_role} Return ONLY JSON."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"summary": user_text, "error": str(e)}


def _normalize_food_key(text):
    t = str(text or "").lower()
    t = re.sub(r"[^0-9a-z가-힣]", "", t)
    return t


def _to_float(v, default=0.0):
    try:
        return float(v)
    except:
        return float(default)


@st.cache_data(ttl=3600 * 12)
def load_food_nutrition_index():
    cols = ["name", "kcal", "protein", "fat", "carbs"]
    try:
        df = pd.read_csv("food_db.csv", usecols=cols)
    except Exception:
        return {"exact": {}, "token": {}}

    if df.empty:
        return {"exact": {}, "token": {}}

    exact_sum = {}
    token_sum = {}

    for _, r in df.iterrows():
        name = str(r.get("name", "") or "").strip()
        if not name:
            continue
        kcal = _to_float(r.get("kcal", 0))
        protein = _to_float(r.get("protein", 0))
        fat = _to_float(r.get("fat", 0))
        carbs = _to_float(r.get("carbs", 0))
        payload = {"kcal": kcal, "protein": protein, "fat": fat, "carbs": carbs}

        # exact key
        exact_key = _normalize_food_key(name.replace("_", " "))
        if exact_key:
            s = exact_sum.get(exact_key, {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "n": 0})
            s["kcal"] += payload["kcal"]
            s["protein"] += payload["protein"]
            s["fat"] += payload["fat"]
            s["carbs"] += payload["carbs"]
            s["n"] += 1
            exact_sum[exact_key] = s

        # token keys
        toks = re.findall(r"[0-9a-zA-Z가-힣]+", name.replace("_", " "))
        for tok in toks:
            tk = _normalize_food_key(tok)
            if len(tk) < 2 or tk in NUTRITION_STOPWORDS:
                continue
            s = token_sum.get(tk, {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "n": 0})
            s["kcal"] += payload["kcal"]
            s["protein"] += payload["protein"]
            s["fat"] += payload["fat"]
            s["carbs"] += payload["carbs"]
            s["n"] += 1
            token_sum[tk] = s

    def _avg_map(src):
        out = {}
        for k, s in src.items():
            n = max(1, int(s.get("n", 1)))
            out[k] = {
                "kcal": s["kcal"] / n,
                "protein": s["protein"] / n,
                "fat": s["fat"] / n,
                "carbs": s["carbs"] / n,
            }
        return out

    return {"exact": _avg_map(exact_sum), "token": _avg_map(token_sum)}


def _split_food_items(text):
    raw = str(text or "")
    parts = re.split(r",|/|\\n|\\+| 및 | 그리고 ", raw)
    return [p.strip() for p in parts if str(p or "").strip()]


def _extract_multiplier(item_text, matched_token):
    t = str(item_text or "")
    frac = re.search(r"(\d+)\s*/\s*(\d+)", t)
    if frac:
        den = max(1, int(frac.group(2)))
        return float(int(frac.group(1)) / den)

    m = re.search(r"(\d+(?:\.\d+)?)\s*(인분|그릇|공기|마리|캔|병|잔|개|세트|조각|컵)", t)
    if m:
        return max(0.1, float(m.group(1)))

    if ("반" in t) and not re.search(r"\d", t):
        return 0.5

    ml = re.search(r"(\d+(?:\.\d+)?)\s*ml", t, flags=re.IGNORECASE)
    if ml and (matched_token in BEVERAGE_TOKENS):
        return max(0.1, float(ml.group(1)) / 250.0)

    return 1.0


def estimate_nutrition_from_text(user_text):
    idx = load_food_nutrition_index()
    token_map = idx.get("token", {}) or {}
    exact_map = idx.get("exact", {}) or {}
    items = _split_food_items(user_text)

    total = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    matched_tokens = []

    alias_keys = sorted(FOOD_ALIAS_MAP.keys(), key=len, reverse=True)

    for item in items:
        norm = _normalize_food_key(item)
        if not norm:
            continue

        chosen_token = None
        chosen = None

        # 0) explicit fallback profile first (high precision for frequent foods)
        for fk in sorted(NUTRITION_FALLBACK_PROFILE.keys(), key=len, reverse=True):
            if _normalize_food_key(fk) in norm:
                chosen_token = _normalize_food_key(fk)
                chosen = dict(NUTRITION_FALLBACK_PROFILE[fk])
                break

        # 1) exact match
        if (chosen is None) and (norm in exact_map):
            chosen_token = norm
            chosen = exact_map[norm]

        # 2) alias match
        if chosen is None:
            for ak in alias_keys:
                if _normalize_food_key(ak) in norm:
                    alias_target = _normalize_food_key(FOOD_ALIAS_MAP[ak])
                    if alias_target in token_map:
                        chosen_token = alias_target
                        chosen = token_map[alias_target]
                        break

        # 3) token match
        if chosen is None:
            toks = re.findall(r"[0-9a-zA-Z가-힣]+", item)
            toks = [(_normalize_food_key(x), len(_normalize_food_key(x))) for x in toks]
            toks = [x for x in toks if x[0] and len(x[0]) >= 2 and x[0] not in NUTRITION_STOPWORDS]
            toks.sort(key=lambda x: x[1], reverse=True)
            for tk, _ in toks:
                if tk in token_map:
                    chosen_token = tk
                    chosen = token_map[tk]
                    break

        if chosen is None:
            continue

        mult = _extract_multiplier(item, chosen_token)
        total["kcal"] += chosen["kcal"] * mult
        total["protein"] += chosen["protein"] * mult
        total["fat"] += chosen["fat"] * mult
        total["carbs"] += chosen["carbs"] * mult
        matched_tokens.append(chosen_token)

    return {
        "calories": int(round(total["kcal"])),
        "protein": round(total["protein"], 1),
        "fat": round(total["fat"], 1),
        "carbs": round(total["carbs"], 1),
        "matched": matched_tokens,
    }


def parse_log_quick(category, user_text, log_time):
    """
    Tab3 저장 성능 개선용 로컬 파서.
    OpenAI 호출 없이 즉시 JSON을 만들어 append_row 지연을 줄인다.
    """
    txt = (user_text or "").strip()
    if not txt:
        return {"summary": ""}

    def _first_int(pattern, default=0):
        m = re.search(pattern, txt, flags=re.IGNORECASE)
        return int(m.group(1)) if m else default

    def _first_float(pattern, default=0.0):
        m = re.search(pattern, txt, flags=re.IGNORECASE)
        return float(m.group(1)) if m else default

    if "섭취" in category:
        est = estimate_nutrition_from_text(txt)
        kcal = int(est.get("calories", 0) or 0)
        carbs = float(est.get("carbs", 0.0) or 0.0)
        protein = float(est.get("protein", 0.0) or 0.0)
        fat = float(est.get("fat", 0.0) or 0.0)
        if kcal <= 0:
            # fallback heuristic (DB 매칭 실패 시)
            kcal = _first_int(r"(\d{2,4})\s*kcal", 0)
            if kcal <= 0:
                kcal_table = {
                    "샐러드": 350,
                    "김밥": 450,
                    "햄버거": 650,
                    "치킨": 800,
                    "라면": 500,
                    "떡볶이": 550,
                    "피자": 750,
                    "밥": 550,
                }
                for k, v in kcal_table.items():
                    if k in txt:
                        kcal = v
                        break
        macros = ""
        if carbs > 0 or protein > 0 or fat > 0:
            macros = f"탄:{carbs:.1f} 단:{protein:.1f} 지:{fat:.1f}"
        return {
            "calories": int(kcal),
            "food_name": txt[:40],
            "macros": macros,
            "carbs": carbs,
            "protein": protein,
            "fat": fat,
            "summary": f"섭취 기록 (약 {int(kcal)}kcal)" if kcal > 0 else "섭취 기록",
        }

    if "운동" in category:
        mins = _first_int(r"(\d{1,3})\s*(분|min|minute)", 0)
        if mins <= 0:
            km = _first_float(r"(\d{1,2}(?:\.\d+)?)\s*km", 0.0)
            if km > 0:
                mins = int(max(10, round(float(km) * 7)))
        if mins <= 0:
            mins = 20
        return {
            "activity_type": "exercise",
            "duration": int(mins),
            "time": int(mins),
            "summary": f"운동 기록 ({int(mins)}분)",
        }

    if "음주" in category:
        soju = _first_int(r"소주\s*(\d+)\s*병", 0)
        beer_can = _first_int(r"맥주\s*(\d+)\s*(캔|병)", 0)
        beer_glass = _first_int(r"맥주\s*(\d+)\s*잔", 0)
        wine = _first_int(r"와인\s*(\d+)\s*병", 0)
        drinks = soju * 7 + int(beer_can * 1.5) + beer_glass + wine * 5
        calories = int(drinks * 100)
        return {
            "alcohol_type": "기타",
            "standard_drinks": int(drinks),
            "calories": int(calories),
            "summary": f"음주 기록 ({int(drinks)}잔, 약 {int(calories)}kcal)",
        }

    if "영양제" in category:
        known = ["마그네슘", "밀크시슬", "락토핏", "오메가3", "비타민D3"]
        supplements = [k for k in known if k in txt]
        return {
            "supplements": supplements,
            "count": int(len(supplements)),
            "details": ", ".join(supplements) if supplements else txt[:60],
            "summary": f"영양제 {len(supplements)}종 복용" if supplements else "영양제 복용",
        }

    if "회복" in category:
        mins = _first_int(r"(\d{1,3})\s*(분|min|minute)", 0)
        cycles = _first_int(r"(\d{1,2})\s*(세트|사이클)", 0)
        if mins <= 0 and cycles > 0:
            mins = cycles * 20
        return {
            "activity_type": "recovery",
            "cycles": int(cycles),
            "duration": int(mins),
            "summary": f"회복 기록 ({int(mins)}분)" if mins > 0 else "회복 기록",
        }

    if "노트" in category:
        return {
            "symptoms": [],
            "stress_level": "medium",
            "summary": txt[:120],
        }

    if "DF" in str(category).upper():
        marks = []
        for m in re.finditer(r"(?<![A-Z0-9])DF\s*([1-5])(?!\d)", txt.upper()):
            marks.append(f"DF{int(m.group(1))}")
        marks = sorted(set(marks))
        return {
            "activity_type": "daily_five_completion",
            "df_marks": marks,
            "count": int(len(marks)),
            "summary": f"Daily Five 수행 체크 ({', '.join(marks)})" if marks else "Daily Five 체크 기록",
        }

    return {"summary": txt[:120]}


# ==========================================
# [메인 UI]
# ==========================================
_rollover_updates = run_daily_sprint_rollover_once()
if DEBUG_MODE and _rollover_updates > 0:
    print(f"sprint rollover updated rows: {_rollover_updates}")
_schema_synced = run_sheet_schema_sync_once()
if DEBUG_MODE and _schema_synced:
    print("sprint sheet schema synced")

_dashboard_subpage = get_dashboard_subpage()
if _dashboard_subpage == "makjang":
    st.markdown("### 📉 일상 막장 지수 상세")
    c_back, c_empty = st.columns([0.18, 0.82])
    with c_back:
        if st.button("← 대시보드", width="stretch"):
            set_dashboard_subpage("")
            st.rerun()
    with c_empty:
        st.caption("최근 3일 점수 산정 근거")

    try:
        date_key_mj = get_mission_date_key()
        df_action_mj = pd.DataFrame(get_db_connection("Action_Log").get_all_records())
        mj_detail = compute_makjang_3day_score(date_key_mj, df_action_mj)
        st.metric("일상 막장 지수", f"{int(mj_detail.get('score', 0))}/100")
        render_makjang_score_drilldown(mj_detail)
    except Exception as e:
        st.error(f"막장지수 상세 로딩 실패: {e}")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📊 대시보드", "🎯 Sprint", "📝 기록하기", "🏎️ Pit Wall"])

# [TAB 1] Dashboard
with tab1:
    st.markdown("### 📡 Real-time Bio-Stat")
    try:
        sh_h = get_db_connection("Health_Log")
        sh_a = get_db_connection("Action_Log")
        df_h = pd.DataFrame(sh_h.get_all_records())
        df_a = pd.DataFrame(sh_a.get_all_records())

        if not df_h.empty:
            now_kst = get_current_kst()
            date_key = get_mission_date_key()

            # 1) 캘린더 -> 슬롯 생성
            cal_evts = get_today_calendar_events(date_key)
            available_slots = build_available_slots(date_key, cal_evts)

            # 2) 오늘 액션 로그
            today_logs = df_a[df_a['Date'] == date_key]
            today_acts = [f"[{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in today_logs.iterrows()]

            # 3) Health 최신값 (w_c 먼저!)
            last_h = df_h.iloc[-1]
            hrv_c = float(last_h.get('HRV', 0))
            rhr_c = float(last_h.get('RHR', 0))
            w_c   = float(last_h.get('Weight', 0))

            # 4) trend_weight
            trend = get_or_create_daily_trend(date_key, df_h)
            trend_weight = trend["trend_weight"] if trend else None

            # 5) xC 계산
            xc = None
            sprint = None
            progress = None
            try:
                sprint = get_active_sprint()
                if sprint:
                    progress = calculate_sprint_progress(sprint, w_c, trend_weight=trend_weight)
                    daily_state = build_daily_state(
                        date_key=date_key,
                        now_kst=now_kst,
                        df_action=df_a,
                        cal_evts=cal_evts,
                        available_slots=available_slots,
                        sprint_progress=progress,
                        trend_weight=trend_weight,
                        current_hrv=hrv_c,
                        current_rhr=rhr_c,
                    )
                    xc = get_or_create_daily_xc(date_key, sprint, daily_state)
            except Exception as e:
                print("xC error:", e)
                xc = None

            
            mission = calculate_mission_status(w_c)
            
            mj = compute_makjang_3day_score(date_key, df_a)
            mj_score = mj["score"]

            st.caption(f"🕒 마지막 업데이트: {last_h.get('Date','Unknown')}")

            hrv_icon = "🟢" if hrv_c >= 45 else "🔴"
            rhr_icon = "🟢" if rhr_c <= 65 else "🔴"

            dashboard_html = f"""
<div style="display: flex; gap: 8px; margin-bottom: 20px; width: 100%;">
<div style="flex: 1; background: #FFFFFF; padding: 12px 5px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="font-size: 16px; color: #64748B; font-weight: 600; margin-bottom: 4px;">HRV</div>
<div style="font-size: 33px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{hrv_c:.1f}</div>
<div style="font-size: 11px; color: #64748B;">{hrv_icon} (평균:40)</div>
</div>
<div style="flex: 1; background: #FFFFFF; padding: 12px 5px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="font-size: 16px; color: #64748B; font-weight: 600; margin-bottom: 4px;">RHR</div>
<div style="font-size: 33px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{rhr_c:.1f}</div>
<div style="font-size: 11px; color: #64748B;">{rhr_icon} (평균:65)</div>
</div>
<a href="?dash=makjang" style="flex:1; display:flex; align-items:stretch; text-decoration:none; color:inherit; -webkit-tap-highlight-color: transparent;">
<div style="width:100%; min-height:100%; background: #FFFFFF; padding: 14px 8px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor:pointer;">
<div style="font-size: 16px; color: #64748B; font-weight: 600; margin-bottom: 4px;">일상 막장 지수</div>
<div style="font-size: 33px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{mj_score}</div>
<div style="font-size: 11px; color: #64748B;">/100 </div>
</div>
</a>
</div>
</div>
"""
            st.markdown(dashboard_html, unsafe_allow_html=True)
            ck_res = None

            if mj_score >= 60:
                st.error(f"🚨 일상 막장 지수 {mj_score}/100 - 최근 3일이 무너지고 있습니다. 오늘은 차단 모드로 갑니다.")


            df_h['Date_Clean'] = pd.to_datetime(df_h['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            today_h = df_h[df_h['Date_Clean'] == date_key]

            if not today_h.empty:
                m_row = today_h.iloc[0]
                m_ctx = prepare_full_context(df_h, df_a, float(m_row['Weight']), True)

                # checkin은 UI 참고용 텍스트 유지(여기까지는 트러블 포인트 아님)
                cal_txt = "\n".join(
                    [f"[운동]{e['start_dt'].strftime('%H:%M')} {e['title']}" for e in cal_evts['Sports']] +
                    [f"[일정]{e['start_dt'].strftime('%H:%M')} {e['title']}" for e in cal_evts['Termin']]
                ) or "None"

                ck_res = load_checkin_cache(date_key)
                if not ck_res:
                    with st.spinner("Analyzing..."):
                        ck_res = ai_generate_daily_checkin(
                            date_key,
                            float(m_row['HRV']),
                            float(m_row['RHR']),
                            float(m_row['Weight']),
                            m_ctx,
                            cal_txt
                        )
                        ck_res["generated_at_kst"] = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
                        ck_res["date_key"] = date_key
                        save_checkin_cache(date_key, ck_res)
                        clear_old_caches()

                generated_at = (ck_res or {}).get("generated_at_kst", "-")
                checkin_lbl = f"{generated_at} 생성"

                st.markdown(f"""
                <div style="display:flex; align-items:baseline; gap:8px; margin-bottom:10px;">
                <h3 style="margin:0;">☀️ Daily Check-in</h3>
                <span style="font-size:11px; color:#94a3b8;">({checkin_lbl})</span>
                </div>
                """, unsafe_allow_html=True)

                try:
                    sprint = get_active_sprint()
                    if sprint:
                        if not load_dailyfive_cache(date_key, sprint['sprint_id']):
                            ywr = summarize_yesterday_workout_review(df_a, date_key)
                            five = ai_generate_daily_five(
                                date_key,
                                sprint,
                                {'weight': float(m_row['Weight']), 'hrv': float(m_row['HRV']), 'rhr': float(m_row['RHR'])},
                                {'available_slots': available_slots, 'yesterday_workout_review': ywr}  # ✅ [FIX]
                            )
                            if five:
                                save_dailyfive_cache(date_key, sprint['sprint_id'], five)
                except:
                    pass

                icon = {"Green":"🟢", "Red":"🔴"}.get((ck_res or {}).get("condition_signal"), "🟡")
                headline = (ck_res or {}).get("headline") or "오늘 컨디션 체크"
                headline_reason = (ck_res or {}).get("headline_reason") or ""

                st.subheader(f"{icon} {headline}")

                with st.container(border=True):
                    if headline_reason:
                        st.caption(f"근거: {headline_reason}")
                    st.markdown(f"**🕵️ 분석:** {(ck_res or {}).get('analysis', '-')}")

                st.write(""); st.markdown("**🎯 오늘의 전략**")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"""<div class="strategy-box workout-box"><span class="strategy-title">💪 운동</span>{ck_res.get('mission_workout', "-")}</div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="strategy-box diet-box"><span class="strategy-title">🥗 식단</span>{ck_res.get('mission_diet', "-")}</div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class="strategy-box recovery-box"><span class="strategy-title">🔋 회복</span>{ck_res.get('mission_recovery', "-")}</div>""", unsafe_allow_html=True)
            else:
                st.info(f"💤 데이터 대기 중 ({date_key})")

            st.write("")
            rt_ctx = prepare_full_context(df_h, df_a, w_c, False)
            wrapup_kind = resolve_wrapup_kind(date_key, now_kst)
            if wrapup_kind:
                if wrapup_kind == "weekly":
                    wrapup_payload = build_weekly_wrapup_payload(
                        date_key=date_key,
                        now_kst=now_kst,
                        df_health=df_h,
                        df_action=df_a,
                        current_weight=w_c,
                        current_hrv=hrv_c,
                        current_rhr=rhr_c,
                        sprint=sprint,
                        sprint_progress=progress,
                    )
                else:
                    wrapup_payload = build_daily_wrapup_payload(
                        date_key=date_key,
                        now_kst=now_kst,
                        df_health=df_h,
                        df_action=df_a,
                        current_weight=w_c,
                        current_hrv=hrv_c,
                        current_rhr=rhr_c,
                        cal_evts=cal_evts,
                        available_slots=available_slots,
                        sprint=sprint,
                        sprint_progress=progress,
                        trend_weight=trend_weight,
                        xc=xc,
                    )
                wrapup = get_or_create_wrapup(
                    kind=wrapup_kind,
                    cache_key=date_key,
                    payload=wrapup_payload,
                )
                render_wrapup_block(wrapup_kind, wrapup, xc=xc)
            else:
                # ✅ [FIX] Action Plan 호출: calendar를 logs에 섞어 넣지 말고 slots로 전달
                ap = ai_generate_action_plan(
                    hrv_c, rhr_c, w_c,
                    rt_ctx,
                    today_acts,
                    available_slots
                )

                st.markdown(f"""<h3 style="margin-bottom: 10px;">⚡ Action Plan <span class="time-badge">{ap.get('generated_at', now_kst.strftime('%H:%M'))} 기준</span></h3>""", unsafe_allow_html=True)
                if xc and (xc.get("xc_value_kg") is not None):
                    st.caption(f"🎯 xC(오늘 기대 변화량): {float(xc.get('xc_value_kg')):.1f}kg")

                with st.container(border=True):
                    st.markdown(f"**📊 현재 상황:** {ap.get('current_analysis')}")
                    st.markdown(f"**🚀 실질적 조언:**\n{ap.get('next_actions', '').replace(chr(10), chr(10)*2)}")
                    if ap.get('warnings'):
                        st.error(f"⚠️ {ap['warnings']}")
        else:
            st.warning("No Data")
    except Exception as e:
        st.error(f"Error: {e}")


# =========================================================
# [TAB 2] 🎯 Sprint
# =========================================================
with tab2:
    with st.spinner("로딩 중..."):
        try:
            @st.cache_data(ttl=300)
            def get_current_health_data():
                sh_h = get_db_connection("Health_Log")
                df_h = pd.DataFrame(sh_h.get_all_records())
                if df_h.empty:
                    return None
                last = df_h.iloc[-1]
                return {
                    'weight': float(last['Weight']),
                    'hrv': float(last.get('HRV', 0)),
                    'rhr': float(last.get('RHR', 0))
                }

            health_data = get_current_health_data()

            if not health_data:
                st.warning("건강 데이터 없음")
            else:
                current_weight = health_data['weight']
                current_hrv = health_data['hrv']
                current_rhr = health_data['rhr']

                sprint = get_active_sprint()

                if not sprint:
                    st.info("🎯 진행 중인 Sprint가 없습니다")
                else:
                    st.markdown(f"### 🎯 Sprint: {sprint['name']}")

                    date_key = get_mission_date_key()

                    sh_h = get_db_connection("Health_Log")
                    df_h = pd.DataFrame(sh_h.get_all_records())

                    trend = get_or_create_daily_trend(date_key, df_h)
                    trend_weight = trend["trend_weight"] if trend else None
                    
                    cal_events = get_today_calendar_events(date_key)
                    available_slots = build_available_slots(date_key, cal_events)

                    progress = calculate_sprint_progress(sprint, current_weight, trend_weight=trend_weight)
                    df_action_tab2 = pd.DataFrame(get_db_connection("Action_Log").get_all_records())
                    daily_state = build_daily_state(
                        date_key=date_key,
                        now_kst=get_current_kst(),
                        df_action=df_action_tab2,
                        cal_evts=cal_events,
                        available_slots=available_slots,
                        sprint_progress=progress,
                        trend_weight=trend_weight,
                        current_hrv=current_hrv,
                        current_rhr=current_rhr,
                    )
                    xc = get_or_create_daily_xc(date_key, sprint, daily_state)
                    xc_value = xc.get("xc_value_kg") if xc else None

                    if progress:
                        with st.container(border=True):
                            day = progress['day']
                            total = progress['sprint']['duration_days']
                            progress_pct = min(100.0, max(0.0, float(progress.get('progress_pct', 0.0))))

                            st.caption(f"Day {day}/{total}")
                            st.progress(progress_pct / 100)

                            st.write("")

                            status_html = f"""
                            <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                            <div style="flex: 1; background: #FFFFFF; padding: 12px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center;">
                            <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">시작</div>
                            <div style="font-size: 22px; font-weight: 900; color: #1A2B4D;">{progress['weight_start']:.1f}kg</div>
                            </div>
                            <div style="flex: 1; background: #FFFFFF; padding: 12px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center;">
                            <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">현재</div>
                            <div style="font-size: 22px; font-weight: 900; color: #1A2B4D;">{progress['weight_current']:.1f}kg</div>
                            <div style="font-size: 11px; color: #3B82F6; margin-top: 4px;">{progress['weight_current'] - progress['weight_start']:.1f}kg</div>
                            </div>
                            <div style="flex: 1; background: #FFFFFF; padding: 12px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center;">
                            <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">목표</div>
                            <div style="font-size: 22px; font-weight: 900; color: #1A2B4D;">{progress['weight_target']:.1f}kg</div>
                            </div>
                            </div>
                            """
                            st.markdown(status_html, unsafe_allow_html=True)

                            delta = progress['weight_delta']
                            pace_status = progress['pace_status']

                            # ✅ [FIX] 메시지/남은kg 계산을 pace_weight(=trend 우선) 기준으로 통일
                            remaining = progress['pace_weight'] - progress['weight_target']

                            if pace_status == 'ahead':
                                st.success(f"🟢 목표보다 {abs(delta):.1f}kg 앞서감! ({remaining:.1f}kg 남음)")
                            
                            elif pace_status == 'behind':
                                st.markdown(
                                    f"""
                                    <div style="
                                        background: #EAF2FF;   /* 옅은 파랑 */
                                        border: 1px solid #B6D0FF;
                                        padding: 12px 14px;
                                        border-radius: 12px;
                                        margin: 6px 0 8px 0;
                                    ">
                                    <div style="
                                        color: #DC2626;      /* 빨강 글씨 */
                                        font-weight: 900;
                                        font-size: 16px;
                                        line-height: 1.35;
                                    ">
                                        🟡 목표보다 {abs(delta):.1f}kg 느림 ({remaining:.1f}kg 남음)
                                    </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.caption(f"💪 따라잡으려면: 하루 평균 -{progress['required_daily_pace']:.2f}kg 필요")

                            else:
                                st.info(f"🎯 완벽한 페이스! ({remaining:.1f}kg 남음)")

                            linear_expected = progress["weight_expected"]

                            st.caption(f"📏 기계식 페이스 {linear_expected:.2f}kg")

                            if trend_weight is not None:
                                st.caption(f"📈 추세체중(EWMA) {trend_weight:.2f}kg ")
                            else:
                                st.caption("📈 추세체중(EWMA) 없음 → 현재체중 기준")

                            if xc_value is not None:
                                st.caption(f"🎯 xC(오늘 기대 변화량) {xc_value:.1f}kg")
                            else:
                                st.caption("🎯 xC 계산값 없음")


                    st.markdown("### 💪🏽 Sprint: Daily Five")
                    st.caption(f"🕐 {date_key} 05:00 생성")

                    cal_events = get_today_calendar_events(date_key)
                    available_slots = build_available_slots(date_key, cal_events)

                    cached_five = load_dailyfive_cache(date_key, sprint['sprint_id'])
                    if not cached_five:
                        daily_five = ai_generate_daily_five(
                            date_key,
                            sprint,
                            {'weight': current_weight, 'hrv': current_hrv, 'rhr': current_rhr},
                            {
                                'available_slots': available_slots,
                                'yesterday_workout_review': summarize_yesterday_workout_review(df_action_tab2, date_key),
                            }
                        )
                        if daily_five:
                            save_dailyfive_cache(date_key, sprint['sprint_id'], daily_five)
                            clear_old_caches()
                    else:
                        daily_five = cached_five

                    if daily_five and 'tasks' in daily_five:

                        if daily_five.get('daily_message'):
                            urgency = daily_five.get('urgency_level', 'medium')
                            if urgency == 'high':
                                st.error(daily_five['daily_message'])
                            elif urgency == 'low':
                                st.success(daily_five['daily_message'])
                            else:
                                st.info(daily_five['daily_message'])

                        st.write("")

                        for task in daily_five['tasks']:
                            priority = task.get('priority', 5)
                            if priority <= 2:
                                border_color = "#EF4444"
                                icon = "🔥"
                            else:
                                border_color = "#3B82F6"
                                icon = "⚡"
                            bg_color = "#FFFFFF"

                            task_html = f"""
                            <div style="background: {bg_color}; padding: 16px; border-radius: 12px; border-left: 4px solid {border_color}; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                            <div style="display: flex; align-items: flex-start; gap: 12px;">
                            <div style="font-size: 24px; line-height: 1;">{icon}</div>
                            <div style="flex: 1;">
                            <div style="font-weight: 700; color: #1A2B4D; font-size: 16px; margin-bottom: 6px;">{task['title']}</div>
                            <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;">{task['description']}</div>
                            <div style="font-size: 12px; color: #94A3B8; font-style: italic;">💡 {task['why']}</div>
                            </div>
                            </div>
                            </div>
                            """
                            st.markdown(task_html, unsafe_allow_html=True)

                    else:
                        st.warning("데일리 파이브 생성 실패")

                    st.divider()

                    st.markdown("### 📅 앞으로의 계획")
                    st.caption("현재 페이스 유지 시 예상")

                    with st.expander("내일 예상"):
                        st.info("내일 아침 5시에 생성됩니다")

                    with st.expander("모레 예상"):
                        st.info("모레 아침 5시에 생성됩니다")

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())


# =========================================================
# [TAB 3] 기록하기 (원본 유지)
# =========================================================
with tab3:
    now_kst = get_current_kst()
    today_str = now_kst.strftime('%Y-%m-%d')

    st.markdown("### 📊 오늘의 기록")

    @st.cache_data(ttl=300)
    def get_today_summary(date_str):
        cal = 0
        mins = 0
        try:
            sh_a = get_db_connection("Action_Log")
            df_a = pd.DataFrame(sh_a.get_all_records())

            if not df_a.empty:
                df_a["Date_Clean"] = pd.to_datetime(df_a["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
                today_df = df_a[df_a["Date_Clean"] == date_str]

                for _, r in today_df.iterrows():
                    try:
                        js = json.loads(r.get("AI_Analysis_JSON", "{}") or "{}")
                        cat = str(r.get("Category", ""))
                        if "섭취" in cat:
                            cal += int(js.get("calories", 0) or 0)
                        if "운동" in cat:
                            mins += int(js.get("time", js.get("duration", 0)) or 0)
                    except:
                        pass
        except:
            pass

        return {"calories": cal, "minutes": mins}

    summary = get_today_summary(today_str)

    summary_html = f"""
    <div style="display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap;">
      <div style="flex:1; min-width:140px; background:#FFFFFF; padding:14px 8px; border-radius:12px; border:1px solid #E2E8F0; text-align:center; box-shadow:0 1px 2px rgba(0,0,0,0.05);">
        <div style="font-size:12px; color:#64748B; font-weight:600; margin-bottom:6px;">섭취 칼로리</div>
        <div style="font-size:22px; font-weight:900; color:#1A2B4D;">{summary['calories']} kcal</div>
      </div>

      <div style="flex:1; min-width:140px; background:#FFFFFF; padding:14px 8px; border-radius:12px; border:1px solid #E2E8F0; text-align:center; box-shadow:0 1px 2px rgba(0,0,0,0.05);">
        <div style="font-size:12px; color:#64748B; font-weight:600; margin-bottom:6px;">운동 시간</div>
        <div style="font-size:22px; font-weight:900; color:#1A2B4D;">{summary['minutes']} 분</div>
      </div>

      <div style="flex:1; min-width:140px; background:#FFFFFF; padding:14px 8px; border-radius:12px; border:1px solid #E2E8F0; text-align:center; box-shadow:0 1px 2px rgba(0,0,0,0.05);">
        <div style="font-size:12px; color:#64748B; font-weight:600; margin-bottom:6px;">Dry Feb</div>
        <div style="font-size:22px; font-weight:900; color:#1A2B4D;">{now_kst.day}/28일</div>
      </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    st.divider()

    st.markdown("### ✍️ 기록하기")

    default_date = now_kst.date()
    default_hour = now_kst.hour
    default_minute = (now_kst.minute // 5) * 5

    categories = ["섭취", "운동", "음주", "영양제", "회복", "노트", "DF"]

    with st.container(border=True):
        with st.form("log_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1.2, 0.9, 0.9, 1.2])

            with c1:
                log_date = st.date_input("날짜", value=default_date, key="log_date_widget", label_visibility="collapsed")
            with c2:
                log_hour = st.selectbox("시", options=list(range(0, 24)), index=default_hour, key="log_hour_widget", label_visibility="collapsed")
            with c3:
                minute_options = list(range(0, 60, 5))
                log_minute = st.selectbox("분", options=minute_options, index=minute_options.index(default_minute) if default_minute in minute_options else 0, key="log_minute_widget", label_visibility="collapsed")
            with c4:
                log_category = st.selectbox("카테고리", options=categories, index=0, key="log_category_widget", label_visibility="collapsed")

            log_time = f"{int(log_hour):02d}:{int(log_minute):02d}"

            log_text = st.text_area(
                "내용",
                placeholder="예: 닭가슴살 샐러드 / 러닝 5km / 맥주 2잔 / SAT 복용 / 사우나 2세트 / 야근으로 운동 못함",
                height=120,
                key="log_text_widget",
                label_visibility="collapsed",
            )

            submitted = st.form_submit_button("🚀 저장", width="stretch")

        if submitted:
            text_clean = (log_text or "").strip()
            if not text_clean:
                st.error("⚠️ 내용을 입력해주세요.")
            else:
                try:
                    with st.spinner("저장 중..."):
                        parsed = parse_log_quick(log_category, text_clean, log_time)
                        get_db_connection("Action_Log").append_row([
                            log_date.strftime("%Y-%m-%d"),
                            log_time,
                            log_category,
                            text_clean,
                            json.dumps(parsed, ensure_ascii=False),
                            ""
                        ])
                        # DF 완료 마커 입력 시 Daily Five 완료율/시트 동기화를 즉시 반영
                        try:
                            cat_up = str(log_category or "").upper().strip()
                            txt_up = str(text_clean or "").upper()
                            if (cat_up == "DF") or ("DF5:" in txt_up):
                                sprint_now = get_active_sprint()
                                if sprint_now:
                                    df_action_now = pd.DataFrame(get_db_connection("Action_Log").get_all_records())
                                    date_candidates = []
                                    d_log = log_date.strftime("%Y-%m-%d")
                                    d_mission = get_mission_date_key()
                                    for d in [d_log, d_mission]:
                                        if d not in date_candidates:
                                            date_candidates.append(d)
                                    for dk in date_candidates:
                                        get_daily_five_completion(
                                            dk,
                                            sprint_now["sprint_id"],
                                            df_action_now,
                                        )
                        except Exception as _sync_e:
                            print("df completion immediate sync error:", _sync_e)
                        try:
                            d_log = log_date.strftime("%Y-%m-%d")
                            d_mission = get_mission_date_key()
                            invalidate_realtime_plan_cache(d_log)
                            if d_mission != d_log:
                                invalidate_realtime_plan_cache(d_mission)
                            get_today_summary.clear()
                        except Exception as _cache_e:
                            print("realtime cache invalidation error:", _cache_e)
                    st.success("✅ 저장 완료!")
                except Exception as e:
                    st.error(f"저장 실패: {e}")

    st.divider()

    with st.expander("📂 아카이브", expanded=False):

        @st.cache_data(ttl=300)
        def load_archive_data():
            sh_a = get_db_connection("Action_Log")
            return pd.DataFrame(sh_a.get_all_records())

        try:
            df = load_archive_data()
            if df.empty:
                st.info("아직 기록이 없습니다.")
            else:
                view_cols = [c for c in ["Date", "Action_Time", "Category", "User_Input"] if c in df.columns]
                st.dataframe(
                    df.iloc[::-1][view_cols].head(100),
                    width="stretch",
                    hide_index=True,
                )
        except Exception as e:
            st.error(f"로딩 실패: {e}")


# =========================================================
# [TAB 4] Pit Wall
# =========================================================
with tab4:
    st.markdown("## 🏎️ The Pit Wall")
    st.info("개발자 도구 영역")

    st.write("server now:", datetime.now())
    st.write("kst now:", get_current_kst())

    _s = None
    try:
        _s = get_active_sprint()
    except:
        _s = None

    if _s:
        st.write("sprint start:", _s['start_date'])
    else:
        st.write("sprint start:", "(no active sprint)")

    st.write("debug mode:", DEBUG_MODE)

    if DEBUG_MODE:
        try:
            date_key_dbg = get_mission_date_key()
            now_kst_dbg = get_current_kst()
            df_action_dbg = pd.DataFrame(get_db_connection("Action_Log").get_all_records())
            cal_dbg = get_today_calendar_events(date_key_dbg)
            slots_dbg = build_available_slots(date_key_dbg, cal_dbg)
            sprint_dbg = get_active_sprint()
            trend_dbg = None
            progress_dbg = None
            if sprint_dbg:
                df_health_dbg = pd.DataFrame(get_db_connection("Health_Log").get_all_records())
                trend_obj_dbg = get_or_create_daily_trend(date_key_dbg, df_health_dbg)
                trend_dbg = trend_obj_dbg.get("trend_weight") if trend_obj_dbg else None
                current_w_dbg = float(df_health_dbg.iloc[-1].get("Weight", 0)) if not df_health_dbg.empty else 0.0
                progress_dbg = calculate_sprint_progress(sprint_dbg, current_w_dbg, trend_weight=trend_dbg)

            ds_dbg = build_daily_state(
                date_key=date_key_dbg,
                now_kst=now_kst_dbg,
                df_action=df_action_dbg,
                cal_evts=cal_dbg,
                available_slots=slots_dbg,
                sprint_progress=progress_dbg,
                trend_weight=trend_dbg,
            )
            st.write("daily_state preview:")
            st.json(ds_dbg)
        except Exception as e:
            st.warning(f"debug daily_state error: {e}")

    if st.button("🔄 전체 캐시 클리어"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("캐시 클리어 완료!")
