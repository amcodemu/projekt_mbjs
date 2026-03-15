import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import json
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import os
import time as pytime
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
    :root {
        --mb-bg-0: #070d18;
        --mb-bg-1: #0a1324;
        --mb-bg-2: #0d1627;
        --mb-line: #1f2d46;
        --mb-line-soft: #1a2638;
        --mb-text: #e2e8f0;
        --mb-text-dim: #8fa8c7;
        --mb-accent: #60a5fa;
        --mb-accent-2: #22c55e;
        --mb-warn: #fb7185;
    }
    .stApp {
        background: linear-gradient(180deg, var(--mb-bg-0) 0%, var(--mb-bg-1) 100%);
        color: var(--mb-text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, var(--mb-bg-0) 0%, var(--mb-bg-1) 100%);
    }
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1000px;
    }
    h1, h2, h3, h4, h5, h6, p, label {
        color: var(--mb-text) !important;
    }
    .stCaption {
        color: var(--mb-text-dim) !important;
    }
    [data-testid="stMarkdownContainer"] p {
        color: var(--mb-text);
    }

    hr { margin-top: 1rem; margin-bottom: 1rem; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: transparent; border-bottom: none; padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"],
    .stTabs [role="tab"] {
        height: 45px; background-color: var(--mb-bg-2); border-radius: 25px;
        box-shadow: none; border: 1px solid var(--mb-line);
        color: var(--mb-text-dim); font-weight: 700; font-size: 14px;
        flex-grow: 1; min-width: 0;
        display: flex !important; align-items: center !important; justify-content: center !important;
        width: 100% !important; padding: 0 14px !important;
        cursor: pointer !important; transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"] > *,
    .stTabs [role="tab"] > * {
        pointer-events: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #142341 !important; color: #ffffff !important;
        border: 1px solid #3f7ed4 !important;
        box-shadow: 0 0 0 1px rgba(96,165,250,0.30) inset !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stElementContainer"]) > div[data-testid="stExpander"] {
        background: var(--mb-bg-2);
        border: 1px solid var(--mb-line);
        border-radius: 12px;
    }

    div[data-testid="stForm"], div[data-testid="stExpander"], div[data-testid="stDataFrame"] {
        border-color: var(--mb-line) !important;
    }
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    textarea {
        background: #0b1424 !important;
        color: var(--mb-text) !important;
        border-color: var(--mb-line) !important;
    }
    input, textarea {
        color: var(--mb-text) !important;
    }
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    textarea {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        caret-color: #93c5fd !important;
    }
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder,
    textarea::placeholder {
        color: #93a6c0 !important;
        opacity: 1 !important;
    }
    [data-testid="stForm"] p,
    [data-testid="stForm"] small,
    [data-testid="stForm"] span {
        color: #8fa8c7 !important;
    }

    button[kind],
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        background: #12203a !important;
        color: #dbeafe !important;
        border: 1px solid #2c466e !important;
    }
    button[kind]:hover,
    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #60a5fa !important;
        color: #ffffff !important;
    }
    .stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(180deg, #2f7df6 0%, #1d5fd0 100%) !important;
        color: #ffffff !important;
        border: 1px solid #5ea5ff !important;
        box-shadow: 0 0 0 1px rgba(96,165,250,0.25) inset, 0 4px 14px rgba(37,99,235,0.35) !important;
    }
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #4f97ff 0%, #2a6ee0 100%) !important;
        border-color: #93c5fd !important;
    }

    [data-testid="stMetric"] {
        background: var(--mb-bg-2);
        border: 1px solid var(--mb-line);
        border-radius: 12px;
        padding: 10px 12px;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
        color: var(--mb-text-dim) !important;
    }

    [data-testid="stProgress"] > div {
        background: transparent !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0 !important;
    }
    [data-testid="stProgress"] > div > div {
        background: #22293a !important;
        border-radius: 999px !important;
        height: 16px !important;
        overflow: hidden !important;
    }
    [data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #1d7bf2 0%, #3ea3ff 100%) !important;
        border-radius: 999px !important;
        box-shadow: none !important;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }
    [data-testid="stAlert"] > div {
        background: #0f172a !important;
        color: var(--mb-text) !important;
        border: 1px solid var(--mb-line) !important;
    }

    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: auto !important;
            flex: 1 1 auto !important;
            min-width: 0px !important;
        }
    }

    .strategy-box {
        background-color: var(--mb-bg-2); padding: 15px; border-radius: 12px;
        color: var(--mb-text); font-size: 15px; line-height: 1.5;
        box-shadow: none; margin-bottom: 10px;
    }
    .strategy-title {
        font-weight: 800; font-size: 16px; margin-bottom: 8px; display: block; color: #f8fafc;
    }
    .workout-box { border: 2px solid #3b82f6; }
    .diet-box { border: 2px solid #22c55e; }
    .recovery-box { border: 2px solid #f59e0b; }

    .time-badge {
        background-color: #1a2f52; color: white; padding: 2px 10px;
        border-radius: 12px; font-size: 12px; font-weight: 600;
        vertical-align: middle; margin-left: 8px; display: inline-block;
        transform: translateY(-2px);
    }

    .pit-chat-panel {
        background: #0b1424;
        border: 1px solid #21314b;
        border-radius: 14px;
        padding: 10px;
        max-height: 420px;
        overflow-y: auto;
    }
    .pit-msg-row {
        display: flex;
        margin-bottom: 10px;
    }
    .pit-msg-row-user {
        justify-content: flex-end;
    }
    .pit-msg-row-coach {
        justify-content: flex-start;
    }
    .pit-bubble {
        max-width: 82%;
        border-radius: 12px;
        border: 1px solid #2b3c58;
        padding: 10px 12px;
        line-height: 1.5;
        font-size: 14px;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .pit-bubble-user {
        background: #172742;
        color: #e2e8f0;
        border-color: #355585;
    }
    .pit-bubble-coach {
        background: #0f1b30;
        color: #dbeafe;
        border-color: #29436d;
    }
    .pit-bubble-tag {
        font-size: 11px;
        color: #93a6c0;
        margin-bottom: 4px;
        letter-spacing: 0.2px;
        font-weight: 700;
    }
    .pit-empty {
        color: #8fa8c7;
        font-size: 13px;
        padding: 8px 4px;
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
        payload = dict(data or {})
        payload["_style_version"] = CHECKIN_STYLE_VERSION
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_checkin_cache(date_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"checkin_{date_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if str((data or {}).get("_style_version", "")) != CHECKIN_STYLE_VERSION:
                    return None
                return data
        return None
    except:
        return None


def save_dailyfive_cache(date_key, sprint_id, data):
    local_ok = False
    payload = dict(data or {})
    payload["_style_version"] = DAILY_FIVE_STYLE_VERSION
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        local_ok = True
    except:
        local_ok = False

    sheet_ok = False
    try:
        sheet_ok = persist_dailyfive_to_sheet(date_key, sprint_id, payload)
    except:
        sheet_ok = False

    return local_ok or sheet_ok

def load_dailyfive_cache(date_key, sprint_id):
    try:
        cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if str((data or {}).get("_style_version", "")) != DAILY_FIVE_STYLE_VERSION:
                    return None
                return data
    except:
        pass

    # /tmp 캐시에 없으면 시트에서 복원 시도
    try:
        from_sheet = load_dailyfive_from_sheet(date_key, sprint_id)
        if from_sheet:
            if str((from_sheet or {}).get("_style_version", "")) != DAILY_FIVE_STYLE_VERSION:
                return None
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


def save_pit_chat_cache(date_key, history, pending_patch=None):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"pit_chat_{date_key}.json")
        payload = {
            "date_key": str(date_key),
            "history": list(history or [])[-200:],
            "pending_patch": pending_patch if isinstance(pending_patch, dict) else None,
            "updated_at": get_current_kst().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def load_pit_chat_cache(date_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"pit_chat_{date_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            history = data.get("history", []) if isinstance(data, dict) else []
            pending_patch = data.get("pending_patch") if isinstance(data, dict) else None
            if not isinstance(history, list):
                history = []
            if not isinstance(pending_patch, dict):
                pending_patch = None
            return {"history": history, "pending_patch": pending_patch}
        return {"history": [], "pending_patch": None}
    except:
        return {"history": [], "pending_patch": None}


def clear_pit_chat_cache(date_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"pit_chat_{date_key}.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
        return True
    except:
        return False


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
            if filename.startswith(("checkin_", "dailyfive_", "xc_", "daily_wrapup_", "weekly_wrapup_", "pit_chat_")):
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

if "ANTHROPIC_API_KEY" in st.secrets:
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
else:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

try:
    ACTION_PLAN_PROVIDER = str(
        st.secrets.get("ACTION_PLAN_PROVIDER", os.getenv("ACTION_PLAN_PROVIDER", "openai"))
        or "openai"
    ).strip().lower()
except Exception:
    ACTION_PLAN_PROVIDER = str(os.getenv("ACTION_PLAN_PROVIDER", "openai") or "openai").strip().lower()
if ACTION_PLAN_PROVIDER not in {"openai", "anthropic"}:
    ACTION_PLAN_PROVIDER = "openai"

try:
    ACTION_PLAN_MODEL_OPENAI = str(
        st.secrets.get("ACTION_PLAN_MODEL_OPENAI", os.getenv("ACTION_PLAN_MODEL_OPENAI", "gpt-4o"))
        or "gpt-4o"
    ).strip()
except Exception:
    ACTION_PLAN_MODEL_OPENAI = str(os.getenv("ACTION_PLAN_MODEL_OPENAI", "gpt-4o") or "gpt-4o").strip()

try:
    ACTION_PLAN_MODEL_ANTHROPIC = str(
        st.secrets.get("ACTION_PLAN_MODEL_ANTHROPIC", os.getenv("ACTION_PLAN_MODEL_ANTHROPIC", "claude-sonnet-4-6"))
        or "claude-sonnet-4-6"
    ).strip()
except Exception:
    ACTION_PLAN_MODEL_ANTHROPIC = str(
        os.getenv("ACTION_PLAN_MODEL_ANTHROPIC", "claude-sonnet-4-6") or "claude-sonnet-4-6"
    ).strip()

try:
    COACHING_PROVIDER = str(
        st.secrets.get("COACHING_PROVIDER", os.getenv("COACHING_PROVIDER", "anthropic"))
        or "anthropic"
    ).strip().lower()
except Exception:
    COACHING_PROVIDER = str(os.getenv("COACHING_PROVIDER", "anthropic") or "anthropic").strip().lower()
if COACHING_PROVIDER not in {"openai", "anthropic"}:
    COACHING_PROVIDER = "anthropic"

try:
    COACHING_MODEL_OPENAI = str(
        st.secrets.get("COACHING_MODEL_OPENAI", os.getenv("COACHING_MODEL_OPENAI", "gpt-4o"))
        or "gpt-4o"
    ).strip()
except Exception:
    COACHING_MODEL_OPENAI = str(os.getenv("COACHING_MODEL_OPENAI", "gpt-4o") or "gpt-4o").strip()

try:
    COACHING_MODEL_ANTHROPIC = str(
        st.secrets.get("COACHING_MODEL_ANTHROPIC", os.getenv("COACHING_MODEL_ANTHROPIC", "claude-sonnet-4-6"))
        or "claude-sonnet-4-6"
    ).strip()
except Exception:
    COACHING_MODEL_ANTHROPIC = str(
        os.getenv("COACHING_MODEL_ANTHROPIC", "claude-sonnet-4-6") or "claude-sonnet-4-6"
    ).strip()

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
WRAPUP_CACHE_VERSION = "v5"
ACTION_PLAN_CACHE_VERSION = "v10"
CHECKIN_STYLE_VERSION = "v3"
DAILY_FIVE_STYLE_VERSION = "v3"
DAY_RESET_HOUR = 5
DEFAULT_DAILY_KCAL_TARGET = 2000
XC_BASELINE_KG = 0.30
XC_MIN_KG = -0.20
XC_MAX_KG = 0.50
MAKJANG_FACTOR_MULTIPLIER = 2.0

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
    # slot_id (current)
    "lunch_window": "점심 가능 시간",
    "evening_window": "저녁 가능 시간",
}

BEVERAGE_TOKENS = {"콜라", "사이다", "주스", "음료"}
OPENAI_NUTRITION_TIMEOUT_SEC = 1.8

try:
    NUTRITION_PARSE_MODE = str(st.secrets.get("NUTRITION_PARSE_MODE", "openai") or "openai").strip().lower()
except Exception:
    NUTRITION_PARSE_MODE = "openai"
if NUTRITION_PARSE_MODE not in {"fast", "balanced", "openai"}:
    NUTRITION_PARSE_MODE = "openai"

HEURISTIC_NUTRITION_PROFILE = {
    # Approximate per one serving unit
    "간짜장": {"kcal": 850, "carbs": 108.0, "protein": 22.0, "fat": 28.0},
    "짜장면": {"kcal": 800, "carbs": 118.0, "protein": 20.0, "fat": 22.0},
    "탕수육": {"kcal": 900, "carbs": 84.0, "protein": 32.0, "fat": 44.0},
    "후라이드치킨": {"kcal": 1200, "carbs": 48.0, "protein": 72.0, "fat": 74.0},
    "치킨": {"kcal": 980, "carbs": 34.0, "protein": 64.0, "fat": 58.0},
    "햄버거": {"kcal": 650, "carbs": 45.0, "protein": 28.0, "fat": 36.0},
    "피자": {"kcal": 750, "carbs": 84.0, "protein": 32.0, "fat": 32.0},
    "라면": {"kcal": 500, "carbs": 79.0, "protein": 10.0, "fat": 16.0},
    "떡볶이": {"kcal": 550, "carbs": 92.0, "protein": 10.0, "fat": 13.0},
    "김밥": {"kcal": 450, "carbs": 62.0, "protein": 13.0, "fat": 14.0},
    "비빔밥": {"kcal": 550, "carbs": 88.0, "protein": 19.0, "fat": 13.0},
    "샐러드": {"kcal": 350, "carbs": 24.0, "protein": 24.0, "fat": 16.0},
    "보쌈": {"kcal": 460, "carbs": 6.0, "protein": 38.0, "fat": 30.0},
    "돼지고기": {"kcal": 320, "carbs": 0.0, "protein": 27.0, "fat": 23.0},
    "쌀밥": {"kcal": 300, "carbs": 67.0, "protein": 5.7, "fat": 0.5},
    "밥": {"kcal": 300, "carbs": 67.0, "protein": 5.7, "fat": 0.5},
    "콜라": {"kcal": 108, "carbs": 27.0, "protein": 0.0, "fat": 0.0},  # 250ml
}

PITWALL_CARDIO_WEEKS = 8
PITWALL_START_DATE_DEFAULT = "2026-02-21"
PITWALL_RHR_START_DEFAULT = 60.0
PITWALL_RHR_TARGET_DEFAULT = 55.0
PITWALL_CARDIO_WEEK_TARGETS = [
    (180, 210), (200, 230), (220, 260), (160, 200),
    (230, 270), (250, 300), (240, 290), (150, 190),
]
PITWALL_HIIT_KEYS = (
    "hiit", "인터벌", "하이록스", "tabata", "타바타", "sprint",
)
PITWALL_ZONE2_KEYS = (
    "zone2", "zone 2", "조깅", "러닝", "달리기", "싸이클", "사이클",
    "자전거", "incline", "걷기", "유산소",
)
PITWALL_STRENGTH_KEYS = (
    "웨이트", "근력", "스쿼트", "벤치", "데드", "3대", "보디빌딩",
)

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


def build_korean_style_context():
    return """
[KOREAN STYLE GUIDE]
- 한국어 원어민 코치처럼 자연스럽고 간결하게 작성하십시오.
- 영어 문장을 직역한 번역투 표현(예: 컨트롤, 패턴 반복 차단 등)을 남발하지 마십시오.
- 어색한 군더더기 대신 짧고 명확한 문장을 우선하십시오.
- 과장된 공문체(실시하십시오/수행하십시오 반복)를 줄이고, 상황에 맞는 자연스러운 존댓말을 사용하십시오.
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


def polish_korean_coaching_text(text: str) -> str:
    if not text:
        return text
    out = str(text)
    replace_map = {
        "낙후 상태": "뒤처진 상태",
        "체중 변화를 유도": "체중 감량 흐름을 다시 만들",
        "측정치": "지표",
        "컨트롤": "관리",
        "과식 차단": "과식 줄이기",
        "야식 차단": "야식 줄이기",
        "추가 섭취 차단": "추가 섭취 줄이기",
        "패턴 반복을 차단": "같은 패턴을 끊",
        "실시하십시오": "해 주세요",
        "수행하십시오": "해 주세요",
    }
    for k, v in replace_map.items():
        out = out.replace(k, v)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def format_xc_caption_text(xc_value) -> str:
    try:
        val = abs(float(xc_value))
        return f"xC 참고값(오늘 목표 변화량): {val:.2f}kg"
    except Exception:
        return "xC 참고값 없음"


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

    lines.append("Rule: Mark ✅ when DF category input includes DF1~DF5 or plain numbers 1~5 (legacy DF5 markers supported)")
    return "\n".join(lines)


def extract_df_marks_from_text(text, allow_plain_numbers=False):
    txt_up = str(text or "").upper()
    marks = set()

    for m in re.finditer(r"(?<![A-Z0-9])DF\s*([1-5])(?!\d)", txt_up):
        marks.add(f"DF{int(m.group(1))}")

    if allow_plain_numbers:
        for m in re.finditer(r"(?<!\d)([1-5])(?!\d)", txt_up):
            marks.add(f"DF{int(m.group(1))}")

    return sorted(marks)


def _task_index_from_task_id(task_id):
    s = str(task_id or "").strip().upper()
    m = re.match(r"TASK[_-]?([1-9]\d*)$", s)
    if not m:
        return None
    try:
        return int(m.group(1))
    except:
        return None


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

        # 신규 규칙: 카테고리=DF + (DF1~DF5 또는 숫자 1~5)
        if cat == "DF":
            for mk in extract_df_marks_from_text(text_up, allow_plain_numbers=True):
                marks["df_numbers"].add(int(mk.replace("DF", "")))

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

    for pos, t in enumerate((tasks or []), start=1):
        tid = str(t.get("task_id", "")).upper().strip()
        idx = _task_index_from_task_id(tid) or pos
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


def build_daily_five_focus_snapshot(date_key, sprint_id, df_action):
    out = {
        "has_plan": False,
        "completed": 0,
        "total": 0,
        "completion_rate": 0.0,
        "remaining_count": 0,
        "remaining_tasks": [],
        "summary_line": "DF 계획 없음",
        "signature": "no_plan",
    }
    if not sprint_id:
        return out

    daily_five = load_dailyfive_cache(date_key, sprint_id)
    if not daily_five or "tasks" not in daily_five:
        return out

    tasks = list(daily_five.get("tasks", []) or [])
    total = len(tasks)
    out["has_plan"] = True
    out["total"] = int(total)
    if total <= 0:
        out["summary_line"] = "DF 계획은 있으나 항목 없음"
        out["signature"] = "plan_empty"
        return out

    if df_action is None or getattr(df_action, "empty", True) or ("Date" not in df_action.columns):
        done_rows = [{"index": i, "task_id": str(t.get("task_id", "")).upper().strip(), "title": str(t.get("title", "")).strip(), "done": False} for i, t in enumerate(tasks, start=1)]
    else:
        today_logs = df_action[df_action["Date"] == date_key]
        marks = collect_dailyfive_completion_marks(today_logs)
        done_rows = build_dailyfive_done_rows(tasks, marks)

    completed = sum(1 for d in done_rows if bool(d.get("done")))
    completion_rate = float(completed / total) if total > 0 else 0.0
    out["completed"] = int(completed)
    out["completion_rate"] = completion_rate

    remaining = []
    for idx, t in enumerate(tasks, start=1):
        dr = done_rows[idx - 1] if idx - 1 < len(done_rows) else {}
        if bool(dr.get("done")):
            continue
        remaining.append({
            "index": int(idx),
            "task_id": str(t.get("task_id", f"task_{idx}") or f"task_{idx}").strip(),
            "priority": _safe_int(t.get("priority", idx), idx),
            "title": str(t.get("title", "") or "").strip(),
        })
    remaining.sort(key=lambda x: (x["priority"], x["index"]))
    out["remaining_tasks"] = remaining[:5]
    out["remaining_count"] = int(len(remaining))

    if out["remaining_count"] > 0:
        top = out["remaining_tasks"][0]
        top_title = str(top.get("title", "") or "").strip()
        out["summary_line"] = f"DF 진행 {completed}/{total}, 남은 {len(remaining)}개, 최우선: {top_title}"
    else:
        out["summary_line"] = f"DF 진행 {completed}/{total}, 오늘 DF 완료"

    rem_ids = [str(x.get("task_id", "")) for x in out["remaining_tasks"]]
    out["signature"] = f"{completed}/{total}:{'|'.join(rem_ids)}"
    return out


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
        return _sheet_get_all_records_with_retry(sheet, worksheet_name=worksheet_name)
    except Exception as e:
        print(f"⚠️ API Error ({worksheet_name}): {e}")
        return []


def _is_read_quota_error(err):
    s = str(err or "")
    low = s.lower()
    return ("429" in low) and ("read requests" in low or "quota exceeded" in low)


def _sheet_get_all_records_with_retry(sheet, worksheet_name="", max_attempts=4):
    delay = 0.7
    last_err = None
    for attempt in range(1, int(max_attempts) + 1):
        try:
            return sheet.get_all_records()
        except Exception as e:
            last_err = e
            if (not _is_read_quota_error(e)) or attempt >= int(max_attempts):
                break
            print(f"⚠️ Sheets read quota retry ({worksheet_name}) attempt={attempt}/{max_attempts}")
            pytime.sleep(delay)
            delay = min(delay * 2.0, 4.0)
    raise last_err

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

DF5_CATEGORY_UI = {
    "workout": {"icon": "🏋️", "border": "#3B82F6"},
    "diet": {"icon": "🥗", "border": "#22C55E"},
    "recovery": {"icon": "🛌", "border": "#F59E0B"},
    "hydration": {"icon": "💧", "border": "#06B6D4"},
    "default": {"icon": "📌", "border": "#64748B"},
}


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


def _safe_float_or_none(v):
    try:
        n = float(v)
        if (n != n) or (n == float("inf")) or (n == float("-inf")):
            return None
        return n
    except:
        return None


def _latest_health_values(df_health, defaults=None, columns=None):
    """
    Health_Log에서 각 컬럼의 '가장 최근 유효 숫자'를 역순 탐색해 반환.
    빈 문자열/NaN은 건너뛰고, 없으면 defaults를 사용한다.
    """
    cols = list(columns or ["Weight", "HRV", "RHR"])
    defaults = dict(defaults or {})

    out = {}
    for c in cols:
        out[c] = _safe_float(defaults.get(c, 0.0), 0.0)

    if df_health is None or df_health.empty:
        return out

    found = set()
    for i in range(len(df_health) - 1, -1, -1):
        row = df_health.iloc[i]
        for c in cols:
            if c in found:
                continue
            v = row.get(c, None) if hasattr(row, "get") else None
            n = _safe_float_or_none(v)
            if n is None:
                continue
            out[c] = n
            found.add(c)
        if len(found) == len(cols):
            break

    return out


def _resolve_dashboard_vitals(df_health, date_key=None):
    """
    대시보드/스프린트 공통 규칙:
    1) date_key(오늘) 데이터가 있으면 오늘의 최신 유효값 사용
    2) 없으면 전체에서 최근 유효값 사용
    3) 유효값이 없으면 None
    """
    out = {
        "weight": None,
        "hrv": None,
        "rhr": None,
        "weight_date": "",
        "hrv_date": "",
        "rhr_date": "",
    }

    if df_health is None or df_health.empty or ("Date" not in df_health.columns):
        return out

    try:
        df = df_health.copy()
        df["Date_Key"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

        date_part = df["Date"].astype(str).str.strip()
        if "Time" in df.columns:
            time_part = df["Time"].astype(str).str.strip()
            ts = pd.to_datetime(date_part + " " + time_part, errors="coerce")
        else:
            ts = pd.to_datetime(date_part, errors="coerce")

        ts_date_only = pd.to_datetime(date_part, errors="coerce")
        ts = ts.where(ts.notna(), ts_date_only)

        if "Hour_Key" in df.columns:
            hk = (
                df["Hour_Key"]
                .astype(str)
                .str.extract(r"(\d{4}-\d{2}-\d{2})[_ ](\d{1,2})", expand=True)
            )
            hk_ts = pd.to_datetime(hk[0] + " " + hk[1] + ":00", errors="coerce")
            ts = ts.where(ts.notna(), hk_ts)

        df["_ts"] = ts
        df["_weight_num"] = pd.to_numeric(df.get("Weight", np.nan), errors="coerce")
        df["_hrv_num"] = pd.to_numeric(df.get("HRV", np.nan), errors="coerce")
        df["_rhr_num"] = pd.to_numeric(df.get("RHR", np.nan), errors="coerce")

        # 0 또는 음수는 결측으로 취급
        df.loc[df["_weight_num"] <= 0, "_weight_num"] = np.nan
        df.loc[df["_hrv_num"] <= 0, "_hrv_num"] = np.nan
        df.loc[df["_rhr_num"] <= 0, "_rhr_num"] = np.nan

        def _pick(num_col):
            if date_key:
                day = df[(df["Date_Key"] == str(date_key)) & (df[num_col].notna())].copy()
                if not day.empty:
                    day = day.sort_values("_ts")
                    v = float(day.iloc[-1][num_col])
                    dk = str(day.iloc[-1].get("Date_Key", "") or "")
                    return v, dk

            all_valid = df[df[num_col].notna()].copy()
            if all_valid.empty:
                return None, ""
            all_valid = all_valid.sort_values("_ts")
            v = float(all_valid.iloc[-1][num_col])
            dk = str(all_valid.iloc[-1].get("Date_Key", "") or "")
            return v, dk

        out["weight"], out["weight_date"] = _pick("_weight_num")
        out["hrv"], out["hrv_date"] = _pick("_hrv_num")
        out["rhr"], out["rhr_date"] = _pick("_rhr_num")
        return out
    except Exception:
        return out


def _get_health_last_update_badge(df_health, default_dt=None):
    """
    Health_Log 기준 업데이트 배지(HH:MM)를 계산한다.
    우선순위:
    1) Updated_At(실제 수집/반영 시각)
    2) Date+Time
    3) Date
    4) Hour_Key
    5) 기본(now)
    """
    base_dt = default_dt if isinstance(default_dt, datetime) else get_current_kst()
    default_badge = base_dt.strftime("%H:%M")

    if df_health is None or df_health.empty:
        return default_badge

    try:
        df = df_health.copy()
        # 1) 실제 동기화 반영 시각(Updated_At) 우선
        if "Updated_At" in df.columns:
            ts_updated = pd.to_datetime(df["Updated_At"], errors="coerce")
            valid_updated = ts_updated.dropna()
            if not valid_updated.empty:
                return valid_updated.max().strftime("%H:%M")

        if "Date" not in df.columns:
            return default_badge

        # 2) 보조: Date/Time 조합
        date_part = df["Date"].astype(str).str.strip()
        if "Time" in df.columns:
            time_part = df["Time"].astype(str).str.strip()
            ts = pd.to_datetime(date_part + " " + time_part, errors="coerce")
        else:
            ts = pd.to_datetime(date_part, errors="coerce")

        ts_date_only = pd.to_datetime(date_part, errors="coerce")
        ts = ts.where(ts.notna(), ts_date_only)

        if "Hour_Key" in df.columns:
            hk = (
                df["Hour_Key"]
                .astype(str)
                .str.extract(r"(\d{4}-\d{2}-\d{2})[_ ](\d{1,2})", expand=True)
            )
            hk_ts = pd.to_datetime(hk[0] + " " + hk[1] + ":00", errors="coerce")
            ts = ts.where(ts.notna(), hk_ts)

        valid = ts.dropna()
        if not valid.empty:
            return valid.max().strftime("%H:%M")
    except Exception:
        pass

    return default_badge


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
    date_key 기준 '어제 성과'를 반환.
    우선순위:
    1) date_key 당일 행의 Prev_XC_KG / Actual_Change_KG (어제 xC 성과가 기록되는 정석 위치)
    2) 당일 행이 없으면 직전 행 + 오늘 Start_Weight_KG로 보정 계산
    양수 gap_kg는 xC 미달.
    """
    try:
        rows = fetch_sheet_data("Daily_Sprint_Progress")
        sprint_id_str = str(sprint_id).strip()
        date_key_str = str(date_key).strip()

        current_row = None
        for r in (rows or []):
            if (
                str(r.get("Sprint_ID", "")).strip() == sprint_id_str
                and str(r.get("Date", "")).strip() == date_key_str
            ):
                current_row = r
                break

        if current_row:
            prev_xc = _safe_float(current_row.get("Prev_XC_KG"), None)
            actual = _safe_float(current_row.get("Actual_Change_KG"), None)
            gap = _safe_float(current_row.get("XC_Gap_KG"), None)
            ach_pct = _safe_float(current_row.get("XC_Achievement_PCT"), None)
            if gap is None and (prev_xc is not None) and (actual is not None):
                gap = float(prev_xc) - float(actual)
            if (ach_pct is None) and (prev_xc is not None) and (actual is not None) and float(prev_xc) != 0:
                ach_pct = (float(actual) / float(prev_xc)) * 100.0

            # date_key 행은 '어제 성과'를 담으므로 표시일은 date_key-1
            try:
                fb_date = (datetime.strptime(date_key_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            except:
                fb_date = None

            if (prev_xc is not None) or (actual is not None) or (gap is not None):
                return {
                    "date": fb_date,
                    "gap_kg": (round(float(gap), 3) if gap is not None else None),
                    "prev_xc_kg": (round(float(prev_xc), 3) if prev_xc is not None else None),
                    "actual_change_kg": (round(float(actual), 3) if actual is not None else None),
                    "achievement_pct": (round(float(ach_pct), 1) if ach_pct is not None else None),
                }

        # fallback: 직전 row 기반 보정 (당일 row 미생성 시)
        prev = _get_prev_progress_row(rows, sprint_id, date_key)
        if not prev:
            return {"date": None, "gap_kg": None}

        prev_date = str(prev.get("Date", "")).strip() or None
        prev_xc = _safe_float(prev.get("XC_Value_KG"), None)
        prev_start = _safe_float(prev.get("Start_Weight_KG"), None)
        today_start = _safe_float(get_start_weight_kg_for_date(date_key_str), None)

        actual = None
        if (prev_start is not None) and (today_start is not None):
            actual = float(prev_start) - float(today_start)
        gap = None
        if (prev_xc is not None) and (actual is not None):
            gap = float(prev_xc) - float(actual)
        ach_pct = None
        if (prev_xc is not None) and (actual is not None) and float(prev_xc) != 0:
            ach_pct = (float(actual) / float(prev_xc)) * 100.0

        return {
            "date": prev_date,
            "gap_kg": (round(float(gap), 3) if gap is not None else None),
            "prev_xc_kg": (round(float(prev_xc), 3) if prev_xc is not None else None),
            "actual_change_kg": (round(float(actual), 3) if actual is not None else None),
            "achievement_pct": (round(float(ach_pct), 1) if ach_pct is not None else None),
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


def _update_row_fields_by_header(sheet, headers, row_num, value_map, value_input_option="RAW"):
    """
    특정 row의 일부 컬럼만 헤더 기준으로 갱신한다.
    기존 수식 컬럼을 보존하기 위해 전체 row 덮어쓰기를 피한다.
    """
    updates = []
    for h, v in (value_map or {}).items():
        if h not in headers:
            continue
        col = _a1_col(headers.index(h) + 1)
        updates.append({"range": f"{col}{row_num}", "values": [[v]]})
    if updates:
        sheet.batch_update(updates, value_input_option=value_input_option)


def _apply_daily_progress_derived_formulas(sheet, headers, row_num):
    """
    Daily_Sprint_Progress 파생 컬럼을 시트 수식으로 계산한다.
    앱은 기본값만 쓰고, 파생 계산은 시트가 담당한다.
    """
    required = [
        "Date", "Sprint_ID", "XC_Value_KG", "Start_Weight_KG",
        "Prev_Start_Weight_KG", "Prev_XC_KG",
        "Actual_Change_KG", "XC_Gap_KG", "XC_Achievement_PCT",
    ]
    if any(h not in headers for h in required):
        return

    date_col = _a1_col(headers.index("Date") + 1)
    sprint_col = _a1_col(headers.index("Sprint_ID") + 1)
    xc_col = _a1_col(headers.index("XC_Value_KG") + 1)
    start_col = _a1_col(headers.index("Start_Weight_KG") + 1)
    prev_start_col = _a1_col(headers.index("Prev_Start_Weight_KG") + 1)
    prev_xc_col = _a1_col(headers.index("Prev_XC_KG") + 1)
    actual_col = _a1_col(headers.index("Actual_Change_KG") + 1)
    gap_col = _a1_col(headers.index("XC_Gap_KG") + 1)
    ach_col = _a1_col(headers.index("XC_Achievement_PCT") + 1)
    r = int(row_num)

    formulas = {
        "Prev_Start_Weight_KG": (
            f'=IFERROR(INDEX(SORT(FILTER({{{date_col}$2:{date_col},{start_col}$2:{start_col}}},'
            f'{sprint_col}$2:{sprint_col}={sprint_col}{r},{date_col}$2:{date_col}<{date_col}{r}),1,FALSE),1,2),"")'
        ),
        "Prev_XC_KG": (
            f'=IFERROR(INDEX(SORT(FILTER({{{date_col}$2:{date_col},{xc_col}$2:{xc_col}}},'
            f'{sprint_col}$2:{sprint_col}={sprint_col}{r},{date_col}$2:{date_col}<{date_col}{r}),1,FALSE),1,2),"")'
        ),
        "Actual_Change_KG": (
            f'=IF(AND({prev_start_col}{r}<>"",{start_col}{r}<>""),{prev_start_col}{r}-{start_col}{r},"")'
        ),
        "XC_Gap_KG": (
            f'=IF(AND({prev_xc_col}{r}<>"",{actual_col}{r}<>""),{prev_xc_col}{r}-{actual_col}{r},"")'
        ),
        "XC_Achievement_PCT": (
            f'=IF(AND({prev_xc_col}{r}<>"",{actual_col}{r}<>"",{prev_xc_col}{r}<>0),({actual_col}{r}/{prev_xc_col}{r})*100,"")'
        ),
    }
    _update_row_fields_by_header(
        sheet=sheet,
        headers=headers,
        row_num=r,
        value_map=formulas,
        value_input_option="USER_ENTERED",
    )


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

        rows = sorted(
            rows,
            key=lambda x: (
                _task_index_from_task_id(x.get("Task_ID", "")) or 999,
                _safe_int(x.get("Priority", 999), 999),
            ),
        )
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
            row_idx = _task_index_from_task_id(row_tid) or _safe_int(r.get("Priority", 0), 0)
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

        if not target_row_num:
            # 부분 데이터 행(Completed/Total만 채워진 행) 생성 방지.
            # full row는 persist_daily_sprint_progress에서 생성한다.
            return False

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
            "Trend_Weight": "",
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
    score 대략 -120~+160 범위 (요인 배율 2.0x 적용)
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
    def _scaled_points(points):
        return int(round(float(points) * float(MAKJANG_FACTOR_MULTIPLIER)))

    def add_scored_factor(name, points, detail=""):
        nonlocal score
        scaled = _scaled_points(points)
        if scaled == 0:
            return
        score += scaled
        factors.append({"name": name, "points": int(scaled), "detail": detail})

    if has_alcohol:
        add_scored_factor("음주", +30, "음주 기록")
    if has_bad_food:
        add_scored_factor("정크키워드", +15, "고위험 음식 키워드")
    if has_workout:
        add_scored_factor("운동 수행", -20, "운동 카테고리 기록")
    if low_logging:
        add_scored_factor("저기록 페널티", +5, "로그 1개 이하")

    # 시너지: 술+야식 같이 터지면 추가 벌점
    if has_alcohol and has_bad_food:
        add_scored_factor("음주+정크 시너지", +10, "동시 발생")

    # kcal 기반 가감(고칼로리/저칼로리 극단 리스크 반영)
    if intake_kcal >= 2800:
        add_scored_factor("섭취 kcal", +20, f"{intake_kcal}kcal (과다)")
    elif intake_kcal >= 2300:
        add_scored_factor("섭취 kcal", +12, f"{intake_kcal}kcal (높음)")
    elif intake_kcal >= 1800:
        add_scored_factor("섭취 kcal", +5, f"{intake_kcal}kcal (중상)")
    elif intake_kcal >= 1200:
        add_scored_factor("섭취 kcal", -4, f"{intake_kcal}kcal (적정)")
    elif intake_kcal > 0:
        add_scored_factor("섭취 kcal", +2, f"{intake_kcal}kcal (저섭취)")

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
            add_scored_factor("단백질 비율", +8, f"{protein_ratio*100:.0f}% (낮음)")
        elif 0.25 <= protein_ratio <= 0.40:
            add_scored_factor("단백질 비율", -3, f"{protein_ratio*100:.0f}% (양호)")

        if carb_ratio > 0.65:
            add_scored_factor("탄수화물 비율", +4, f"{carb_ratio*100:.0f}% (높음)")
        if fat_ratio > 0.40:
            add_scored_factor("지방 비율", +4, f"{fat_ratio*100:.0f}% (높음)")

        balanced = (0.20 <= protein_ratio <= 0.40) and (0.30 <= carb_ratio <= 0.60) and (0.15 <= fat_ratio <= 0.35)
        if balanced:
            add_scored_factor("탄단지 밸런스", -4, "균형 구간")

    # 사우나 수행일은 충분히 감점
    if sauna_count > 0:
        sauna_bonus = min(20, 12 + (sauna_count - 1) * 4)
        add_scored_factor("사우나 보정", -sauna_bonus, f"{sauna_count}회")

    # 영양제 1개당 -5 완화(일일 상한 30점)
    if supplement_count > 0:
        supp_bonus = min(30, supplement_count * 5)
        add_scored_factor("영양제 보정", -supp_bonus, f"{supplement_count}개")

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
                    'description': sprint.get('Description', sprint.get('Descriptions', ''))
                }
        return None
    except Exception as e:
        print(f"Error getting active sprint: {e}")
        return None


@st.cache_data(ttl=900)
def get_latest_ended_sprint(reference_date_key=None):
    """
    reference_date 이전(당일 제외)에 종료된 sprint 중 가장 최근 sprint를 반환한다.
    """
    try:
        records = fetch_sheet_data("Sprints")
        if not records:
            return None
        if reference_date_key:
            ref_date = _safe_parse_ymd(reference_date_key)
        else:
            ref_date = get_current_kst().date()
        if ref_date is None:
            ref_date = get_current_kst().date()

        picked = None
        picked_end = None
        for sprint in records:
            end_date = _safe_parse_ymd(sprint.get("End_Date", ""))
            start_date = _safe_parse_ymd(sprint.get("Start_Date", ""))
            if not end_date:
                continue
            if end_date >= ref_date:
                continue
            if (picked_end is None) or (end_date > picked_end):
                dur = _safe_int(sprint.get("Duration_Days", 0), 0)
                if dur <= 0 and start_date:
                    dur = int((end_date - start_date).days + 1)
                picked = {
                    "sprint_id": str(sprint.get("Sprint_ID", "") or "").strip(),
                    "name": str(sprint.get("Name", "") or "").strip(),
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_days": int(dur),
                    "status": str(sprint.get("Status", "") or "").strip().lower(),
                    "description": str(sprint.get("Description", sprint.get("Descriptions", "")) or "").strip(),
                    "result": str(sprint.get("Result", "") or "").strip().lower(),
                    "final_wt": _safe_float(sprint.get("Final_Wt"), None),
                    "closed_at": str(sprint.get("Closed_At", "") or "").strip(),
                }
                picked_end = end_date
        return picked
    except Exception as e:
        print(f"Error getting latest ended sprint: {e}")
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


def _align_date_to_saturday(d):
    if d is None:
        return None
    # Monday=0 ... Saturday=5
    delta = (5 - int(d.weekday())) % 7
    return d + timedelta(days=delta)


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
    Sprints.Status를 날짜 기준으로 자동 동기화한다.
    - 시작 전: pending
    - 기간 내: active
    - 종료 후: done (+ result/final_wt/closed_at 보정)
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
            desired_status = status
            start_date = _safe_parse_ymd(r.get("Start_Date", ""))
            end_date = _safe_parse_ymd(r.get("End_Date", ""))
            if start_date and (today_kst < start_date):
                desired_status = "pending"
            elif start_date and end_date and (start_date <= today_kst <= end_date):
                desired_status = "active"
            elif end_date and (today_kst > end_date):
                desired_status = "done"

            update_map = {}
            if desired_status != status:
                update_map["Status"] = desired_status

            sprint_id = str(r.get("Sprint_ID", "")).strip()
            if desired_status == "done":
                target_wt = target_by_sprint.get(sprint_id)
                final_wt = _latest_weight_on_or_before(df_health, end_date)
                if (target_wt is not None) and (final_wt is not None):
                    result = "success" if final_wt <= target_wt else "fail"
                else:
                    result = "unknown"

                result_now = str(r.get("Result", "")).strip().lower()
                if result_now != result:
                    update_map["Result"] = result

                final_txt = f"{final_wt:.1f}" if final_wt is not None else ""
                final_now = str(r.get("Final_Wt", "")).strip()
                if final_now != final_txt:
                    update_map["Final_Wt"] = final_txt

                closed_now = str(r.get("Closed_At", "")).strip()
                # done 최초 전환 시점 또는 비어있을 때만 종료 시각 기록
                if (not closed_now) and ((status != "done") or ("Status" in update_map)):
                    update_map["Closed_At"] = now_str

            if not update_map:
                continue

            try:
                for key, value in update_map.items():
                    if key in col_idx:
                        sh_s.update_cell(row_num, col_idx[key], value)
                updated += 1
            except Exception as e:
                print("auto close sprint: update row error:", e)

        if updated > 0:
            try:
                fetch_sheet_data.clear()
                get_active_sprint.clear()
                get_sprint_goals.clear()
                get_latest_ended_sprint.clear()
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


def backfill_daily_sprint_progress_missing_rows():
    """
    Daily_Sprint_Progress의 부분/누락 행을 가능한 범위에서 보정한다.
    - Health_Log로 Start_Weight_KG/Weight_Current 보강
    - 이전 행 기반 Prev_* / Actual_Change / XC_Gap / XC_Achievement 계산
    - xC 캐시가 있으면 XC_Value_KG 보강
    """
    try:
        sheet = get_db_connection("Daily_Sprint_Progress")
        headers = _get_or_init_headers(sheet, DAILY_SPRINT_PROGRESS_DEFAULT_HEADERS)
        rows = sheet.get_all_records()
        if not rows:
            return 0

        now_str = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
        weight_cache = {}
        xc_cache = {}

        def _start_weight(date_key):
            dk = str(date_key or "").strip()
            if not dk:
                return None
            if dk not in weight_cache:
                weight_cache[dk] = get_start_weight_kg_for_date(dk)
            return weight_cache.get(dk)

        def _xc_cached(date_key, sprint_id):
            key = f"{date_key}|{sprint_id}"
            if key not in xc_cache:
                xc_cache[key] = load_xc_cache(str(date_key), str(sprint_id)) or {}
            return xc_cache.get(key, {}) or {}

        by_sprint = {}
        for row_num, row in enumerate(rows, start=2):
            date_key = str(row.get("Date", "")).strip()
            sprint_id = str(row.get("Sprint_ID", "")).strip()
            if not date_key or not sprint_id:
                continue
            by_sprint.setdefault(sprint_id, []).append((row_num, row, date_key))

        updated = 0
        for sprint_id, items in by_sprint.items():
            items.sort(key=lambda x: x[2])
            prev_start_weight = None
            prev_xc = None

            for row_num, row, date_key in items:
                row_map = {h: row.get(h, "") for h in headers}
                changed = False

                start_weight = _safe_float(row_map.get("Start_Weight_KG"), None)
                if start_weight is None:
                    start_weight = _start_weight(date_key)
                    if start_weight is not None:
                        row_map["Start_Weight_KG"] = round(float(start_weight), 3)
                        changed = True

                weight_current = _safe_float(row_map.get("Weight_Current"), None)
                if weight_current is None and start_weight is not None:
                    weight_current = float(start_weight)
                    row_map["Weight_Current"] = round(weight_current, 3)
                    changed = True

                xc_value = _safe_float(row_map.get("XC_Value_KG"), None)
                xc_obj = _xc_cached(date_key, sprint_id)
                if xc_value is None:
                    xc_cached_val = _safe_float(xc_obj.get("xc_value_kg"), None)
                    if xc_cached_val is not None:
                        xc_value = float(xc_cached_val)
                        row_map["XC_Value_KG"] = round(xc_value, 3)
                        changed = True

                prev_start_col = _safe_float(row_map.get("Prev_Start_Weight_KG"), None)
                if prev_start_col is None and prev_start_weight is not None:
                    prev_start_col = float(prev_start_weight)
                    row_map["Prev_Start_Weight_KG"] = round(prev_start_col, 3)
                    changed = True

                prev_xc_col = _safe_float(row_map.get("Prev_XC_KG"), None)
                if prev_xc_col is None and prev_xc is not None:
                    prev_xc_col = float(prev_xc)
                    row_map["Prev_XC_KG"] = round(prev_xc_col, 3)
                    changed = True

                actual_change = _safe_float(row_map.get("Actual_Change_KG"), None)
                if actual_change is None and (prev_start_col is not None) and (start_weight is not None):
                    actual_change = float(prev_start_col) - float(start_weight)
                    row_map["Actual_Change_KG"] = round(actual_change, 3)
                    changed = True

                xc_gap = _safe_float(row_map.get("XC_Gap_KG"), None)
                if xc_gap is None and (prev_xc_col is not None) and (actual_change is not None):
                    xc_gap = float(prev_xc_col) - float(actual_change)
                    row_map["XC_Gap_KG"] = round(xc_gap, 3)
                    changed = True

                ach_pct = _safe_float(row_map.get("XC_Achievement_PCT"), None)
                if ach_pct is None and (prev_xc_col is not None) and (actual_change is not None) and float(prev_xc_col) != 0:
                    ach_pct = (float(actual_change) / float(prev_xc_col)) * 100.0
                    row_map["XC_Achievement_PCT"] = round(ach_pct, 1)
                    changed = True

                summary_raw = str(row_map.get("Summary_JSON", "") or "").strip()
                if not summary_raw:
                    row_map["Summary_JSON"] = json.dumps(
                        {
                            "backfill": True,
                            "xc_reason": list(xc_obj.get("xc_reason", []) or []),
                            "calc": {
                                "start_weight": start_weight,
                                "prev_start_weight": prev_start_col,
                                "prev_xc": prev_xc_col,
                                "actual_change": actual_change,
                                "xc_gap": xc_gap,
                                "xc_achievement_pct": ach_pct,
                            },
                        },
                        ensure_ascii=False,
                    )
                    changed = True

                if changed:
                    row_map["Updated_At"] = now_str
                    end_col = _a1_col(len(headers))
                    values = [row_map.get(h, "") for h in headers]
                    sheet.update(
                        f"A{row_num}:{end_col}{row_num}",
                        [values],
                        value_input_option="RAW",
                    )
                    updated += 1

                if start_weight is not None:
                    prev_start_weight = float(start_weight)
                if xc_value is not None:
                    prev_xc = float(xc_value)

        if updated > 0:
            try:
                fetch_sheet_data.clear()
            except:
                pass
        return int(updated)
    except Exception as e:
        print("backfill daily sprint progress error:", e)
        return 0


def run_daily_progress_backfill_once():
    """
    같은 날짜에는 한 번만 Daily_Sprint_Progress 누락 보정을 수행한다.
    """
    try:
        today_key = get_current_kst().strftime("%Y-%m-%d")
        if st.session_state.get("_daily_progress_backfill_checked_date") == today_key:
            return 0
        st.session_state["_daily_progress_backfill_checked_date"] = today_key
        return backfill_daily_sprint_progress_missing_rows()
    except:
        return 0


def calculate_sprint_progress(sprint, current_weight):
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

        # EWMA 추세체중은 폐기. 현재체중 기준으로만 판정한다.
        is_cut_sprint = weight_goal['target_value'] < weight_goal['start_value']
        pace_weight = float(current_weight)

        if is_cut_sprint:
            actual_delta = pace_weight - expected_weight
        else:
            actual_delta = expected_weight - pace_weight

        if actual_delta < -0.2:
            pace_status = 'ahead'
        elif actual_delta > 0.2:
            pace_status = 'behind'
        else:
            pace_status = 'on-track'

        if is_cut_sprint:
            remaining_loss = pace_weight - weight_goal['target_value']
        else:
            remaining_loss = weight_goal['target_value'] - pace_weight
        required_daily_pace = remaining_loss / max(1, days_remaining)

        return {
            'sprint': sprint,
            'day': min(sprint_days, days_passed + 1),
            'days_remaining': days_remaining,
            'progress_pct': (days_passed / sprint_days) * 100,
            'weight_start': weight_goal['start_value'],
            'weight_target': weight_goal['target_value'],
            'weight_current': current_weight,
            'weight_trend': None,
            'weight_expected': expected_weight,
            'weight_delta': actual_delta,
            'pace_status': pace_status,
            'required_daily_pace': required_daily_pace,
            'daily_target': daily_target,
            # 메시지/남은kg 계산은 현재체중(= pace_weight) 기준
            'pace_weight': pace_weight,
            'pace_weight_mode': 'current_weight_only',
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
                    'calendar_name': name,
                })

        return evts
    except Exception as e:
        print("calendar fetch error:", e)
        return {"Sports": [], "Termin": []}

def _overlaps(a_start, a_end, b_start, b_end):
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    return latest_start < earliest_end


def _is_canceled_event_title(title):
    t = re.sub(r"\s+", "", str(title or "").lower())
    cancel_tokens = [
        "취소", "cancel", "canceled", "cancelled",
        "연기", "보류", "미정", "reschedule", "rescheduled",
        "다시잡아야", "다시잡기", "다시잡음",
        "불참",
    ]
    return any(tok in t for tok in cancel_tokens)


def _is_workout_event_title(title):
    t = re.sub(r"\s+", "", str(title or "").lower())
    if not t:
        return False
    workout_tokens = [
        "운동", "헬스", "짐", "pt", "피티", "요가", "필라테스", "크로스핏",
        "런", "러닝", "조깅", "걷기", "산책", "사이클", "자전거", "수영",
        "테니스", "배드민턴", "농구", "축구", "클라이밍", "사우나", "gfc",
    ]
    return any(tok in t for tok in workout_tokens)


def _is_lesson_event_title(title):
    t = re.sub(r"\s+", "", str(title or "").lower())
    if not t:
        return False
    # 프로젝트 운영 규칙:
    # 사용자가 캘린더에 적는 "레슨"은 테니스 레슨으로 간주한다.
    return ("레슨" in t) or ("lesson" in t)


def _is_workout_event(ev):
    if not isinstance(ev, dict):
        return False
    title = str(ev.get("title", "") or "")
    cal_name = str(ev.get("calendar_name", "") or "").strip().lower()
    if cal_name == "sports":
        return True
    return _is_workout_event_title(title)


def build_available_slots(date_key, cal_evts):
    """
    ✅ [FIX] Hard Gate: AI에 캘린더 원문을 주지 않고,
    enabled 슬롯만 주기 위한 슬롯 생성기
    """
    dt = datetime.strptime(date_key, "%Y-%m-%d")
    now_kst = get_current_kst()  # ✅ 현재 시각
    lunch_plan_cutoff = time(11, 0)  # ✅ 11시 넘으면 점심계획 포기
    day_wrapup_cutoff = time(DAY_WRAPUP_START_HOUR, DAY_WRAPUP_START_MIN)  # ✅ 21시 이후 신규 제안 차단

    # windows (KST aware)
    lunch_start = datetime.combine(dt.date(), time(11,30), tzinfo=KST)
    lunch_end = datetime.combine(dt.date(), time(13,0), tzinfo=KST)
    evening_start = datetime.combine(dt.date(), time(19,0), tzinfo=KST)
    evening_end = datetime.combine(dt.date(), time(23,59), tzinfo=KST)

    all_events = []
    for _, ev_list in (cal_evts or {}).items():
        all_events.extend(ev_list or [])
    valid_events = [e for e in all_events if not _is_canceled_event_title(e.get("title", ""))]

    def has_blocking_overlap(win_start, win_end):
        for e in valid_events:
            if _is_workout_event(e):
                continue
            es = e['start_dt']
            ee = e['end_dt']
            if _overlaps(es, ee, win_start, win_end):
                return True
        return False

    def has_workout_overlap(win_start, win_end):
        for e in valid_events:
            if not _is_workout_event(e):
                continue
            es = e['start_dt']
            ee = e['end_dt']
            if _overlaps(es, ee, win_start, win_end):
                return True
        return False

    # tag-based forced blocking
    lunch_tagged = False
    dinner_tagged = False
    for e in valid_events:
        title = str(e.get("title", "") or "")
        t = re.sub(r"\s+", "", title)
        is_workout = _is_workout_event(e)
        if ("점심" in t) or ("점:" in t) or t.startswith("점"):
            if not is_workout:
                lunch_tagged = True
        if ("저녁" in t) or ("저:" in t) or t.startswith("저"):
            if not is_workout:
                dinner_tagged = True

    is_past_date = now_kst.date() > dt.date()
    lunch_blocked = has_blocking_overlap(lunch_start, lunch_end) or lunch_tagged
    lunch_workout_scheduled = has_workout_overlap(lunch_start, lunch_end)
    lunch_too_late = is_past_date or ((now_kst.date() == dt.date()) and (now_kst.time() >= lunch_plan_cutoff))
    evening_blocked = has_blocking_overlap(evening_start, evening_end) or dinner_tagged
    evening_workout_scheduled = has_workout_overlap(evening_start, evening_end)
    day_wrapup_mode = is_past_date or ((now_kst.date() == dt.date()) and (now_kst.time() >= day_wrapup_cutoff))
    lunch_active_now = (now_kst.date() == dt.date()) and (lunch_start <= now_kst <= lunch_end)
    evening_active_now = (now_kst.date() == dt.date()) and (evening_start <= now_kst <= evening_end)

    slots = []
    lunch_enabled = (not lunch_blocked) and (not lunch_too_late)
    slots.append({
        "slot_id": "lunch_window",
        "label": "점심 운동 실행 시간" if lunch_workout_scheduled else "점심 가능 시간",
        "start": lunch_start.strftime("%H:%M"),
        "end": lunch_end.strftime("%H:%M"),
        "enabled": lunch_enabled,
        "active_now": bool(lunch_enabled and lunch_active_now),
        "scheduled_workout": bool(lunch_workout_scheduled),
        "notes": "캘린더와 현재 시각 기준으로 점심 실행 가능 여부만 제공합니다.",
        "reason_disabled":
            ("점심 태그/점심시간 일정과 겹쳐서 막힘" if lunch_blocked else
             "해당 날짜는 이미 종료되어 신규 제안을 차단" if is_past_date else
             "11시 이후라 점심시간 계획은 폐기" if lunch_too_late else
             "")
    })
    evening_enabled = (not evening_blocked) and (not day_wrapup_mode)
    slots.append({
        "slot_id": "evening_window",
        "label": "저녁 운동 실행 시간" if evening_workout_scheduled else "저녁 가능 시간",
        "start": "19:00",
        "end": "23:59",
        "enabled": evening_enabled,
        "active_now": bool(evening_enabled and evening_active_now),
        "scheduled_workout": bool(evening_workout_scheduled),
        "notes": "캘린더와 현재 시각 기준으로 저녁 실행 가능 여부만 제공합니다.",
        "reason_disabled":
            ("저녁 태그 또는 19:00~23:59 일정과 겹쳐서 저녁 실행 불가" if evening_blocked else
             "해당 날짜는 이미 종료되어 신규 제안을 차단" if is_past_date else
             "21:00 이후에는 하루 마무리 모드로 전환되어 신규 운동 제안을 차단" if day_wrapup_mode else
             "")
    })

    return slots

def slots_to_compact_text(slots):
    # 디버그/표시용 (AI에는 JSON으로)
    lines = []
    for s in slots:
        ok = "ENABLED" if s["enabled"] else "DISABLED"
        rsn = str(s.get("reason_disabled", "") or "").strip()
        if rsn:
            lines.append(f"- {s['slot_id']}({s['start']}-{s['end']}): {ok} | {rsn}")
        else:
            lines.append(f"- {s['slot_id']}({s['start']}-{s['end']}): {ok}")
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


def _html_escape(v):
    s = str(v or "")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_escape_multiline(v):
    return _html_escape(v).replace("\n", "<br>")


def _pitwall_resolve_cardio_minutes(row):
    mins = 0
    try:
        js = _safe_json_obj(row.get("AI_Analysis_JSON", "{}"))
        mins = _safe_int(js.get("time", js.get("duration", 0)), 0)
    except:
        mins = 0
    if mins <= 0:
        mins = _extract_minutes_from_text(row.get("User_Input", ""))
    return max(0, int(mins))


def _pitwall_classify_cardio_kind(row, minutes):
    txt = " ".join(
        [
            str(row.get("Category", "") or ""),
            str(row.get("User_Input", "") or ""),
            str(row.get("AI_Analysis_JSON", "") or ""),
        ]
    ).lower()
    if any(k in txt for k in PITWALL_HIIT_KEYS):
        return "hiit"
    has_zone2 = any(k in txt for k in PITWALL_ZONE2_KEYS)
    has_strength = any(k in txt for k in PITWALL_STRENGTH_KEYS)
    if has_zone2:
        return "zone2"
    if has_strength:
        return ""
    # Do not auto-promote generic "운동 N분" into zone2.
    # zone2 is counted only when explicit zone2/cardio keywords exist.
    return ""


def build_pitwall_cardio_experiment(
    df_action,
    df_health=None,
    start_date=None,
    weeks=PITWALL_CARDIO_WEEKS,
    rhr_start=PITWALL_RHR_START_DEFAULT,
    rhr_target=PITWALL_RHR_TARGET_DEFAULT,
):
    today = get_current_kst().date()
    if isinstance(start_date, str):
        start_date = _safe_parse_ymd(start_date)
    if start_date is None:
        start_date = today
    total_weeks = max(1, int(weeks or PITWALL_CARDIO_WEEKS))
    end_date = start_date + timedelta(days=(total_weeks * 7 - 1))

    targets = list(PITWALL_CARDIO_WEEK_TARGETS)
    if len(targets) < total_weeks:
        last = targets[-1] if targets else (180, 210)
        targets.extend([last] * (total_weeks - len(targets)))

    day_stats = {}
    if df_action is not None and (not df_action.empty):
        for _, r in df_action.iterrows():
            cat = str(r.get("Category", "") or "")
            if "운동" not in cat:
                continue
            d = _safe_parse_ymd(r.get("Date", ""))
            if d is None or d < start_date or d > end_date:
                continue
            mins = _pitwall_resolve_cardio_minutes(r)
            kind = _pitwall_classify_cardio_kind(r, mins)
            if not kind:
                continue
            key = d.strftime("%Y-%m-%d")
            if key not in day_stats:
                day_stats[key] = {"zone2_min": 0, "hiit_min": 0, "hiit_sessions": 0}
            if kind == "hiit":
                day_stats[key]["hiit_sessions"] += 1
                day_stats[key]["hiit_min"] += int(mins)
            else:
                day_stats[key]["zone2_min"] += int(mins)

    health = pd.DataFrame()
    if df_health is not None and (not df_health.empty):
        health = df_health.copy()
        if "Date" in health.columns:
            parsed = pd.to_datetime(health["Date"], errors="coerce")
            if parsed.isna().any():
                parsed = parsed.where(~parsed.isna(), health["Date"].astype(str).map(lambda x: parse_korean_datetime(x)))
            health["Date_Key"] = parsed.apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "")
        else:
            health["Date_Key"] = ""
        health["RHR_num"] = pd.to_numeric(health.get("RHR", 0), errors="coerce")
        health = health[(health["Date_Key"] >= start_date.strftime("%Y-%m-%d")) & (health["Date_Key"] <= end_date.strftime("%Y-%m-%d"))]

    weeks_out = []
    total_z2 = 0
    z2_weeks_done = 0
    hiit_weeks_done = 0
    current_week_rhr_avg = None

    for i in range(total_weeks):
        ws = start_date + timedelta(days=i * 7)
        we = ws + timedelta(days=6)
        target_min, target_max = targets[i]
        week_z2 = 0
        week_hiit_sessions = 0
        days = []
        for d in range(7):
            dt = ws + timedelta(days=d)
            k = dt.strftime("%Y-%m-%d")
            stt = day_stats.get(k, {})
            z2m = _safe_int(stt.get("zone2_min", 0), 0)
            hs = _safe_int(stt.get("hiit_sessions", 0), 0)
            hm = _safe_int(stt.get("hiit_min", 0), 0)
            week_z2 += z2m
            week_hiit_sessions += hs
            days.append(
                {
                    "date": k,
                    "label": dt.strftime("%a"),
                    "zone2_min": z2m,
                    "hiit_sessions": hs,
                    "hiit_min": hm,
                    "is_today": dt == today,
                    "is_future": dt > today,
                }
            )

        total_z2 += week_z2
        if week_z2 >= target_min:
            z2_weeks_done += 1
        if week_hiit_sessions >= 1:
            hiit_weeks_done += 1

        z2_left = max(0, int(target_min - week_z2))
        hiit_left = max(0, int(1 - week_hiit_sessions))
        if ws > today:
            week_hint = "upcoming"
        else:
            hints = []
            if z2_left > 0:
                hints.append(f"{z2_left}m Z2 left")
            if hiit_left > 0:
                hints.append("need HIIT")
            week_hint = " · ".join(hints) if hints else "target hit"

        ws_key = ws.strftime("%Y-%m-%d")
        we_key = we.strftime("%Y-%m-%d")
        rhr_avg = None
        if not health.empty:
            wk_h = health[(health["Date_Key"] >= ws_key) & (health["Date_Key"] <= we_key)]["RHR_num"].dropna()
            if not wk_h.empty:
                rhr_avg = float(wk_h.mean())

        is_current = ws <= today <= we
        if is_current and (rhr_avg is not None):
            current_week_rhr_avg = float(rhr_avg)

        weeks_out.append(
            {
                "index": i + 1,
                "start": ws,
                "end": we,
                "target_min": int(target_min),
                "target_max": int(target_max),
                "zone2_total": int(week_z2),
                "hiit_sessions": int(week_hiit_sessions),
                "rhr_avg": (round(float(rhr_avg), 1) if rhr_avg is not None else None),
                "days": days,
                "hint": week_hint,
                "is_current": is_current,
            }
        )

    current_week = int((today - start_date).days // 7 + 1)
    current_week = max(1, min(total_weeks, current_week))
    total_target = sum(t[0] for t in targets[:total_weeks])
    total_target_hi = sum(t[1] for t in targets[:total_weeks])

    return {
        "title": f"RHR {int(round(float(rhr_start)))} -> {int(round(float(rhr_target)))} Experiment",
        "subtitle": f"{total_weeks}-week zone2 + HIIT plan",
        "start_date": start_date,
        "end_date": end_date,
        "rhr_start": float(rhr_start),
        "rhr_target": float(rhr_target),
        "current_week_rhr_avg": (round(float(current_week_rhr_avg), 1) if current_week_rhr_avg is not None else None),
        "current_week": current_week,
        "weeks_total": total_weeks,
        "total_zone2": int(total_z2),
        "target_zone2_min": int(total_target),
        "target_zone2_max": int(total_target_hi),
        "z2_weeks_done": int(z2_weeks_done),
        "hiit_weeks_done": int(hiit_weeks_done),
        "weeks": weeks_out,
    }


def render_pitwall_cardio_experiment(board):
    if not board:
        return

    hdr_date = (
        f"{board['start_date'].strftime('%b %d')} - "
        f"{board['end_date'].strftime('%b %d, %Y')}"
    )
    style = """
<style>
.pwx-wrap { background:#070d18; color:#dbeafe; border:1px solid #1b2638; border-radius:18px; padding:14px; margin-top:8px; }
.pwx-title { font-size:48px; font-weight:800; color:#f8fafc; margin:0; line-height:1.02; letter-spacing:-0.8px; }
.pwx-sub { color:#8fa8c7; font-size:14px; margin-top:6px; margin-bottom:10px; }
.pwx-metrics { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:8px; margin:0 0 10px; }
.pwx-metric { background:#0d1627; border:1px solid #1f2d46; border-radius:12px; padding:10px 12px; min-height:84px; }
.pwx-metric-k { color:#8ba0bd; font-size:11px; letter-spacing:1px; text-transform:uppercase; font-weight:700; margin-bottom:6px; }
.pwx-metric-v { color:#f8fafc; font-size:clamp(28px, 3.4vw, 44px); font-weight:800; line-height:1; letter-spacing:-0.8px; white-space:nowrap; }
.pwx-legend { display:flex; gap:14px; color:#9fb0c6; font-size:13px; margin:4px 0 8px; }
.pwx-dot { width:10px; height:10px; border-radius:3px; display:inline-block; margin-right:6px; vertical-align:middle; }
.pwx-dot-z2 { background:#4ade80; } .pwx-dot-hiit { background:#fb7185; } .pwx-dot-today { border:1px solid #60a5fa; background:transparent; }
.pwx-week { border:1px solid #172338; border-radius:12px; padding:10px; margin-top:8px; background:#0a1324; display:grid; grid-template-columns:150px 1fr 190px; gap:10px; align-items:center; }
.pwx-week-current { border-color:#4a89dd; box-shadow:0 0 0 1px rgba(96,165,250,0.45) inset; }
.pwx-week-muted { opacity:0.42; filter:saturate(0.8); }
.pwx-week-name { font-size:30px; font-weight:800; color:#e2e8f0; margin-bottom:2px; line-height:1; letter-spacing:-0.6px; }
.pwx-week-date { color:#90a3bf; font-size:12px; }
.pwx-days { display:grid; grid-template-columns: repeat(7, minmax(0,1fr)); gap:6px; }
.pwx-day { background:#0a111f; border:1px solid #1a2638; border-radius:8px; min-height:54px; display:flex; flex-direction:column; justify-content:center; align-items:center; padding:3px; }
.pwx-day-l { color:#7f8fa8; font-size:12px; margin-bottom:2px; }
.pwx-day-v { color:#cbd5e1; font-size:18px; font-weight:700; letter-spacing:-0.2px; line-height:1.1; }
.pwx-day-z2 { background:rgba(74,222,128,0.12); border-color:#22c55e; }
.pwx-day-hiit { background:rgba(251,113,133,0.14); border-color:#fb7185; }
.pwx-day-today { box-shadow:0 0 0 2px rgba(96,165,250,0.55) inset; }
.pwx-day-future { opacity:0.5; }
.pwx-right { text-align:right; }
.pwx-right-v { color:#f8fafc; font-size:25px; font-weight:800; letter-spacing:-0.4px; }
.pwx-right-bar { margin-top:6px; height:6px; width:100%; border-radius:999px; background:#162236; overflow:hidden; }
.pwx-right-fill { height:100%; background:#60a5fa; border-radius:999px; }
.pwx-right-h { color:#60a5fa; font-size:12px; margin-top:6px; }
.pwx-right-rhr { font-size:12px; margin-top:6px; color:#9fb0c6; }
.pwx-right-rhr-good { color:#34d399; }
.pwx-right-rhr-warn { color:#fca5a5; }
@media (max-width: 980px) {
  .pwx-title { font-size:42px; }
  .pwx-metric { min-height:76px; padding:9px 10px; }
  .pwx-metric-k { font-size:10px; margin-bottom:5px; }
  .pwx-metric-v { font-size:clamp(22px, 7.2vw, 34px); }
  .pwx-week { grid-template-columns:1fr; }
  .pwx-right { text-align:left; }
}
</style>
"""

    html_parts = [style, '<div class="pwx-wrap">']
    html_parts.append(f'<h3 class="pwx-title">{_html_escape(board.get("title", ""))}</h3>')
    wk_rhr = board.get("current_week_rhr_avg")
    wk_rhr_text = f"" if wk_rhr is not None else ""
    html_parts.append(
        f'<div class="pwx-sub">{_html_escape(board.get("subtitle", ""))} · '
        f'{_html_escape(hdr_date)}{_html_escape(wk_rhr_text)}</div>'
    )
    total_z2 = _safe_int(board.get("total_zone2", 0), 0)
    target_z2 = _safe_int(board.get("target_zone2_min", 0), 0)
    week_now = _safe_int(board.get("current_week", 1), 1)
    week_total = _safe_int(board.get("weeks_total", 8), 8)
    html_parts.append('<div class="pwx-metrics">')
    html_parts.append(
        '<div class="pwx-metric">'
        '<div class="pwx-metric-k">TOTAL Z2</div>'
        f'<div class="pwx-metric-v">{total_z2}m</div>'
        '</div>'
    )
    html_parts.append(
        '<div class="pwx-metric">'
        '<div class="pwx-metric-k">TARGET</div>'
        f'<div class="pwx-metric-v">{target_z2}m</div>'
        '</div>'
    )
    html_parts.append(
        '<div class="pwx-metric">'
        '<div class="pwx-metric-k">WEEK</div>'
        f'<div class="pwx-metric-v">{week_now}/{week_total}</div>'
        '</div>'
    )
    html_parts.append('</div>')
    html_parts.append(
        '<div class="pwx-legend">'
        '<span><i class="pwx-dot pwx-dot-z2"></i>Zone 2</span>'
        '<span><i class="pwx-dot pwx-dot-hiit"></i>HIIT</span>'
        '<span><i class="pwx-dot pwx-dot-today"></i>Today</span>'
        "</div>"
    )

    rhr_target = _safe_float(board.get("rhr_target"), PITWALL_RHR_TARGET_DEFAULT)
    for wk in (board.get("weeks", []) or []):
        row_cls = "pwx-week pwx-week-current" if wk.get("is_current") else "pwx-week pwx-week-muted"
        html_parts.append(f'<div class="{row_cls}">')
        html_parts.append(
            '<div>'
            f'<div class="pwx-week-name">Week {int(wk.get("index", 0))}</div>'
            f'<div class="pwx-week-date">{wk["start"].strftime("%b %d")} - {wk["end"].strftime("%b %d")}</div>'
            '</div>'
        )

        html_parts.append('<div class="pwx-days">')
        for d in (wk.get("days", []) or []):
            c = ["pwx-day"]
            if d.get("zone2_min", 0) > 0:
                c.append("pwx-day-z2")
            if d.get("hiit_sessions", 0) > 0:
                c.append("pwx-day-hiit")
            if d.get("is_today"):
                c.append("pwx-day-today")
            if d.get("is_future"):
                c.append("pwx-day-future")

            value = ""
            if d.get("hiit_sessions", 0) > 0:
                hm = _safe_int(d.get("hiit_min", 0), 0)
                value = f"HIIT {hm}m" if hm > 0 else "HIIT"
            elif d.get("zone2_min", 0) > 0:
                value = f"{_safe_int(d.get('zone2_min', 0), 0)}m"

            html_parts.append(
                f'<div class="{" ".join(c)}">'
                f'<div class="pwx-day-l">{_html_escape(d.get("label", ""))}</div>'
                f'<div class="pwx-day-v">{_html_escape(value)}</div>'
                "</div>"
            )
        html_parts.append("</div>")

        target_min = max(1, int(wk.get("target_min", 0)))
        achieved = max(0, int(wk.get("zone2_total", 0)))
        bar_pct = int(clamp((achieved / target_min) * 100.0, 0.0, 100.0))
        rhr_avg = wk.get("rhr_avg")
        rhr_cls = "pwx-right-rhr"
        if rhr_avg is not None:
            if float(rhr_avg) <= rhr_target:
                rhr_cls += " pwx-right-rhr-good"
            else:
                rhr_cls += " pwx-right-rhr-warn"
            rhr_txt = f"RHR avg {float(rhr_avg):.1f} (target {rhr_target:.0f})"
        else:
            rhr_txt = "RHR avg -"
        html_parts.append(
            '<div class="pwx-right">'
            f'<div class="pwx-right-v">{achieved}m / {int(wk.get("target_min", 0))}-{int(wk.get("target_max", 0))}m</div>'
            f'<div class="pwx-right-bar"><div class="pwx-right-fill" style="width:{bar_pct}%"></div></div>'
            f'<div class="pwx-right-h">{_html_escape(wk.get("hint", ""))}</div>'
            f'<div class="{rhr_cls}">{_html_escape(rhr_txt)}</div>'
            "</div>"
        )
        html_parts.append("</div>")

    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


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
    lunch_workout = False
    dinner_workout = False
    lunch_lesson = False
    dinner_lesson = False
    dinner_workout_times = []

    all_events = []
    for _, ev_list in (cal_evts or {}).items():
        all_events.extend(ev_list or [])

    for e in all_events:
        title = str(e.get("title", "") or "")
        if _is_canceled_event_title(title):
            continue
        title_compact = re.sub(r"\s+", "", title.lower())
        is_workout = _is_workout_event(e)
        is_lesson = _is_lesson_event_title(title)
        es = e.get("start_dt")
        ee = e.get("end_dt")
        if es is not None and ee is not None:
            if _overlaps(es, ee, lunch_start, lunch_end):
                if is_workout:
                    lunch_workout = True
                    if is_lesson:
                        lunch_lesson = True
                lunch_overlap = True
            if _overlaps(es, ee, dinner_start, dinner_end):
                if is_workout:
                    dinner_workout = True
                    if is_lesson:
                        dinner_lesson = True
                    clip_start = max(es, dinner_start)
                    clip_end = min(ee, dinner_end)
                    if clip_start < clip_end:
                        dinner_workout_times.append((clip_start, clip_end))
                dinner_overlap = True

        if ("점심" in title_compact) or ("점:" in title_compact) or title_compact.startswith("점"):
            if is_workout:
                lunch_workout = True
                if is_lesson:
                    lunch_lesson = True
            else:
                lunch_tag = True
        if ("저녁" in title_compact) or ("저:" in title_compact) or title_compact.startswith("저"):
            if is_workout:
                dinner_workout = True
                if is_lesson:
                    dinner_lesson = True
            else:
                dinner_tag = True

    dinner_workout_start = None
    dinner_workout_end = None
    if dinner_workout_times:
        try:
            dinner_workout_start = min(x[0] for x in dinner_workout_times).strftime("%H:%M")
            dinner_workout_end = max(x[1] for x in dinner_workout_times).strftime("%H:%M")
        except Exception:
            dinner_workout_start = None
            dinner_workout_end = None

    return {
        "lunch_appointment": bool((lunch_overlap or lunch_tag) and (not lunch_workout)),
        "dinner_appointment": bool((dinner_overlap or dinner_tag) and (not dinner_workout)),
        "lunch_workout_scheduled": bool(lunch_workout),
        "dinner_workout_scheduled": bool(dinner_workout),
        "lunch_lesson_scheduled": bool(lunch_lesson),
        "dinner_lesson_scheduled": bool(dinner_lesson),
        "dinner_workout_start": dinner_workout_start,
        "dinner_workout_end": dinner_workout_end,
    }


def _calendar_fact_sentence(daily_state):
    cf = (daily_state or {}).get("calendar_flags", {}) or {}
    lunch_appt = bool(cf.get("lunch_appointment", False))
    dinner_appt = bool(cf.get("dinner_appointment", False))
    lunch_workout = bool(cf.get("lunch_workout_scheduled", False))
    dinner_workout = bool(cf.get("dinner_workout_scheduled", False))
    lunch_lesson = bool(cf.get("lunch_lesson_scheduled", False))
    dinner_lesson = bool(cf.get("dinner_lesson_scheduled", False))
    if lunch_lesson and dinner_lesson:
        return "점심·저녁에 테니스 레슨 일정이 있어, 해당 세션 수행 중심으로 식사·회복만 정리하면 됩니다."
    if lunch_appt and dinner_lesson:
        return "점심 약속은 있지만 저녁 테니스 레슨 일정이 있어, 저녁 레슨 수행에 집중하면 됩니다."
    if dinner_appt and lunch_lesson:
        return "저녁 약속은 있지만 점심 테니스 레슨 일정이 있어, 점심 레슨 수행에 집중하면 됩니다."
    if lunch_lesson:
        return "오늘 점심에 테니스 레슨 일정이 이미 잡혀 있어, 해당 세션 수행 중심으로 운영하면 됩니다."
    if dinner_lesson:
        return "오늘 저녁에 테니스 레슨 일정이 이미 잡혀 있어, 해당 세션 수행 중심으로 운영하면 됩니다."
    if lunch_appt and dinner_appt:
        return "오늘은 점심·저녁에 약속이 있어 실행 가능한 시간이 짧습니다."
    if lunch_appt and dinner_workout:
        return "점심 약속은 있지만 저녁 운동 일정이 잡혀 있어, 저녁 세션 실행에 집중하면 됩니다."
    if dinner_appt and lunch_workout:
        return "저녁 약속은 있지만 점심 운동 일정이 잡혀 있어, 점심 세션 실행에 집중하면 됩니다."
    if lunch_workout and dinner_workout:
        return "점심·저녁에 운동 일정이 이미 잡혀 있어, 각 세션을 기준으로 식사·회복만 정렬하면 됩니다."
    if lunch_workout:
        return "오늘 점심에 운동 일정이 이미 잡혀 있어, 해당 세션 실행 중심으로 운영하면 됩니다."
    if dinner_workout:
        return "오늘 저녁에 운동 일정이 이미 잡혀 있어, 해당 세션 실행 중심으로 운영하면 됩니다."
    if lunch_appt:
        return "오늘은 점심 일정이 있어 점심 시간 선택 폭이 좁습니다."
    if dinner_appt:
        return "오늘은 저녁 약속이 있어 별도 운동 시간 확보가 어렵습니다."
    return ""


def _apply_calendar_fact_guard(text, daily_state):
    s = str(text or "").strip()
    if not s:
        return s

    fact = _calendar_fact_sentence(daily_state)
    if not fact:
        return s

    # AI가 가끔 사실과 다르게 "약속 없음"을 말하는 케이스를 문장 단위로 제거
    parts = [p.strip() for p in re.split(r'(?<=[\.\!\?])\s+|\n+', s) if p.strip()]
    kept = []
    for ln in parts:
        has_schedule_word = ("약속" in ln) or ("일정" in ln)
        has_no_schedule_word = bool(re.search(r"(없|안\s*잡|잡혀\s*있지)", ln))
        if has_schedule_word and has_no_schedule_word:
            continue
        kept.append(ln)
    s = " ".join(kept).strip()
    s = re.sub(r"\s{2,}", " ", s).strip()

    has_calendar_hint = bool(re.search(r"(점심|저녁).*(일정|약속|운동|세션|슬롯)", s))
    if not has_calendar_hint:
        s = f"{fact} {s}".strip()
    return s


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
    after_work_open = _slot_enabled(slots, "evening_window")
    lunch_open = _slot_enabled(slots, "lunch_window")

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
    - linear_expected_weight
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
            "day": (int(sprint_progress.get("day")) if sprint_progress and sprint_progress.get("day") is not None else None),
            "days_remaining": (int(sprint_progress.get("days_remaining")) if sprint_progress and sprint_progress.get("days_remaining") is not None else None),
            "progress_pct": (float(sprint_progress.get("progress_pct")) if sprint_progress and sprint_progress.get("progress_pct") is not None else None),
            "pace_status": (sprint_progress.get("pace_status") if sprint_progress else None),
            "weight_delta": (float(sprint_progress.get("weight_delta")) if sprint_progress and sprint_progress.get("weight_delta") is not None else None),
            "required_daily_pace": (float(sprint_progress.get("required_daily_pace")) if sprint_progress and sprint_progress.get("required_daily_pace") is not None else None),
            "daily_target": (float(sprint_progress.get("daily_target")) if sprint_progress and sprint_progress.get("daily_target") is not None else None),
        },
        "bio_signal": {
            "hrv": (float(current_hrv) if current_hrv is not None else None),
            "rhr": (float(current_rhr) if current_rhr is not None else None),
        },
        "linear_expected_weight": (float(linear_expected_weight) if linear_expected_weight is not None else None),
        "available_slots": available_slots or [],
        "today_logs": list(today["today_logs"] or []),
    }
    state["xc"] = compute_xc(daily_target, state)
    state["urgency"] = compute_urgency(state)
    return state


def _slot_enabled(slots, slot_id):
    if isinstance(slot_id, (list, tuple, set)):
        targets = {str(x) for x in slot_id}
        for s in (slots or []):
            if str(s.get("slot_id")) in targets:
                return bool(s.get("enabled"))
        return False
    for s in (slots or []):
        if s.get("slot_id") == slot_id:
            return bool(s.get("enabled"))
    return False


def _sanitize_plan_lines(text):
    if not text:
        return ""

    def _norm_key(src):
        s = str(src or "").strip().lower()
        s = re.sub(r"^\s*[-•]\s*", "", s)
        s = re.sub(r"^\s*(지금 상황|현 시점 제안|핵심|현재 상태 요약|현 시점 우선 1개|왜 이걸 우선하냐면|오늘 방어선|오늘 이득)\s*:\s*", "", s)
        s = re.sub(r"\b\d{1,2}:\d{2}\s*기준\b", "", s)
        s = re.sub(r"\s*~\s*", "~", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip(" .")

    cleaned = []
    seen = set()
    for raw in str(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"(\d{1,2})\s*:\s*(\d{2})", r"\1:\2", line)
        line = re.sub(r"\s*~\s*", "~", line)
        line = re.sub(r"\b\d{1,2}:\d{2}\s*기준\s*", "", line).strip()
        line = re.sub(r"^\s*(지금 상황|현 시점 제안)\s*:\s*", "", line).strip()
        line = re.sub(r"\s{2,}", " ", line).strip()

        key = _norm_key(line)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(line)

    return "\n".join(cleaned).strip()


def _dedupe_consecutive_sentences(text):
    if not text:
        return ""
    parts = re.split(r"(?<=[\.\!\?])\s+", str(text).strip())
    if len(parts) <= 1:
        return str(text).strip()

    out = []
    seen = set()
    for p in parts:
        s = str(p or "").strip()
        if not s:
            continue
        key = re.sub(r"^\s*[-•]\s*", "", s).strip().lower()
        key = re.sub(r"^\s*(핵심|현재 상태 요약|현 시점 우선 1개|왜 이걸 우선하냐면|오늘 방어선|오늘 이득)\s*:\s*", "", key)
        key = re.sub(r"\b\d{1,2}:\d{2}\s*기준\b", "", key)
        key = re.sub(r"\s+", " ", key).strip(" .")
        if key in seen:
            continue
        out.append(s)
        seen.add(key)
    return " ".join(out).strip()


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
        "실행", "고정", "차단", "기록", "시작", "마무리",
        "하십시오", "하세요", "하십시", "must", "do now",
    ]
    return any(m in low for m in action_markers)


def _rewrite_vague_korean(text):
    if not text:
        return ""
    out = str(text)
    replacements = [
        ("자유 슬롯", "여유 시간"),
        ("점심 시간대 여유 시간이 제한됩니다", "점심은 다른 일정이 있어 시간이 짧습니다"),
        ("저녁 시간대 여유 시간이 제한됩니다", "저녁은 다른 일정이 있어 시간이 짧습니다"),
        ("점심 시간대 자유 슬롯이 제한됩니다", "점심은 다른 일정이 있어 시간이 짧습니다"),
        ("저녁 시간대 자유 슬롯이 제한됩니다", "저녁은 다른 일정이 있어 시간이 짧습니다"),
        ("점심 시간대 운동 가능한 시간이 제한됩니다", "점심은 다른 일정이 있어 시간이 짧습니다"),
        ("저녁 시간대 운동 가능한 시간이 제한됩니다", "저녁은 다른 일정이 있어 시간이 짧습니다"),
        ("점심 시간 전에 좀 더 준비하시고", "점심 전에 메뉴를 먼저 정하고"),
        ("가능한 건강한 메뉴로 식사를 진행하세요", "점심은 단백질+채소로 고르고 밥/면/튀김은 빼세요"),
        ("식사/수분/준비를 정리하고", "물 200ml만 마시고"),
        ("스프린트에 뒤쳐져 있으니", "목표 대비 지연 상태이므로"),
    ]
    for src, dst in replacements:
        out = out.replace(src, dst)

    # 모호한 '준비' 문구를 실행형으로 치환
    out = re.sub(r"준비를 완료하고", "실행 항목을 확정하고", out)
    out = re.sub(r"준비하세요", "바로 정하세요", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def _prepend_urgency_header(analysis, daily_state):
    txt = str(analysis or "").strip()
    urg = (daily_state or {}).get("urgency", {}) or {}
    level = str(urg.get("level", "") or "").strip().lower()
    sprint = (daily_state or {}).get("sprint", {}) or {}
    delta = sprint.get("weight_delta")
    req = sprint.get("required_daily_pace")

    try:
        delta_f = float(delta) if delta is not None else None
    except Exception:
        delta_f = None
    try:
        req_f = float(req) if req is not None else None
    except Exception:
        req_f = None

    if level == "high":
        if (delta_f is not None) and (delta_f > 0) and (req_f is not None):
            head = (
                f"현재 위기 구간입니다: 목표 대비 {delta_f:.2f}kg 뒤처져 있고, "
                f"필요 페이스는 하루 {req_f:.2f}kg 수준입니다."
            )
        elif (delta_f is not None) and (delta_f > 0):
            head = f"현재 위기 구간입니다: 목표 대비 {delta_f:.2f}kg 뒤처져 있습니다."
        else:
            head = "현재 위기 구간입니다: 오늘 페이스가 밀리면 복구 난도가 크게 올라갈 수 있습니다."
    elif level == "medium":
        if req_f is not None:
            head = f"현재 주의 구간입니다: 목표 페이스를 맞추려면 하루 {req_f:.2f}kg 수준의 관리가 필요합니다."
        else:
            head = "현재 주의 구간입니다: 오늘 선택에 따라 주간 흐름이 갈릴 수 있습니다."
    else:
        return txt

    if txt.startswith(head):
        return txt
    return f"{head} {txt}".strip()


def _prepend_sprint_context_header(analysis, daily_state):
    txt = str(analysis or "").strip()
    if not txt:
        return txt

    sprint = (daily_state or {}).get("sprint", {}) or {}
    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    day = sprint.get("day")
    days_left = sprint.get("days_remaining")
    delta = sprint.get("weight_delta")
    req = sprint.get("required_daily_pace")

    try:
        day_i = int(day) if day is not None else None
    except Exception:
        day_i = None
    try:
        left_i = int(days_left) if days_left is not None else None
    except Exception:
        left_i = None
    try:
        delta_f = float(delta) if delta is not None else None
    except Exception:
        delta_f = None
    try:
        req_f = float(req) if req is not None else None
    except Exception:
        req_f = None

    if pace == "behind":
        if (left_i is not None) and (delta_f is not None) and (req_f is not None):
            head = (
                f"스프린트 현황: 현재 Day {day_i if day_i is not None else '?'} 구간이고, 남은 {left_i}일 동안 "
                f"{delta_f:.2f}kg 격차를 메우려면 하루 {req_f:.2f}kg 페이스가 필요합니다."
            )
        elif delta_f is not None:
            head = f"스프린트 현황: 목표 대비 {delta_f:.2f}kg 뒤처진 상태입니다."
        else:
            head = "스프린트 현황: 현재 뒤처진 구간으로 분류됩니다."
    elif pace == "on-track":
        if left_i is not None:
            head = f"스프린트 현황: 현재 페이스는 유지 구간이며, 남은 {left_i}일 관리가 핵심입니다."
        else:
            head = "스프린트 현황: 현재 페이스는 유지 구간입니다."
    elif pace == "ahead":
        if left_i is not None:
            head = f"스프린트 현황: 현재는 앞선 구간이며, 남은 {left_i}일은 방어 관리가 핵심입니다."
        else:
            head = "스프린트 현황: 현재는 앞선 구간입니다."
    else:
        return txt

    if txt.startswith(head):
        return txt
    return f"{head} {txt}".strip()


def _detect_today_food_risk(daily_state):
    """
    오늘 섭취 로그에서 고위험(패스트푸드/가공빵/튀김류) 신호를 추출한다.
    """
    logs = list((daily_state or {}).get("today_logs", []) or [])
    if not logs:
        return {"has_any": False, "has_high": False, "high_hits": [], "moderate_hits": []}

    intake_lines = [str(x) for x in logs if "섭취" in str(x)]
    if not intake_lines:
        return {"has_any": False, "has_high": False, "high_hits": [], "moderate_hits": []}

    blob = " ".join(intake_lines)
    norm = re.sub(r"\s+", "", blob).lower()

    high_keywords = [
        # 패스트푸드/가공빵
        "맥모닝", "햄버거", "치즈버거", "버거", "감자튀김", "프라이", "소시지빵",
        "도넛", "도너츠", "피자빵", "치킨버거", "너겟",
        # 고탄수/고지방 대표군(강경 코칭 대상)
        "양념치킨", "후라이드치킨",
        "탕수육", "짜장", "짬뽕", "중국집", "중국음식",
    ]
    moderate_keywords = [
        "튀김", "라면", "짜장", "짬뽕", "떡볶이", "국밥", "우동", "순대", "만두", "피자",
    ]

    high_hits = []
    for kw in high_keywords:
        if re.sub(r"\s+", "", kw).lower() in norm:
            high_hits.append(kw)

    moderate_hits = []
    for kw in moderate_keywords:
        if re.sub(r"\s+", "", kw).lower() in norm:
            moderate_hits.append(kw)

    # 순서 보존 중복 제거
    def _uniq(seq):
        out = []
        seen = set()
        for x in seq:
            k = str(x).strip().lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(x)
        return out

    high_hits = _uniq(high_hits)
    moderate_hits = _uniq(moderate_hits)
    return {
        "has_any": bool(high_hits or moderate_hits),
        "has_high": bool(high_hits),
        "high_hits": high_hits,
        "moderate_hits": moderate_hits,
    }


def _detect_today_alcohol_risk(daily_state):
    logs = list((daily_state or {}).get("today_logs", []) or [])
    if not logs:
        return {"has_alcohol": False, "hits": []}
    hits = []
    for x in logs:
        s = str(x or "")
        if "음주" in s:
            hits.append(s)
    return {"has_alcohol": bool(hits), "hits": hits}


def _resolve_food_risk_tone_level(daily_state, food_risk):
    """
    강경 모드 기준:
    - 고위험 음식(패스트푸드/치킨/중식 튀김 등) 또는
    - 음주
    가 있으면 기본적으로 high.
    """
    risk = food_risk or {}
    alcohol_risk = _detect_today_alcohol_risk(daily_state)
    if bool(alcohol_risk.get("has_alcohol", False)):
        return "high"
    if bool(risk.get("has_high", False)):
        return "high"
    if bool(risk.get("has_any", False)):
        return "medium"
    return "none"


def _downgrade_false_positive_tone(analysis, daily_state):
    txt = str(analysis or "").strip()
    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    risk = _food_risk_fn(daily_state)
    alcohol_risk = _alcohol_risk_fn(daily_state)
    if not txt or ((not bool(risk.get("has_high", False))) and (not bool(alcohol_risk.get("has_alcohol", False)))):
        return txt

    # 고위험 섭취가 있을 때 '잘 진행'류 문구는 강제 교정
    positive_patterns = [
        r"잘\s*진행\s*중(이네요|입니다|이에요)?",
        r"잘하고\s*계시(네요|고\s*있습니다)?",
        r"양호(합니다|한\s*편입니다)?",
        r"순조롭(습니다|게\s*진행)",
        r"안정적(입니다|으로\s*가고\s*있습니다)?",
        r"좋은\s*흐름(입니다|이에요)?",
    ]
    for p in positive_patterns:
        txt = re.sub(p, "현재는 보정이 필요한 상태입니다", txt)

    txt = re.sub(r"\s{2,}", " ", txt).strip()
    return txt


def _prepend_empathy_header(analysis, daily_state):
    txt = str(analysis or "").strip()
    if not txt:
        return txt

    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False, "high_hits": []})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    _risk_level_fn = globals().get("_resolve_food_risk_tone_level", lambda _s, _r: "none")
    food_risk = _food_risk_fn(daily_state)
    alcohol_risk = _alcohol_risk_fn(daily_state)
    urg = (daily_state or {}).get("urgency", {}) or {}
    level = str(urg.get("level", "") or "").strip().lower()
    late_mode = bool((daily_state or {}).get("late_mode", False))
    ys = (daily_state or {}).get("yesterday_summary", {}) or {}
    alcohol_y = bool(ys.get("alcohol_yesterday", False))

    risk_tone = _risk_level_fn(daily_state, food_risk)
    if bool(alcohol_risk.get("has_alcohol", False)):
        empath = "현재는 강경 보정 구간입니다. 음주가 들어간 날은 페이스 복구가 급격히 어려워져서 오늘은 절대 추가 음주를 막아야 합니다."
    elif bool(food_risk.get("has_high", False)):
        kw = ", ".join(list(food_risk.get("high_hits", []) or [])[:3])
        if risk_tone == "high":
            if kw:
                empath = f"현재는 강경 보정 구간입니다. 오늘 섭취에 {kw}가 포함되어 그대로 두면 격차가 고정될 위험이 큽니다."
            else:
                empath = "현재는 강경 보정 구간입니다. 오늘 섭취 구성이 무거워 그대로 두면 복구 난도가 크게 올라갑니다."
        else:
            if kw:
                empath = f"오늘 섭취에 {kw}가 포함되어 있어, 남은 끼니에서 균형 보정이 필요한 구간입니다."
            else:
                empath = "오늘은 섭취 균형 보정이 필요한 구간입니다."
    elif level == "high":
        empath = "지금 답답하고 조급하게 느껴지실 수 있는데, 이런 구간은 실제로 자주 나옵니다."
    elif late_mode or alcohol_y:
        empath = "오늘 컨디션이 흔들릴 만한 배경이 분명히 있었습니다."
    else:
        empath = "지금 흐름에서도 충분히 다시 정리할 수 있습니다."

    if txt.startswith(empath):
        return txt
    return f"{empath} {txt}".strip()


def _build_state_snapshot_line(daily_state):
    meal = (daily_state or {}).get("meal_done", {}) or {}
    workout = (daily_state or {}).get("workout_done", {}) or {}
    intake = (daily_state or {}).get("intake_today", {}) or {}
    cal = (daily_state or {}).get("calendar_flags", {}) or {}
    sprint = (daily_state or {}).get("sprint", {}) or {}

    meals_cnt = _safe_int(intake.get("meals_count_today", 0), 0)
    kcal_now = _safe_int(intake.get("kcal_est_today", 0), 0)
    workout_done = bool(workout.get("worked_out_today", False))
    workout_min = _safe_int(workout.get("workout_minutes_today", 0), 0)

    meal_bits = []
    if bool(meal.get("breakfast_done", False)):
        meal_bits.append("아침 완료")
    if bool(meal.get("lunch_done", False)):
        meal_bits.append("점심 완료")
    if bool(meal.get("dinner_done", False)):
        meal_bits.append("저녁 완료")
    if not meal_bits:
        meal_bits.append("식사 미기록")

    cal_bits = []
    if bool(cal.get("lunch_workout_scheduled", False)):
        cal_bits.append("점심 운동 일정 있음")
    if bool(cal.get("dinner_workout_scheduled", False)):
        cal_bits.append("저녁 운동 일정 있음")
    if bool(cal.get("lunch_appointment", False)):
        cal_bits.append("점심 일정 있음")
    if bool(cal.get("dinner_appointment", False)):
        cal_bits.append("저녁 일정 있음")
    if not cal_bits:
        cal_bits.append("주요 식사 일정 변수 없음")

    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    delta = _safe_float(sprint.get("weight_delta"), None)
    if pace == "behind" and (delta is not None):
        sprint_txt = f"페이스 뒤처짐({delta:.2f}kg)"
    elif pace == "ahead":
        sprint_txt = "페이스 앞섬"
    elif pace == "on-track":
        sprint_txt = "페이스 유지"
    else:
        sprint_txt = "페이스 정보 보통"

    workout_txt = "운동 미실행" if not workout_done else f"운동 {workout_min}분 완료"
    return (
        f"현재 상태 요약: {', '.join(meal_bits)} / {workout_txt} / "
        f"섭취 {meals_cnt}회·약 {kcal_now}kcal / {', '.join(cal_bits)} / {sprint_txt}."
    )


def _build_now_loss_gain_hint(daily_state):
    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False, "high_hits": []})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    food_risk = _food_risk_fn(daily_state)
    alcohol_risk = _alcohol_risk_fn(daily_state)
    meal = (daily_state or {}).get("meal_done", {}) or {}
    workout = (daily_state or {}).get("workout_done", {}) or {}
    intake = (daily_state or {}).get("intake_today", {}) or {}
    sprint = (daily_state or {}).get("sprint", {}) or {}
    cal = (daily_state or {}).get("calendar_flags", {}) or {}
    slots = list((daily_state or {}).get("available_slots", []) or [])
    enabled_now = any(bool(s.get("enabled")) and bool(s.get("active_now")) for s in slots)
    enabled_later = any(bool(s.get("enabled")) and (not bool(s.get("active_now"))) for s in slots)
    scheduled_slot = next(
        (
            s for s in slots
            if bool(s.get("enabled")) and bool(s.get("scheduled_workout"))
        ),
        None,
    )
    dinner_lesson = bool(cal.get("dinner_lesson_scheduled", False))
    lesson_label = "테니스 레슨 세션" if dinner_lesson else "캘린더 운동 세션"
    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    delta = _safe_float(sprint.get("weight_delta"), None)
    req = _safe_float(sprint.get("required_daily_pace"), None)
    days_left = _safe_int(sprint.get("days_remaining"), 0)

    kcal_now = _safe_int(intake.get("kcal_est_today", 0), 0)
    kcal_target = _safe_int(intake.get("kcal_target_today", DEFAULT_DAILY_KCAL_TARGET), DEFAULT_DAILY_KCAL_TARGET)
    over_kcal = (kcal_now - kcal_target) >= 250

    if bool(alcohol_risk.get("has_alcohol", False)):
        loss = "음주가 들어간 날에 추가 탄수·야식이 붙으면 내일 반등폭이 급격히 커져 스프린트 복구가 매우 어려워집니다."
        gain = "지금부터 추가 섭취를 끊고 수분·수면을 지키면 내일 반등폭을 유의미하게 줄일 수 있습니다."
        return loss, gain

    if bool(food_risk.get("has_high", False)):
        kw = ", ".join(list(food_risk.get("high_hits", []) or [])[:3]) or "고열량 가공식"
        loss = f"오늘 {kw}가 들어간 상태에서 추가 탄수·간식이 붙으면 격차가 고정되어 내일 복구 난도가 커질 수 있습니다."
        gain = "남은 식사를 단백질·채소 중심으로 보정하면 오늘 손실 폭을 줄이고 내일 붓기 반등을 막는 데 유리합니다."
        return loss, gain

    if (not meal.get("lunch_done", False)) and (not meal.get("dinner_done", False)):
        if (pace == "behind") and (delta is not None) and (delta > 0):
            loss = f"점심을 탄수 위주로 두면 현재 {delta:.2f}kg 격차가 저녁 과식으로 더 벌어질 가능성이 큽니다."
            gain = "점심을 단백질·채소 중심으로 두면 저녁 허기를 낮춰 오늘 격차 확대를 막는 데 유리합니다."
        else:
            loss = "점심을 탄수 위주로 두면 오후 허기가 커져 저녁 과식으로 이어질 가능성이 큽니다."
            gain = "점심을 단백질·채소 중심으로 두면 저녁 폭식을 줄이고 내일 붓기 감소에 유리합니다."
        return loss, gain

    if (not workout.get("worked_out_today", False)) and scheduled_slot:
        st = str(scheduled_slot.get("start") or "")
        ed = str(scheduled_slot.get("end") or "")
        window = f"{st}~{ed}" if st and ed else "오늘 예정 시간대"
        if (pace == "behind") and (days_left <= 0):
            loss = f"오늘은 마감일이라 {window} {lesson_label} 미실행 자체가 손실입니다. 이 세션을 비우면 반등폭을 그대로 떠안게 됩니다."
            gain = f"{window} {lesson_label}만 지켜도 마감일 손실을 줄이고 내일 붓기 반등을 낮추는 데 도움이 됩니다."
        elif (pace == "behind") and (req is not None):
            loss = f"{window} {lesson_label}을 놓치면 필요한 일일 페이스({req:.2f}kg/일) 대비 오늘 누적 손실이 커질 수 있습니다."
            gain = f"{window} {lesson_label}만 지켜도 당일 소모를 확보해 내일 체중 반등을 낮추는 데 도움이 됩니다."
        else:
            loss = f"{window} {lesson_label}을 비우면 오늘 소모가 0에 가까워져 체중 흐름이 둔해질 수 있습니다."
            gain = f"{window} {lesson_label}만 지켜도 당일 소모를 확보해 밤 붓기 완화에 도움이 됩니다."
        return loss, gain

    if (not workout.get("worked_out_today", False)) and (enabled_now or enabled_later):
        if (pace == "behind") and (days_left <= 0):
            loss = "오늘은 마감일이라 필요 페이스보다 세션 미실행 자체가 손실입니다. 이 슬롯을 비우면 반등폭을 그대로 떠안게 됩니다."
            gain = "운동 슬롯에서 20분만 채워도 마감일 손실을 줄이고 내일 붓기 반등을 낮추는 데 도움이 됩니다."
        elif (pace == "behind") and (req is not None):
            loss = f"운동 슬롯을 비우면 필요한 일일 페이스({req:.2f}kg/일) 대비 오늘 누적 손실이 커질 수 있습니다."
            gain = "운동 슬롯에서 20분만 채워도 당일 소모를 확보해 내일 체중 반등을 낮추는 데 도움이 됩니다."
        else:
            loss = "운동 슬롯을 비우면 오늘 소모가 0에 가까워져 체중 흐름이 둔해질 수 있습니다."
            gain = "운동 슬롯에서 20분만 채워도 당일 소모를 확보해 밤 붓기 완화에 도움이 됩니다."
        return loss, gain

    if over_kcal:
        loss = "추가 섭취가 이어지면 오늘 칼로리 초과가 커져 내일 체중 반등폭이 커질 수 있습니다."
        gain = "추가 섭취를 멈추면 초과 칼로리를 제한해 내일 반등폭을 줄이는 데 유리합니다."
        return loss, gain

    loss = "핵심 행동이 뒤로 밀리면 남은 시간 선택지가 줄어 페이스 복구 여지가 작아질 수 있습니다."
    gain = "핵심 행동 1개만 먼저 확정하면 오늘 페이스를 안정적으로 유지하는 데 유리합니다."
    return loss, gain


def _build_contextual_why_line(daily_state):
    sprint = (daily_state or {}).get("sprint", {}) or {}
    meal = (daily_state or {}).get("meal_done", {}) or {}
    workout = (daily_state or {}).get("workout_done", {}) or {}
    intake = (daily_state or {}).get("intake_today", {}) or {}

    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    delta = _safe_float(sprint.get("weight_delta"), None)
    req = _safe_float(sprint.get("required_daily_pace"), None)
    days_left = _safe_int(sprint.get("days_remaining"), 0)
    kcal_delta = _safe_int(intake.get("kcal_delta_today", 0), 0)
    lunch_done = bool(meal.get("lunch_done", False))
    dinner_done = bool(meal.get("dinner_done", False))
    worked = bool(workout.get("worked_out_today", False))

    if days_left <= 0:
        return "왜 이걸 우선하냐면: 오늘은 스프린트 마감일이라 페이스 숫자보다 추가 반등을 막는 선택이 내일 체중을 가장 크게 좌우하기 때문입니다."

    if (pace == "behind") and (delta is not None) and (delta > 0):
        if req is not None:
            return (
                f"왜 이걸 우선하냐면: 현재 {delta:.2f}kg 뒤처진 상태라 남은 {days_left}일 동안 "
                f"하루 {req:.2f}kg 페이스를 맞추려면 오늘 선택이 바로 반영되기 때문입니다."
            )
        return f"왜 이걸 우선하냐면: 현재 {delta:.2f}kg 뒤처진 상태라 오늘 흐름이 그대로 격차로 남기 때문입니다."

    if (not lunch_done) and (not dinner_done):
        return "왜 이걸 우선하냐면: 점심 구성이 흔들리면 저녁 허기가 커져 하루 전체가 무너지기 쉬운 구간이기 때문입니다."

    if (not worked):
        return "왜 이걸 우선하냐면: 오늘 운동 기록이 0회면 체중보다 먼저 컨디션과 수면 리듬이 무너지기 쉽기 때문입니다."

    if kcal_delta >= 250:
        return "왜 이걸 우선하냐면: 이미 섭취 초과 구간이라 추가 선택 1~2개가 내일 체중 반등폭을 키우기 때문입니다."

    if dinner_done:
        return "왜 이걸 우선하냐면: 지금은 더 잘 먹는 것보다 추가 섭취를 멈추는 쪽이 내일 상태에 더 크게 작용하기 때문입니다."

    return "왜 이걸 우선하냐면: 지금 구간은 작은 선택 1개가 내일 체중·컨디션에 가장 크게 반영되는 시간대이기 때문입니다."


def build_forced_next_action_from_state(daily_state):
    slots = daily_state.get("available_slots", []) or []
    enabled_now = [s for s in slots if s.get("enabled") and s.get("active_now")]
    enabled_later = [s for s in slots if s.get("enabled") and (not s.get("active_now"))]
    cal = daily_state.get("calendar_flags", {}) or {}

    def _slot_session_label(slot):
        slot_id = str((slot or {}).get("slot_id", "") or "")
        if not bool((slot or {}).get("scheduled_workout", False)):
            return ""
        if slot_id == "lunch_window" and bool(cal.get("lunch_lesson_scheduled", False)):
            return "테니스 레슨 세션"
        if slot_id == "evening_window" and bool(cal.get("dinner_lesson_scheduled", False)):
            return "테니스 레슨 세션"
        return "캘린더 운동 세션"

    if enabled_now:
        s = enabled_now[0]
        label = str(s.get("label") or s.get("slot_id") or "다음 슬롯")
        start = str(s.get("start") or "")
        end = str(s.get("end") or "")
        session_label = _slot_session_label(s)
        if session_label:
            return (
                f"현 시점 우선 1개: {label}({start}-{end})에 잡힌 {session_label}을 그대로 수행하세요. "
                "추가 유산소·근력 루틴을 붙이지 말고 해당 세션 완료 여부로 하루를 판정하면 됩니다."
            )
        return (
            f"현 시점 우선 1개: {label}({start}-{end})를 오늘의 1순위 운동 슬롯으로 고정하세요. "
            "해당 시간대에는 20분 걷기부터 시작해 기록까지 마무리하면 됩니다."
        )
    if enabled_later:
        s = enabled_later[0]
        label = str(s.get("label") or s.get("slot_id") or "다음 슬롯")
        start = str(s.get("start") or "")
        end = str(s.get("end") or "")
        session_label = _slot_session_label(s)
        if session_label:
            return (
                f"현 시점 우선 1개: {label}({start}-{end})에 잡힌 {session_label}을 우선순위로 고정하세요. "
                "추가 유산소·근력 루틴을 붙이지 말고 해당 세션 완료 여부로 오늘을 판정하면 됩니다."
            )
        return (
            f"현 시점 우선 1개: {label}({start}-{end}) 시작 시각을 운동 시작선으로 잡으세요. "
            "그 시간대에는 20분 걷기 1회를 우선 완료하는 방향이 좋습니다."
        )
    return "현 시점 우선 1개: 오늘은 추가 섭취를 멈추고 수면 회복을 우선순위로 두세요."


def _normalize_warning_text(warns, daily_state):
    raw = str(warns or "").strip()
    # API/모델/패키지 실패 원인은 덮어쓰지 않고 그대로 노출한다.
    if _is_infra_error_text(raw):
        return raw
    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False, "high_hits": []})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    _risk_level_fn = globals().get("_resolve_food_risk_tone_level", lambda _s, _r: "none")
    food_risk = _food_risk_fn(daily_state)
    alcohol_risk = _alcohol_risk_fn(daily_state)
    sprint = (daily_state or {}).get("sprint", {}) or {}
    intake = (daily_state or {}).get("intake_today", {}) or {}
    meal = (daily_state or {}).get("meal_done", {}) or {}
    workout = (daily_state or {}).get("workout_done", {}) or {}

    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    gap = _safe_float(sprint.get("weight_delta"), None)
    days_left = _safe_int(sprint.get("days_remaining"), 0)
    req = _safe_float(sprint.get("required_daily_pace"), None)
    kcal_delta = _safe_int(intake.get("kcal_delta_today", 0), 0)
    worked = bool(workout.get("worked_out_today", False))
    dinner_done = bool(meal.get("dinner_done", False))

    generic_signals = [
        "청량하고 가벼운",
        "집중하세요",
        "목표 대비 지연 상태이므로",
        "하루 목표 달성",
    ]
    is_generic = (not raw) or any(g in raw for g in generic_signals)

    risk_tone = _risk_level_fn(daily_state, food_risk)
    if bool(alcohol_risk.get("has_alcohol", False)):
        return (
            "음주가 기록된 날은 스프린트 관점에서 절대 금물 구간입니다. "
            "오늘은 추가 음주·야식을 즉시 차단하고 수분·수면 회복에 집중해야 합니다."
        )

    if bool(food_risk.get("has_high", False)):
        kw = ", ".join(list(food_risk.get("high_hits", []) or [])[:3]) or "고열량 가공식"
        if risk_tone == "high":
            return (
                f"오늘 섭취({kw})는 현재 페이스에서 손실이 큰 선택입니다. "
                "남은 식사는 탄수 추가를 멈추고 단백질·채소로 보정해야 격차 확대를 막을 수 있습니다."
            )
        return (
            f"오늘 섭취({kw})가 포함되어 있어 남은 끼니에서 균형 보정이 필요합니다. "
            "저녁은 탄수를 줄이고 단백질·채소 중심으로 정리해 주세요."
        )

    if not is_generic:
        return raw

    if (pace == "behind") and (gap is not None) and (gap > 0):
        if req is not None:
            return (
                f"목표 대비 {gap:.2f}kg 뒤처진 상태입니다. 오늘 저녁 추가 탄수·야식이 들어가면 "
                f"남은 {days_left}일 필요 페이스({req:.2f}kg/일) 복구 난도가 크게 올라갑니다."
            )
        return f"목표 대비 {gap:.2f}kg 뒤처진 상태입니다. 오늘 추가 섭취가 들어가면 격차가 고정될 위험이 큽니다."

    if kcal_delta >= 250:
        return (
            f"현재 섭취가 목표보다 {kcal_delta}kcal 초과입니다. "
            "지금 추가 간식 1~2회가 내일 체중 반등폭을 키울 수 있습니다."
        )

    if (not worked) and dinner_done:
        return "오늘은 운동보다 추가 섭취 차단이 더 중요합니다. 저녁 이후 간식·야식이 들어가면 내일 붓기 반등 위험이 큽니다."

    if (not worked):
        return "오늘 운동 미실행 상태입니다. 최소 20분 걷기 1회를 못 채우면 수면 리듬과 내일 컨디션이 먼저 흔들릴 수 있습니다."

    return "오늘은 큰 무리보다 추가 섭취를 막고 수면 회복을 확보하는 쪽이 내일 체중 방어에 유리합니다."


def _build_personalized_blocking_line(daily_state):
    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False, "high_hits": []})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    _risk_level_fn = globals().get("_resolve_food_risk_tone_level", lambda _s, _r: "none")
    food_risk = _food_risk_fn(daily_state)
    alcohol_risk = _alcohol_risk_fn(daily_state)
    risk_tone = _risk_level_fn(daily_state, food_risk)
    sprint = (daily_state or {}).get("sprint", {}) or {}
    intake = (daily_state or {}).get("intake_today", {}) or {}
    meal = (daily_state or {}).get("meal_done", {}) or {}
    workout = (daily_state or {}).get("workout_done", {}) or {}

    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    gap = _safe_float(sprint.get("weight_delta"), None)
    days_left = _safe_int(sprint.get("days_remaining"), 0)
    req = _safe_float(sprint.get("required_daily_pace"), None)
    kcal_delta = _safe_int(intake.get("kcal_delta_today", 0), 0)

    lunch_done = bool(meal.get("lunch_done", False))
    dinner_done = bool(meal.get("dinner_done", False))
    worked = bool(workout.get("worked_out_today", False))

    if bool(alcohol_risk.get("has_alcohol", False)):
        return "오늘 방어선: 음주가 이미 들어간 날이라 추가 음주·야식이 붙으면 내일 반등폭이 급격히 커지고 복구 난도가 크게 올라갑니다."

    if bool(food_risk.get("has_high", False)):
        kw = ", ".join(list(food_risk.get("high_hits", []) or [])[:3]) or "고열량 가공식"
        if risk_tone == "high":
            return f"오늘 방어선: {kw} 섭취가 이미 들어간 상태라 남은 끼니에서 탄수·간식이 추가되면 내일 반등폭이 빠르게 커질 수 있습니다."
        return f"오늘 방어선: {kw}가 있었던 만큼 남은 끼니는 단순하게 가져가야 내일 반등폭을 줄일 수 있습니다."

    if (pace == "behind") and (gap is not None) and (gap > 0):
        if days_left <= 0:
            return (
                f"오늘 방어선: 마감일 상태에서 {gap:.2f}kg 격차가 남아 있어, "
                "추가 섭취·운동 미실행이 겹치면 손실이 내일 체중 반등으로 바로 고정될 수 있습니다."
            )
        if req is not None:
            return (
                f"오늘 방어선: 지금 식사·운동이 흔들리면 {gap:.2f}kg 격차가 내일 고정되고, "
                f"남은 {days_left}일 필요 페이스({req:.2f}kg/일)가 더 가팔라집니다."
            )
        return f"오늘 방어선: 지금 흔들리면 {gap:.2f}kg 격차가 내일 체중에 그대로 남을 가능성이 큽니다."

    if (not lunch_done) and (not dinner_done):
        return "오늘 방어선: 점심 구성이 무너지면 저녁 허기가 커져 과식으로 이어질 확률이 높습니다."

    if kcal_delta >= 250:
        return f"오늘 방어선: 이미 {kcal_delta}kcal 초과 구간이라 추가 간식 1~2회가 내일 반등폭을 키울 수 있습니다."

    if dinner_done and (not worked):
        return "오늘 방어선: 저녁 이후 추가 섭취가 들어가면 운동 미실행 상태와 겹쳐 내일 컨디션이 먼저 무너질 수 있습니다."

    if not worked:
        return "오늘 방어선: 운동 기록이 0회로 끝나면 체중보다 먼저 수면 리듬과 집중력이 흔들릴 수 있습니다."

    return "오늘 방어선: 지금부터는 잘 먹는 것보다 추가 섭취를 멈추는 쪽이 내일 상태를 지키는 데 더 중요합니다."


def _build_personalized_gain_line(daily_state):
    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    _risk_level_fn = globals().get("_resolve_food_risk_tone_level", lambda _s, _r: "none")
    food_risk = _food_risk_fn(daily_state)
    alcohol_risk = _alcohol_risk_fn(daily_state)
    risk_tone = _risk_level_fn(daily_state, food_risk)
    sprint = (daily_state or {}).get("sprint", {}) or {}
    intake = (daily_state or {}).get("intake_today", {}) or {}
    meal = (daily_state or {}).get("meal_done", {}) or {}
    workout = (daily_state or {}).get("workout_done", {}) or {}

    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    gap = _safe_float(sprint.get("weight_delta"), None)
    req = _safe_float(sprint.get("required_daily_pace"), None)
    days_left = _safe_int(sprint.get("days_remaining"), 0)
    kcal_delta = _safe_int(intake.get("kcal_delta_today", 0), 0)

    lunch_done = bool(meal.get("lunch_done", False))
    worked = bool(workout.get("worked_out_today", False))

    if bool(alcohol_risk.get("has_alcohol", False)):
        return "오늘 이득: 지금부터 추가 음주·야식을 끊으면 내일 반등폭을 줄이고 컨디션 붕괴를 막는 데 가장 큰 효과가 있습니다."

    if bool(food_risk.get("has_high", False)):
        if risk_tone == "high":
            return "오늘 이득: 남은 끼니를 단백질·채소로 고정하면 오늘 손실을 최소화하고 내일 반등폭을 확실히 줄일 수 있습니다."
        return "오늘 이득: 남은 끼니를 가볍게 정리하면 오늘 섭취 영향을 완만하게 눌러 내일 컨디션을 지킬 수 있습니다."

    if (pace == "behind") and (gap is not None) and (gap > 0) and (days_left <= 0):
        return "오늘 이득: 마감일에는 핵심 1개(운동 세션 실행+추가 섭취 차단)만 지켜도 내일 반등폭을 눈에 띄게 줄일 수 있습니다."

    if (pace == "behind") and (gap is not None) and (gap > 0):
        if req is not None:
            return (
                f"오늘 이득: 핵심 1개만 지켜도 격차 확대를 막아 필요 페이스({req:.2f}kg/일)를 "
                f"현실 범위로 유지할 수 있습니다."
            )
        return "오늘 이득: 핵심 1개만 지켜도 격차 확대를 막아 복구 난도를 크게 낮출 수 있습니다."

    if not lunch_done:
        return "오늘 이득: 점심을 단백질·채소로 고정하면 저녁 허기가 줄어 야식 확률을 낮출 수 있습니다."

    if not worked:
        return "오늘 이득: 20~30분 걷기 1회만 채워도 내일 붓기와 피로 반등폭을 눈에 띄게 줄일 수 있습니다."

    if kcal_delta >= 250:
        return "오늘 이득: 추가 섭취를 멈추면 내일 체중 반등폭을 줄이고 컨디션 회복 속도를 높일 수 있습니다."

    if days_left > 0:
        return f"오늘 이득: 남은 {days_left}일 동안 현재 흐름을 지키면 불필요한 극단 플랜 없이도 페이스 유지가 가능합니다."

    return "오늘 이득: 지금 선택을 단순화하면 내일 체중과 컨디션을 동시에 안정적으로 가져갈 수 있습니다."


def _build_critical_now_line(daily_state):
    state = daily_state or {}
    sprint = state.get("sprint", {}) or {}
    intake = state.get("intake_today", {}) or {}
    workout = state.get("workout_done", {}) or {}
    cal = state.get("calendar_flags", {}) or {}
    _food_risk_fn = globals().get("_detect_today_food_risk", lambda _s: {"has_high": False, "high_hits": []})
    _alcohol_risk_fn = globals().get("_detect_today_alcohol_risk", lambda _s: {"has_alcohol": False})
    food_risk = _food_risk_fn(state)
    alcohol_risk = _alcohol_risk_fn(state)
    slots = list(state.get("available_slots", []) or [])


    pace = str(sprint.get("pace_status", "") or "").strip().lower()
    gap = _safe_float(sprint.get("weight_delta"), None)
    req = _safe_float(sprint.get("required_daily_pace"), None)
    days_left = _safe_int(sprint.get("days_remaining"), 0)
    kcal_now = _safe_int(intake.get("kcal_est_today", 0), 0)
    kcal_target = _safe_int(intake.get("kcal_target_today", DEFAULT_DAILY_KCAL_TARGET), DEFAULT_DAILY_KCAL_TARGET)
    worked = bool(workout.get("worked_out_today", False))
    dinner_workout = bool(cal.get("dinner_workout_scheduled", False))
    dinner_lesson = bool(cal.get("dinner_lesson_scheduled", False))
    high_hits = list(food_risk.get("high_hits", []) or [])
    has_high_food = bool(food_risk.get("has_high", False))
    has_alcohol = bool(alcohol_risk.get("has_alcohol", False))

    evening_slot = next((s for s in slots if str(s.get("slot_id", "")) == "evening_window"), None)
    ev_start = str(cal.get("dinner_workout_start") or str((evening_slot or {}).get("start", "") or "19:00"))
    ev_end = str(cal.get("dinner_workout_end") or str((evening_slot or {}).get("end", "") or "23:59"))

    prefix = "핵심: "
    kcal_part = f"현재 섭취 {kcal_now}kcal(목표 {kcal_target}kcal)" if kcal_target > 0 else f"현재 섭취 {kcal_now}kcal"
    if has_alcohol:
        risk_part = "오늘 음주가 이미 기록되어 반등 위험이 높습니다."
    elif has_high_food:
        kw = ", ".join(high_hits[:2]) if high_hits else "고열량 섭취"
        risk_part = f"오늘 '{kw}' 섭취가 이미 들어간 상태입니다."
    else:
        risk_part = ""

    if dinner_workout and (not worked):
        dinner_session_name = "테니스 레슨 일정" if dinner_lesson else "운동 일정"
        risk_prefix = f"{risk_part} " if risk_part else ""
        if (pace == "behind") and (days_left <= 0):
            return (
                f"{prefix}{risk_prefix}저녁 {ev_start}~{ev_end} {dinner_session_name}이 이미 잡혀 있습니다. "
                "오늘은 스프린트 마감일이라 이 세션을 미실행하면 손실이 내일 반등으로 바로 고정될 수 있습니다. "
                f"{kcal_part}라서 저녁은 보정식 중심이 유리합니다."
            )
        if (pace == "behind") and (req is not None):
            return (
                f"{prefix}{risk_prefix}저녁 {ev_start}~{ev_end} {dinner_session_name}이 이미 잡혀 있습니다. "
                f"이 세션을 미실행하면 남은 {days_left}일 필요 페이스가 {req:.2f}kg/일로 더 가팔라집니다. "
                f"{kcal_part}라서 저녁은 보정식 중심이 유리합니다."
            )
        return (
            f"{prefix}{risk_prefix}저녁 {ev_start}~{ev_end} {dinner_session_name}이 이미 잡혀 있습니다. "
            f"오늘 결과는 이 세션 실행 여부가 거의 결정합니다. {kcal_part}라 저녁은 과식 방어가 핵심입니다."
        )

    if (pace == "behind") and (gap is not None) and (req is not None):
        risk_prefix = f"{risk_part} " if risk_part else ""
        return (
            f"{prefix}{risk_prefix}현재 {gap:.2f}kg 뒤처짐 상태이며 남은 {days_left}일 필요 페이스는 {req:.2f}kg/일입니다. "
            f"지금 선택이 그대로 내일 격차로 고정될 수 있습니다."
        )

    if not worked:
        risk_prefix = f"{risk_part} " if risk_part else ""
        return (
            f"{prefix}{risk_prefix}오늘 운동 기록이 아직 0회입니다. "
            f"지금 한 세션을 채우지 않으면 체중보다 먼저 수면·피로 지표가 흔들릴 가능성이 큽니다."
        )

    risk_prefix = f"{risk_part} " if risk_part else ""
    return (
        f"{prefix}{risk_prefix}오늘 기록 흐름은 유지 중이지만 {kcal_part} 기준에서 저녁 선택이 내일 체중 변동폭을 좌우합니다."
    )


def validate_action_plan_output(result, daily_state):
    if not isinstance(result, dict):
        return result

    # 강제 문장 삽입을 최소화하고, 사실/가독성/중복만 정리한다.
    _apply_guard = globals().get("_apply_calendar_fact_guard", lambda t, _s: str(t or ""))
    _rewrite_vague = globals().get("_rewrite_vague_korean", lambda t: str(t or ""))
    _humanize = globals().get("humanize_action_text", lambda t: str(t or ""))
    _polish = globals().get("polish_korean_coaching_text", lambda t: str(t or ""))
    _dedupe_sent = globals().get("_dedupe_consecutive_sentences", lambda t: str(t or ""))
    _warn_norm = globals().get("_normalize_warning_text", lambda w, _s: str(w or ""))
    _critical_now = globals().get("_build_critical_now_line", lambda _s: "")
    _forced_next = globals().get("build_forced_next_action_from_state", lambda _s: "")

    text = str(result.get("next_actions", "") or "")
    warns = str(result.get("warnings", "") or "")
    analysis = str(result.get("current_analysis", "") or "")
    cal = (daily_state or {}).get("calendar_flags", {}) or {}
    dinner_workout = bool(cal.get("dinner_workout_scheduled", False))
    dinner_lesson = bool(cal.get("dinner_lesson_scheduled", False))
    slots = list((daily_state or {}).get("available_slots", []) or [])
    evening_slot = next((s for s in slots if str(s.get("slot_id", "")) == "evening_window"), None)
    ev_start = str(cal.get("dinner_workout_start") or str((evening_slot or {}).get("start", "") or "19:00"))
    ev_end = str(cal.get("dinner_workout_end") or str((evening_slot or {}).get("end", "") or "23:59"))

    def _strip_heading_noise(src):
        s = str(src or "")
        s = re.sub(r"\b\d{1,2}:\d{2}\s*기준\b", "", s)
        s = re.sub(r"^\s*(지금 상황|현 시점 제안)\s*[:：]\s*", "", s, flags=re.MULTILINE)
        s = re.sub(r"\s{2,}", " ", s).strip()
        return s

    def _keyset(src):
        parts = re.split(r"(?<=[\.\!\?])\s+|\n+", str(src or "").strip())
        out = set()
        for p in parts:
            k = str(p or "").strip().lower()
            if not k:
                continue
            k = re.sub(r"^\s*[-•]\s*", "", k)
            k = re.sub(r"^\s*(핵심|현재 상태 요약|현 시점 우선 1개|왜 이걸 우선하냐면|오늘 방어선|오늘 이득)\s*:\s*", "", k)
            k = re.sub(r"\b\d{1,2}:\d{2}\s*기준\b", "", k)
            k = re.sub(r"\s+", " ", k).strip(" .")
            if k:
                out.add(k)
        return out

    def _drop_overlap(action_text, analysis_text):
        a_keys = _keyset(analysis_text)
        kept = []
        for ln in re.split(r"\n+", str(action_text or "").strip()):
            raw = ln.strip()
            if not raw:
                continue
            key = re.sub(r"^\s*[-•]\s*", "", raw).strip().lower()
            key = re.sub(r"^\s*(핵심|현재 상태 요약|현 시점 우선 1개|왜 이걸 우선하냐면|오늘 방어선|오늘 이득)\s*:\s*", "", key)
            key = re.sub(r"\s+", " ", key).strip(" .")
            if key and key in a_keys:
                continue
            kept.append(raw)
        return "\n".join(kept).strip()

    text = _strip_heading_noise(text.replace("초저녁", "저녁"))
    warns = _strip_heading_noise(warns.replace("초저녁", "저녁"))
    analysis = _strip_heading_noise(analysis.replace("초저녁", "저녁"))

    # 사실 보정: 캘린더 저녁 운동 시간창은 실제 겹침 시간으로 교정한다.
    if dinner_workout:
        text = re.sub(r"\b19:00\s*~\s*23:59\b", f"{ev_start}~{ev_end}", text)
        analysis = re.sub(r"\b19:00\s*~\s*23:59\b", f"{ev_start}~{ev_end}", analysis)

    # 용어 보정: 사용자 표현 기준으로 "자유 슬롯 제한"은 자연어로 치환
    text = re.sub(r"저녁\s*시간대\s*자유\s*슬롯이\s*제한됩니다", "저녁 시간 선택지가 좁습니다", text)
    analysis = re.sub(r"저녁\s*시간대\s*자유\s*슬롯이\s*제한됩니다", "저녁 시간 선택지가 좁습니다", analysis)

    # 레슨 일정이 있으면 "유산소+근력" 같은 추가 루틴 강요 문구를 세션 수행 문구로 보정
    if dinner_lesson:
        def _rewrite_lesson_mode(src):
            s = str(src or "")
            s = re.sub(r"유산소\s*\d+\s*분\s*\+\s*근력\s*\d+\s*분", "캘린더에 잡힌 테니스 레슨 세션", s)
            s = re.sub(r"근력\s*\d+\s*분", "레슨 세션", s)
            s = re.sub(r"유산소\s*\d+\s*분", "레슨 세션", s)
            s = re.sub(r"20\s*분\s*걷기", "레슨 세션", s)
            s = re.sub(r"운동\s*30\s*분\s*이상", "레슨 세션", s)
            return s
        text = _rewrite_lesson_mode(text)
        analysis = _rewrite_lesson_mode(analysis)

    # 사실 가드 + 모호표현 축소
    analysis = _apply_guard(analysis, daily_state)
    text = _apply_guard(text, daily_state)
    analysis = _rewrite_vague(analysis)
    text = _rewrite_vague(text)

    warns = _rewrite_vague(warns)
    warns = _warn_norm(warns, daily_state)
    warns = _dedupe_sent(warns)

    # 출력이 비었을 때만 최소 안전 문장 보강
    if not analysis.strip():
        analysis = str(_critical_now(daily_state) or "").strip()
    if not text.strip():
        text = str(_forced_next(daily_state) or "").strip()
    if not analysis.strip():
        analysis = "오늘 데이터 기준으로 리스크와 우선순위를 다시 점검해 주세요."
    if not text.strip():
        text = "현 시점에서 가장 중요한 행동 1개를 확정하고 실행 조건(시간·분량)을 붙여 완료하세요."

    # 최종 중복/형식 정리
    analysis = _sanitize_plan_lines(analysis)
    text = _sanitize_plan_lines(text)
    analysis = _dedupe_sent(analysis)
    text = _dedupe_sent(text)
    text = _drop_overlap(text, analysis)
    text = "\n".join([ln for ln in re.split(r"\n+", text) if ln.strip()][:5]).strip()
    if not text:
        text = str(_forced_next(daily_state) or "").strip()

    result["current_analysis"] = _polish(_humanize(analysis))
    result["next_actions"] = _polish(_humanize(text))
    result["warnings"] = _polish(warns.strip())
    return result


def format_ai_error_message(e):
    msg = str(e or "").strip()
    low = msg.lower()
    if ("anthropic" in low) and (("api key" in low) or ("authentication" in low) or ("unauthorized" in low)):
        return "Claude API 인증 오류입니다. ANTHROPIC_API_KEY를 확인해 주세요."
    if ("insufficient_quota" in low) or ("error code: 429" in low) or ("quota" in low):
        return "OpenAI API 한도(429) 문제입니다. 결제/프로젝트 키를 확인해 주세요."
    if ("model" in low) and (("not found" in low) or ("does not exist" in low) or ("permission" in low)):
        return "모델 접근 권한 오류입니다. 사용 가능한 모델로 변경이 필요합니다."
    if not msg:
        return "AI 호출 오류가 발생했습니다."
    return f"AI 호출 오류: {msg[:220]}"


def _is_infra_error_text(msg):
    low = str(msg or "").lower()
    infra_tokens = [
        "api key", "authentication", "unauthorized", "forbidden",
        "quota", "429", "rate limit", "timeout", "timed out",
        "model", "not found", "does not exist", "permission",
        "anthropic", "openai", "network", "connection",
        "package not installed", "no module named",
    ]
    return any(t in low for t in infra_tokens)


def _is_model_error_text(msg):
    low = str(msg or "").lower()
    return ("model" in low) and (
        ("not found" in low) or ("does not exist" in low) or ("permission" in low)
    )


def _unique_keep_order(items):
    out, seen = [], set()
    for x in list(items or []):
        s = str(x or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _anthropic_model_candidates(preferred=None):
    return _unique_keep_order([
        preferred,
        os.getenv("ANTHROPIC_MODEL", ""),
        "claude-sonnet-4-6",
        "claude-sonnet-4-5",
        "claude-3-7-sonnet-latest",
        "claude-3-5-sonnet-latest",
    ])


def _anthropic_messages_create_with_fallback(client, *, preferred_model, max_tokens, temperature, messages):
    last_error = None
    for model_name in _anthropic_model_candidates(preferred_model):
        try:
            return client.messages.create(
                model=model_name,
                max_tokens=int(max_tokens),
                temperature=float(temperature),
                messages=messages,
            )
        except Exception as e:
            last_error = e
            # 모델 ID/권한 에러는 다음 후보를 시도하고,
            # 그 외 에러는 즉시 상위로 전달한다.
            if _is_model_error_text(e):
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("Anthropic model candidates were empty")


def _extract_json_object_text(raw_text):
    txt = str(raw_text or "").strip()
    if not txt:
        return ""
    if txt.startswith("{") and txt.endswith("}"):
        return txt
    m = re.search(r"\{[\s\S]*\}", txt)
    return m.group(0).strip() if m else ""


def _extract_json_codeblock_text(raw_text):
    txt = str(raw_text or "").strip()
    if not txt:
        return ""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", txt, flags=re.IGNORECASE)
    return (m.group(1) or "").strip() if m else ""


def _extract_balanced_json_object_text(raw_text):
    s = str(raw_text or "")
    if not s:
        return ""
    start = s.find("{")
    if start < 0:
        return ""
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "\"":
                in_str = False
            continue
        if ch == "\"":
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1].strip()
    return ""


def _parse_json_object_from_ai_text(raw_text):
    txt = str(raw_text or "").strip()
    if not txt:
        return None

    candidates = _unique_keep_order([
        txt,
        _extract_json_codeblock_text(txt),
        _extract_balanced_json_object_text(txt),
        _extract_json_object_text(txt),
    ])
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


def _resolve_provider(provider=None):
    p = str(provider or COACHING_PROVIDER or "anthropic").strip().lower()
    if p not in {"openai", "anthropic"}:
        p = "anthropic"
    return p


def _coaching_has_provider_key(provider=None):
    p = _resolve_provider(provider)
    if p == "anthropic":
        return bool(str(ANTHROPIC_API_KEY or "").strip())
    return bool(str(OPENAI_API_KEY or "").strip())


def _coaching_text_completion(
    prompt,
    provider=None,
    model_openai=None,
    model_anthropic=None,
    max_tokens=600,
    temperature=0.6,
):
    p = _resolve_provider(provider)
    if p == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("Anthropic API key is missing")
        try:
            import anthropic  # type: ignore
        except Exception as ie:
            raise RuntimeError(f"anthropic package not installed: {ie}")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = _anthropic_messages_create_with_fallback(
            client,
            preferred_model=str(model_anthropic or COACHING_MODEL_ANTHROPIC),
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = []
        for b in list(getattr(resp, "content", []) or []):
            t = getattr(b, "text", None)
            if t:
                parts.append(str(t))
        return "\n".join(parts).strip()

    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key is missing")
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=str(model_openai or COACHING_MODEL_OPENAI),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=int(max_tokens),
        temperature=float(temperature),
    )
    return str(response.choices[0].message.content or "").strip()


def _coaching_json_completion(
    prompt,
    provider=None,
    model_openai=None,
    model_anthropic=None,
    max_tokens=900,
    temperature=0.6,
):
    p = _resolve_provider(provider)
    if p == "anthropic":
        raw = _coaching_text_completion(
            prompt=prompt,
            provider="anthropic",
            model_anthropic=model_anthropic or COACHING_MODEL_ANTHROPIC,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        parsed = _parse_json_object_from_ai_text(raw)
        if parsed is not None:
            return parsed

        # 1회 자동 복구: Claude가 JSON 외 텍스트를 섞어 보낸 경우 JSON만 재생성
        repair_prompt = f"""
아래 텍스트를 의미 손실 없이 JSON object 1개로만 다시 작성하세요.
- 설명문/코드펜스/추가 텍스트 금지
- 최상위는 반드시 {{ ... }} 객체

원문:
{raw}
"""
        raw2 = _coaching_text_completion(
            prompt=repair_prompt,
            provider="anthropic",
            model_anthropic=model_anthropic or COACHING_MODEL_ANTHROPIC,
            max_tokens=min(int(max_tokens), 700),
            temperature=0.0,
        )
        parsed2 = _parse_json_object_from_ai_text(raw2)
        if parsed2 is not None:
            return parsed2
        raise RuntimeError("Claude response did not contain JSON object")

    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key is missing")
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=str(model_openai or COACHING_MODEL_OPENAI),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _action_plan_chat_completion_json(prompt):
    provider = str(ACTION_PLAN_PROVIDER or "openai").strip().lower()
    if provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("Anthropic API key is missing")
        try:
            import anthropic  # type: ignore
        except Exception as ie:
            raise RuntimeError(f"anthropic package not installed: {ie}")

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = _anthropic_messages_create_with_fallback(
            client,
            preferred_model=ACTION_PLAN_MODEL_ANTHROPIC,
            max_tokens=900,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = []
        for b in list(getattr(resp, "content", []) or []):
            t = getattr(b, "text", None)
            if t:
                parts.append(str(t))
        raw = "\n".join(parts).strip()
        parsed = _parse_json_object_from_ai_text(raw)
        if parsed is not None:
            return parsed
        raise RuntimeError("Claude response did not contain JSON object")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=ACTION_PLAN_MODEL_OPENAI,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def build_rule_based_action_plan(daily_state, daily_five_focus=None):
    lines = [
        "AI 응답 생성에 실패해 임시 플랜으로 전환했습니다. 아래 1개만 먼저 실행하세요.",
        build_forced_next_action_from_state(daily_state),
    ]
    xc = (daily_state.get("xc", {}) or {}).get("xc_value_kg")
    if xc is not None:
        lines.append(f"참고: 오늘 xC 목표 변화량은 {float(xc):.2f}kg입니다.")
    df_focus = daily_five_focus or {}
    if bool(df_focus.get("has_plan")):
        lines.append(f"DF 상태: {str(df_focus.get('summary_line', '')).strip()}")
        rem = list(df_focus.get("remaining_tasks", []) or [])
        if rem:
            top = rem[0]
            lines.append(f"다음 우선 DF: ({top.get('task_id','')}) {top.get('title','')}")
    return "\n".join(lines)


def format_coaching_readability_markdown(text):
    """
    Action Plan 출력 가독성 개선용:
    - ':' 기반 소제목 문장을 줄 분리
    - 항목별 불릿 + 굵은 소제목으로 렌더링
    """
    src = str(text or "").replace("\r\n", "\n").strip()
    if not src:
        return "- 없음"

    heading_tokens = [
        "지금 상황",
        "스프린트 현황",
        "현재 상태 요약",
        "현 시점 제안",
        "현 시점 우선 1개",
        "왜 이걸 우선하냐면",
        "오늘 방어선",
        "오늘 이득",
        "경고",
        "주의",
        "핵심",
        "지금 할 일",
    ]

    normalized = src
    normalized = re.sub(r"(\d{1,2})\s*:\s*(\d{2})", r"\1:\2", normalized)
    normalized = re.sub(r"\s*~\s*", "~", normalized)
    # ① ② ③ 같은 인라인 번호는 줄 분리
    normalized = re.sub(r"(?<!\n)\s*([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*", r"\n\1 ", normalized)
    # 특정 헤딩 토큰은 문장 중간에 있어도 강제로 줄 분리
    for token in heading_tokens:
        normalized = re.sub(
            rf"(?<!\n)\s*({re.escape(token)}\s*:)",
            r"\n\1",
            normalized,
        )

    # 문장부호 뒤에 오는 짧은 '라벨:' 패턴도 줄 분리
    normalized = re.sub(
        r"([.!?])\s+([가-힣A-Za-z][^:\n]{0,20}:)",
        r"\1\n\2",
        normalized,
    )

    lines = []
    for raw in normalized.split("\n"):
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        line = line.replace("~", "\\~")
        if line.startswith("- "):
            lines.append(line)
            continue

        num_m = re.match(r"^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*(.*)$", line)
        if num_m:
            n = num_m.group(1)
            b = num_m.group(2).strip()
            if b:
                lines.append(f"- **{n}** {b}")
            else:
                lines.append(f"- **{n}**")
            continue

        if ":" in line:
            head, body = line.split(":", 1)
            head = head.strip()
            body = body.strip()
            head = head.replace("~", "\\~")
            body = body.replace("~", "\\~")
            # 너무 긴 문장까지 헤딩 처리하지 않도록 제한
            if (1 <= len(head) <= 24) and re.search(r"[가-힣A-Za-z]", head) and (not re.search(r"\d", head)):
                if body:
                    lines.append(f"- **{head}:** {body}")
                else:
                    lines.append(f"- **{head}:**")
                continue

        lines.append(f"- {line}")

    return "\n".join(lines) if lines else "- 없음"


# ==========================================
# AI 생성부 (Daily Five / Check-in / Action Plan)
# ==========================================

def _df_has_concrete_detail(text):
    t = str(text or "")
    # 시간/분량/수치가 있으면 실행성이 높다고 간주
    return bool(re.search(r"\d+(\.\d+)?\s*(분|회|km|kg|g|kcal|잔|개|시|:\d{2}|ml|L|층)", t))


def _df_force_task_specificity(task, idx, progress, slots):
    t = dict(task or {})
    gap = _safe_float((progress or {}).get("weight_delta"), None)
    req = _safe_float((progress or {}).get("required_daily_pace"), None)
    pace = str((progress or {}).get("pace_status", "") or "").strip().lower()
    days_left = _safe_int((progress or {}).get("days_remaining"), 0)
    slot_list = list(slots or [])
    active_now = next((s for s in slot_list if bool(s.get("enabled")) and bool(s.get("active_now"))), None)
    enabled_later = next((s for s in slot_list if bool(s.get("enabled")) and (not bool(s.get("active_now")))), None)

    title = str(t.get("title", "") or "").strip()
    desc = str(t.get("description", "") or "").strip()
    why = str(t.get("why", "") or "").strip()

    if not title:
        if idx == 1 and active_now:
            title = f"{str(active_now.get('label') or '운동')} 슬롯 실행"
        elif idx == 1 and enabled_later:
            title = f"{str(enabled_later.get('label') or '운동')} 슬롯 고정"
        else:
            title = f"오늘 핵심 과제 {idx}"

    if not desc:
        if idx == 1 and active_now:
            st = str(active_now.get("start") or "")
            ed = str(active_now.get("end") or "")
            desc = f"{st}~{ed} 사이에 20~30분 운동 1회를 완료하세요."
        elif idx == 1 and enabled_later:
            st = str(enabled_later.get("start") or "")
            ed = str(enabled_later.get("end") or "")
            desc = f"{st}~{ed} 슬롯을 오늘 우선 블록으로 확정하고 20~30분 움직이세요."
        else:
            desc = "오늘 가능한 시간대에 20~30분 단위로 바로 실행 가능한 행동 1개를 끝내세요."

    if not _df_has_concrete_detail(desc):
        if idx == 1 and enabled_later:
            st = str(enabled_later.get("start") or "")
            ed = str(enabled_later.get("end") or "")
            desc = f"{desc} (예: {st}~{ed} 중 20~30분)"
        else:
            desc = f"{desc} (예: 20~30분 1회)"

    if not why:
        if (pace == "behind") and (gap is not None) and (gap > 0):
            why = f"지금 안 하면 {gap:.2f}kg 격차가 더 벌어질 손해가 있고, 오늘 실행하면 내일 반등을 줄이는 이득이 있습니다."
        elif req is not None:
            why = f"지금 안 하면 필요 페이스({req:.2f}kg/일) 대비 손해가 쌓이고, 지금 하면 내일 회복 폭을 키우는 이득이 있습니다."
        else:
            why = "지금 미루면 손해가 커지고, 오늘 끝내면 내일 컨디션을 지키는 이득이 있습니다."

    if ("손해" not in why) or (not any(x in why for x in ["이득", "유리", "좋아", "개선", "줄어"])):
        if (pace == "behind") and (gap is not None) and (gap > 0):
            why = f"{why} 안 하면 격차가 커지는 손해가 있고, 하면 오늘 격차 확대를 막는 이득이 있습니다."
        else:
            why = f"{why} 안 하면 내일 반등 손해가 생기고, 하면 내일 수치를 지키는 이득이 있습니다."

    t["title"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(title)))
    t["description"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(desc)))
    t["why"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(why)))
    t["task_id"] = str(t.get("task_id", f"task_{idx}") or f"task_{idx}")
    t["priority"] = max(1, min(5, _safe_int(t.get("priority", idx), idx)))
    t["category"] = str(t.get("category", "diet") or "diet")
    return t


def _normalize_daily_five_result(result, progress, slots, default_mode):
    out = dict(result or {})
    tasks = list(out.get("tasks", []) or [])
    tasks = [x for x in tasks if isinstance(x, dict)]
    tasks = tasks[:5]

    # 부족한 과제는 최소 보충
    while len(tasks) < 5:
        tasks.append({})

    normalized = []
    for i in range(1, 6):
        normalized.append(_df_force_task_specificity(tasks[i - 1], i, progress, slots))

    out["tasks"] = normalized

    msg = str(out.get("daily_message", "") or "").strip()
    pace = str((progress or {}).get("pace_status", "") or "").strip().lower()
    gap = _safe_float((progress or {}).get("weight_delta"), None)
    req = _safe_float((progress or {}).get("required_daily_pace"), None)
    days_left = _safe_int((progress or {}).get("days_remaining"), 0)
    day_now = _safe_int((progress or {}).get("day"), 0)
    if not msg:
        if (pace == "behind") and (gap is not None) and (gap > 0):
            if req is not None:
                msg = (
                    f"오늘은 복구 우선 날입니다. 현재 격차 {gap:.2f}kg, 남은 필요 페이스는 {req:.2f}kg/일입니다."
                )
            else:
                msg = f"오늘은 복구 우선 날입니다. 현재 격차 {gap:.2f}kg를 더 키우지 않는 게 핵심입니다."
        elif req is not None:
            msg = f"오늘은 페이스 유지 날입니다. 남은 {days_left}일 동안 {req:.2f}kg/일 기준을 지킬 선택이 필요합니다."
        else:
            msg = "오늘은 핵심 1개를 먼저 끝내는 쪽이 가장 효과적입니다."
    out["daily_message"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(msg)))

    mode = str(out.get("today_training_mode", "") or "").strip().lower()
    if mode not in {"recovery", "build", "push"}:
        mode = str(default_mode or "build")
    out["today_training_mode"] = mode

    urg = str(out.get("urgency_level", "") or "").strip().lower()
    if urg not in {"high", "medium", "low"}:
        if (pace == "behind") and (gap is not None) and (gap > 0):
            urg = "high"
        else:
            urg = "medium"
    out["urgency_level"] = urg
    return out


@st.cache_data(ttl=3600*24)
def ai_generate_daily_five(date_key, sprint, current_status, context):
    if not sprint:
        return None

    progress = calculate_sprint_progress(sprint, current_status['weight'])
    if not progress:
        return None
    dt = datetime.strptime(date_key, '%Y-%m-%d')
    weekday = "Weekday (Work 06-19)" if dt.weekday() < 5 else "Weekend (Free)"

    # ✅ [FIX] calendar 원문 대신 slots만 전달
    slots = context.get("available_slots", [])
    slots_json = json.dumps(slots, ensure_ascii=False)
    yesterday_review = context.get("yesterday_workout_review")
    if not yesterday_review:
        try:
            df_action = pd.DataFrame(fetch_sheet_data("Action_Log"))
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
    korean_style_context = build_korean_style_context()

    prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

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
- 중언부언 금지: 같은 의미 반복 금지, 한 문장에 메시지 1개만 담으십시오.
- 사람 말투로 쓰되, '누구에게나 통하는 일반론' 대신 오늘 데이터와 일정에 박히는 문장으로 쓰십시오.
- 5개 모두 구체적이고 실행 가능한 과제로 작성하십시오.
- task_1은 반드시 '현 시점 기준 최우선 과제'로 작성하고, 슬롯이 없으면 대체 방어 과제를 제시하십시오.
- 각 과제는 "제목(title)" + "실행(description)" 두 요소만 명확히 작성하십시오.
- description에는 가능한 시간대/분량/장소 중 최소 2개를 포함해, 바로 행동 가능한 문장으로 작성하십시오.
- why에는 반드시 아래 2요소를 모두 포함하십시오:
  1) 지금 안 하면 생기는 손해
  2) 지금 하면 좋아지는 점
- "운동하십시오", "관리하세요" 같은 일반론 문장만 단독으로 쓰지 마십시오.
- 번역투/부자연스러운 표현(예: 과식 차단)을 피하고 자연스러운 한국어를 사용하십시오.
- 어제 운동 기록이 있으면 강점 1개 + 보완점 1개를 daily_message에 짧게 반영하십시오.
- today_training_mode는 오늘의 기본 방향(soft anchor)으로 제시하십시오.
- 출력 본문에 "지금 상황:" 같은 섹션 라벨은 넣지 마십시오.
- json 객체 1개만 출력하십시오.

[OUTPUT FORMAT - JSON ONLY]
{{
  "tasks": [
    {{
      "task_id": "task_1",
      "category": "workout/diet/recovery",
      "priority": 1,
      "title": "...",
      "description": "실행: ...",
      "why": "..."
    }}
  ],
  "daily_message": "...",
  "urgency_level": "high/medium/low",
  "today_training_mode": "recovery/build/push"
}}
"""

    try:
        result = _coaching_json_completion(
            prompt=prompt,
            provider=COACHING_PROVIDER,
            model_openai=COACHING_MODEL_OPENAI,
            model_anthropic=COACHING_MODEL_ANTHROPIC,
            max_tokens=1200,
            temperature=0.6,
        )
        result = _normalize_daily_five_result(result, progress, slots, default_mode)
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


def filter_out_df_logs(df_action):
    if df_action is None or getattr(df_action, "empty", True):
        return df_action
    if "Category" not in df_action.columns:
        return df_action
    try:
        cat = df_action["Category"].astype(str).str.upper()
        return df_action[~cat.str.contains("DF", na=False)].copy()
    except Exception:
        return df_action


def prepare_full_context(df_health, df_action, current_weight, is_morning_fixed=False):
    now_kst = get_current_kst()
    mission = calculate_mission_status(current_weight)

    today_date_key = (now_kst - timedelta(days=1)).strftime('%Y-%m-%d') if now_kst.hour < 5 else now_kst.strftime('%Y-%m-%d')

    # DF 체크 로그는 코칭 품질보다는 진행률 집계용이므로 context에서 제외해 캐시 변동을 줄인다.
    df_action = filter_out_df_logs(df_action)

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
        # Prefer finalized sleep columns from Health_Log daily row.
        # Fall back to legacy Sleep_duration (hour) only if needed.
        latest_sleep = None
        for i in range(len(df_h_30) - 1, -1, -1):
            r = df_h_30.iloc[i]
            aslp_m = _safe_float_or_none(r.get("Slp_Aslp_m", None))
            inbed_m = _safe_float_or_none(r.get("Slp_InBed_m", None))
            eff_pct = _safe_float_or_none(r.get("Slp_Eff_pct", None))
            legacy_h = _safe_float_or_none(r.get("Sleep_duration", None))

            has_new = (aslp_m is not None and aslp_m > 0) or (inbed_m is not None and inbed_m > 0)
            has_legacy = legacy_h is not None and legacy_h > 0
            if has_new or has_legacy:
                latest_sleep = {
                    "row": r,
                    "aslp_m": aslp_m,
                    "inbed_m": inbed_m,
                    "eff_pct": eff_pct,
                    "legacy_h": legacy_h,
                }
                break

        if latest_sleep:
            dkey = str(latest_sleep["row"].get("Date", "") or "").strip()
            aslp_m = latest_sleep["aslp_m"]
            inbed_m = latest_sleep["inbed_m"]
            eff_pct = latest_sleep["eff_pct"]
            legacy_h = latest_sleep["legacy_h"]

            if aslp_m is None and legacy_h is not None:
                aslp_m = legacy_h * 60.0

            aslp_h = (aslp_m / 60.0) if (aslp_m is not None and aslp_m > 0) else None
            if aslp_h is not None:
                if inbed_m is not None and inbed_m > 0 and eff_pct is not None and eff_pct > 0:
                    sleep_info = f"Last Sleep({dkey}): {aslp_h:.1f}h (in-bed {inbed_m:.0f}m, eff {eff_pct:.0f}%)"
                elif inbed_m is not None and inbed_m > 0:
                    sleep_info = f"Last Sleep({dkey}): {aslp_h:.1f}h (in-bed {inbed_m:.0f}m)"
                else:
                    sleep_info = f"Last Sleep({dkey}): {aslp_h:.1f}h"

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
    def _contains_positive_signal(t: str) -> bool:
        return any(x in str(t or "") for x in ["좋은 점", "유리", "개선", "줄어", "완화", "낮출 수", "안정"])

    def _normalize_daily_checkin_result(result, sprint_progress, work_constraint):
        out = dict(result or {})
        signal = str(out.get("condition_signal", "") or "").strip().lower()
        if signal not in {"green", "yellow", "red"}:
            signal = "yellow"
        out["condition_signal"] = signal.capitalize()

        pace = str((sprint_progress or {}).get("pace_status", "") or "").strip().lower()
        gap = _safe_float((sprint_progress or {}).get("weight_delta"), None)
        req = _safe_float((sprint_progress or {}).get("required_daily_pace"), None)

        headline = str(out.get("headline", "") or "").strip()
        reason = str(out.get("headline_reason", "") or "").strip()
        analysis = str(out.get("analysis", "") or "").strip()
        workout = str(out.get("mission_workout", "") or "").strip()
        diet = str(out.get("mission_diet", "") or "").strip()
        recovery = str(out.get("mission_recovery", "") or "").strip()

        if not headline:
            if (pace == "behind") and (gap is not None) and (gap > 0):
                headline = f"오늘은 복구 모드가 필요합니다. 현재 격차 {gap:.2f}kg를 더 키우지 않는 게 우선입니다."
            elif signal == "red":
                headline = "오늘은 무리하지 말고 회복 우선으로 가는 날입니다."
            elif signal == "green":
                headline = "오늘은 밀어도 되는 상태입니다. 핵심 1~2개만 확실히 실행하면 됩니다."
            else:
                headline = "오늘은 선택 하나가 내일 컨디션을 바꾸는 구간입니다."

        if not reason:
            reason = f"현재 지표는 HRV {hrv:.0f}, RHR {rhr:.0f}, 체중 {weight:.1f}kg 기준입니다."

        if not analysis:
            analysis = "최근 기록을 보면 오늘은 식사와 운동 타이밍을 단순하게 잡는 편이 유리합니다."
        if ("HRV" not in analysis) and ("RHR" not in analysis) and ("체중" not in analysis):
            analysis = f"{analysis} (현재 지표: HRV {hrv:.0f}, RHR {rhr:.0f}, 체중 {weight:.1f}kg)"

        if ("손해" not in analysis) and ("위험" not in analysis):
            if (pace == "behind") and (gap is not None) and (gap > 0):
                req_txt = f", 남은 필요 페이스 {req:.2f}kg/일" if req is not None else ""
                analysis = f"{analysis} 오늘 식사/운동이 흔들리면 격차 {gap:.2f}kg{req_txt} 구간이 더 악화될 손해가 있습니다."
            else:
                analysis = f"{analysis} 오늘 루틴이 흔들리면 내일 붓기 반등이 커지는 손해가 생길 수 있습니다."
        if not _contains_positive_signal(analysis):
            analysis = f"{analysis} 반대로 오늘 한 끼만 정리해도 내일 수치가 확실히 가벼워질 가능성이 큽니다."

        if not workout:
            workout = (
                "퇴근 후 가능한 슬롯 1개를 고정해 20~30분만 움직이세요."
                if "Workday" in str(work_constraint)
                else "오전/오후 중 가능한 시간대에 30분 내외 유산소 1회를 먼저 끝내세요."
            )
        if not diet:
            diet = "점심은 단백질·채소 중심으로 두고 밥/면/튀김은 한 번 쉬어가세요."
        if not recovery:
            recovery = "취침 전 5분 스트레칭과 마그네슘 1정으로 회복 루틴을 고정하세요."

        if not _df_has_concrete_detail(workout):
            workout = f"{workout} (예: 20~30분 1회)"
        if not _df_has_concrete_detail(diet):
            diet = f"{diet} (예: 탄수 추가 없이 1끼)"
        if not _df_has_concrete_detail(recovery):
            recovery = f"{recovery} (예: 5~10분)"

        out["headline"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(headline)))
        out["headline_reason"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(reason)))
        out["analysis"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(analysis)))
        out["mission_workout"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(workout)))
        out["mission_diet"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(diet)))
        out["mission_recovery"] = polish_korean_coaching_text(_dedupe_consecutive_sentences(_rewrite_vague_korean(recovery)))
        return out

    dt = datetime.strptime(date_key, '%Y-%m-%d')
    wc = "Workday(06-19 Work). No heavy gym during work." if dt.weekday() < 5 else "Weekend. Free."
    sprint_progress = None
    try:
        sprint = get_active_sprint()
        if sprint:
            sprint_progress = calculate_sprint_progress(sprint, float(weight))
    except Exception:
        sprint_progress = None
    sprint_ctx = {
        "day": _safe_int((sprint_progress or {}).get("day"), 0),
        "days_remaining": _safe_int((sprint_progress or {}).get("days_remaining"), 0),
        "pace_status": str((sprint_progress or {}).get("pace_status", "") or ""),
        "weight_delta": _safe_float((sprint_progress or {}).get("weight_delta"), None),
        "required_daily_pace": _safe_float((sprint_progress or {}).get("required_daily_pace"), None),
    }
    sprint_ctx_json = json.dumps(sprint_ctx, ensure_ascii=False)
    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()
    korean_style_context = build_korean_style_context()

    prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

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
SprintContext: {sprint_ctx_json}

[출력 원칙]
- 입력 사실과 모순되지 마십시오.
- 해석과 코칭 표현은 자율적으로 구성하십시오.
- 중언부언 금지: 같은 의미 반복 금지, 문장당 한 가지 메시지만 전달하십시오.
- 사람 말투로 쓰되, '누구에게나 통하는 일반론' 대신 오늘 데이터에 꽂히는 문장으로 작성하십시오.
- analysis에는 현재 지표(HRV/RHR/체중 중 1개 이상)와 스프린트 맥락(격차/남은일/필요페이스 중 1개 이상)을 포함하십시오.
- analysis에는 반드시 아래 2문장을 포함하십시오.
  1) 지금 안 하면 생기는 손해
  2) 지금 하면 좋아지는 점
- mission_workout/mission_diet/mission_recovery는 각각 시간대/행동/분량 중 최소 2개를 담은 실행문으로 작성하십시오.
- "관리하세요", "신경쓰세요", "준비하세요" 같은 모호한 문장만 단독으로 쓰지 마십시오.
- "지금 상황:", "현 시점 제안:" 같은 섹션 라벨은 출력에 넣지 마십시오.
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
        raw = _coaching_json_completion(
            prompt=prompt,
            provider=COACHING_PROVIDER,
            model_openai=COACHING_MODEL_OPENAI,
            model_anthropic=COACHING_MODEL_ANTHROPIC,
            max_tokens=1000,
            temperature=0.6,
        )
        return _normalize_daily_checkin_result(raw, sprint_progress, wc)
    except Exception as e:
        fallback = {
            "condition_signal": "Yellow",
            "headline": "생성 오류로 기본 코칭으로 전환했습니다.",
            "headline_reason": "모델/네트워크 이슈",
            "analysis": "AI 응답이 실패해 기본 규칙 기반 코칭으로 전환했습니다.",
            "mission_workout": "-",
            "mission_diet": "-",
            "mission_recovery": "-"
        }
        if str(e):
            fallback["analysis"] = f"{fallback['analysis']} 오류 메시지: {str(e)}"
        return _normalize_daily_checkin_result(fallback, sprint_progress, wc)

@st.cache_data(ttl=900)
def ai_generate_action_plan_cached(hrv, rhr, weight, date_key, slots_key, activity_sig, today_activities, available_slots, plan_version, daily_five_sig):
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
    now_kst = get_current_kst()

    try:
        df_health = pd.DataFrame(fetch_sheet_data("Health_Log"))
        df_action = pd.DataFrame(fetch_sheet_data("Action_Log"))
    except:
        df_health = pd.DataFrame()
        df_action = pd.DataFrame()

    date_key = get_mission_date_key()
    sprint = None
    progress = None
    try:
        sprint = get_active_sprint()
    except:
        sprint = None

    if sprint and (not df_health.empty):
        try:
            progress = calculate_sprint_progress(sprint, weight)
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

    daily_five_status = {
        "has_plan": False,
        "completed": 0,
        "total": 0,
        "completion_rate": 0.0,
    }
    daily_five_focus = {
        "has_plan": False,
        "completed": 0,
        "total": 0,
        "completion_rate": 0.0,
        "remaining_count": 0,
        "remaining_tasks": [],
        "summary_line": "DF 계획 없음",
        "signature": "no_plan",
    }
    if sprint:
        try:
            daily_five_focus = build_daily_five_focus_snapshot(date_key, sprint["sprint_id"], df_action)
            daily_five_status = {
                "has_plan": bool(daily_five_focus.get("has_plan", False)),
                "completed": int(daily_five_focus.get("completed", 0)),
                "total": int(daily_five_focus.get("total", 0)),
                "completion_rate": float(daily_five_focus.get("completion_rate", 0.0)),
            }
        except:
            pass

    daily_five_plan = {}
    try:
        if sprint:
            daily_five_plan = load_dailyfive_cache(date_key, sprint["sprint_id"]) or {}
    except:
        daily_five_plan = {}

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
    daily_five_focus_json = json.dumps(daily_five_focus, ensure_ascii=False, indent=2)
    yesterday_workout_review = daily_state.get("yesterday_workout_review", {}) or {}
    yesterday_workout_review_json = json.dumps(yesterday_workout_review, ensure_ascii=False, indent=2)
    prev_xc_feedback = daily_state.get("prev_xc_feedback", {}) or {}
    prev_xc_feedback_json = json.dumps(prev_xc_feedback, ensure_ascii=False, indent=2)
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
    korean_style_context = build_korean_style_context()

    prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

역할: 실시간 개인 코치
언어: 한국어 존댓말

핵심 원칙:
- 사용자는 "누구나 해당되는 일반론"을 싫어합니다. 지금 이 사람의 오늘 상태에 맞게 말하십시오.
- 데이터 해석은 날카롭게, 말투는 사람답고 자연스럽게 작성하십시오.
- 중언부언 금지: 같은 의미 반복 금지, 짧고 명확하게.
- 모호한 표현 금지: "자유 슬롯", "준비하세요", "건강한 메뉴" 같은 추상어를 쓰지 마십시오.
- 식사/음주 리스크가 실제로 있으면 강도 높은 피드백을 허용합니다(모욕/비난 금지).
- 하드 템플릿 문장을 복붙하지 말고 상황에 맞게 자율적으로 구성하십시오.
- 섹션 헤더 문구(예: "지금 상황:", "현 시점 제안:", "핵심:")를 본문에 다시 쓰지 마십시오.
- "HH:MM 기준" 같은 시각 표기를 본문에 넣지 마십시오. 상단 배지 시각만 사용합니다.
- 어제가 정크푸드/음주 손실일이면 current_analysis 첫 문장에서 그 손실과 오늘 메이크업 필요성을 분명히 말하십시오.

작성 가이드:
- current_analysis: 2~4문장. "왜 오늘이 이런 상태인지"를 현재 데이터로 설명.
- next_actions: 3~5줄. 각 줄은 실행 가능한 행동 1개 + 이유(손해/이득) 포함.
- warnings: 리스크가 있을 때만 1~2문장. 없으면 빈 문자열.
- 캘린더/시간 관련 내용은 available_slots와 daily_state 사실만 사용.
- 최근 로그에 정크푸드/음주가 있으면, current_analysis 첫 문장에서 그 사실과 오늘 손실을 짧게 명시하십시오.

현재 컨텍스트:
- coaching_mode: {coaching_mode}
- xc: {xc_value}
- xc_reason: {xc_reason_json}
- urgency: {urgency_json}
- intake_kcal_today: {kcal_now}
- kcal_target_today: {kcal_target_today}
- kcal_delta_today: {kcal_delta_today}
- kcal_balance_status: {kcal_balance_status}
- repeat_bad_food_days(d2~d0): {repeat_bad_food_days}
- repeat_bad_food_tags: {repeat_bad_food_tags_json}

YESTERDAY_WORKOUT_REVIEW:
{yesterday_workout_review_json}

PREV_XC_FEEDBACK:
{prev_xc_feedback_json}

TRAINING_ANCHOR:
{training_anchor_json}

SPRINT_STATUS:
{sprint_status_json}

DAILY_FIVE_STATUS:
{daily_five_status_json}

DAILY_FIVE_FOCUS:
{daily_five_focus_json}

DAILY_STATE:
{daily_state_json}

TODAY_LOG_EVIDENCE:
{logs_text_today}

RECENT_LOG_EVIDENCE:
{logs_text_recent}

반드시 JSON 객체 1개만 출력:
{{
  "current_analysis": "string",
  "next_actions": "string",
  "warnings": "string"
}}
"""

    try:
        result = _action_plan_chat_completion_json(prompt)
        result = validate_action_plan_output(result, daily_state)

        now_kst2 = get_current_kst()
        result['generated_at'] = now_kst2.strftime('%H:%M')
        result['generated_hours_left'] = 24 - now_kst2.hour
        return result
    except Exception as e:
        print("action plan error:", e)
        fallback = {
            "current_analysis": "AI 호출 실패로 규칙 기반 플랜으로 전환했습니다.",
            "next_actions": build_rule_based_action_plan(daily_state, daily_five_focus=daily_five_focus),
            "warnings": format_ai_error_message(e),
            "fallback_mode": "ai_error",
        }
        fallback = validate_action_plan_output(fallback, daily_state)
        now_kst2 = get_current_kst()
        return {
            "current_analysis": fallback.get("current_analysis", "AI 호출 실패"),
            "next_actions": fallback.get("next_actions", ""),
            "warnings": fallback.get("warnings", ""),
            "fallback_mode": "ai_error",
            "generated_at": now_kst2.strftime('%H:%M'),
            "generated_hours_left": 24 - now_kst2.hour
        }

def ai_generate_action_plan(hrv, rhr, weight, full_context, today_activities, available_slots, daily_five_sig=""):
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
            available_slots,
            ACTION_PLAN_CACHE_VERSION,
            str(daily_five_sig or ""),
        )
    except Exception:
        # 캐시 우회 1회 실행 (실패 결과 비캐시)
        return ai_generate_action_plan_internal(
            hrv, rhr, weight,
            list(today_activities),
            available_slots
        )


PITWALL_PATCH_FIELD_MAP = {
    "title": "Title",
    "description": "Description",
    "why": "Why",
    "priority": "Priority",
    "category": "Category",
    "urgency_level": "Urgency_Level",
}

PITWALL_PATCH_TRIGGER_KEYWORDS = [
    "patch", "패치", "수정안", "계획 수정", "task_", "json", "daily five 수정",
]


def _extract_df_task_targets(user_message):
    txt_up = str(user_message or "").upper()
    targets = set()
    for m in re.finditer(r"(?<![A-Z0-9])DF\s*([1-5])(?!\d)", txt_up):
        targets.add(f"task_{int(m.group(1))}")
    for m in re.finditer(r"(?<![A-Z0-9])TASK[_-]?([1-5])(?!\d)", txt_up):
        targets.add(f"task_{int(m.group(1))}")
    return sorted(targets)


def _pitwall_wants_patch(user_message):
    txt = str(user_message or "").strip().lower()
    if not txt:
        return False
    if _extract_df_task_targets(txt):
        return True
    change_verbs = ["바꾸", "변경", "수정", "교체", "replace", "change", "update", "revise"]
    if any(v in txt for v in change_verbs):
        if ("df" in txt) or ("task" in txt):
            return True
    return any(k in txt for k in PITWALL_PATCH_TRIGGER_KEYWORDS)


def _pitwall_compact_context(consult_context):
    ctx = dict(consult_context or {})
    try:
        recent_logs = list(ctx.get("recent_logs", []) or [])
        if recent_logs:
            ctx["recent_logs"] = recent_logs[:10]
    except:
        pass
    try:
        daily_state = dict(ctx.get("daily_state", {}) or {})
        today_logs = list(daily_state.get("today_logs", []) or [])
        if today_logs:
            daily_state["today_logs"] = today_logs[:8]
        slots = list(daily_state.get("available_slots", []) or [])
        if slots:
            daily_state["available_slots"] = slots[:4]
        ctx["daily_state"] = daily_state
    except:
        pass
    try:
        tasks = list(ctx.get("daily_five_tasks", []) or [])
        if tasks:
            ctx["daily_five_tasks"] = tasks[:5]
    except:
        pass
    return ctx


def _normalize_pitwall_reply_text(coach_reply, consult_context):
    txt = str(coach_reply or "").strip()
    if not txt:
        return "오늘 상태 기준으로 핵심 1개만 먼저 고르고, 실행 조건(시간·분량)을 붙여 확정해 주세요."

    ctx = dict(consult_context or {})
    daily_state = dict(ctx.get("daily_state", {}) or {})
    sprint_progress = dict(ctx.get("sprint_progress", {}) or {})
    if sprint_progress:
        daily_state["sprint"] = sprint_progress

    txt = _rewrite_vague_korean(_dedupe_consecutive_sentences(txt))
    lines = [ln.strip() for ln in str(txt).splitlines() if str(ln).strip()]
    if not lines:
        lines = [txt]

    dedup = []
    seen = set()
    for ln in lines:
        k = re.sub(r"\s+", " ", str(ln).strip()).lower()
        if not k or k in seen:
            continue
        seen.add(k)
        dedup.append(polish_korean_coaching_text(str(ln).strip()))

    if not any(_is_action_oriented_text(ln) for ln in dedup):
        dedup.append(build_forced_next_action_from_state(daily_state))

    return "\n".join(dedup[:8]).strip()


def invalidate_dailyfive_local_cache(date_key, sprint_id):
    try:
        cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
    except Exception as e:
        print("dailyfive local cache invalidate error:", e)


@st.cache_data(ttl=120)
def build_pitwall_consult_context(date_key, context_nonce="0"):
    out = {
        "date_key": str(date_key),
        "now_kst": get_current_kst().strftime("%Y-%m-%d %H:%M:%S"),
        "sprint": {},
        "sprint_progress": {},
        "daily_state": {},
        "daily_five_focus": {},
        "daily_five_tasks": [],
        "recent_logs": [],
    }
    try:
        df_action = pd.DataFrame(fetch_sheet_data("Action_Log"))
    except Exception:
        df_action = pd.DataFrame()
    try:
        df_health = pd.DataFrame(fetch_sheet_data("Health_Log"))
    except Exception:
        df_health = pd.DataFrame()

    sprint = get_active_sprint()
    if not sprint:
        out["recent_logs"] = list(build_recent_action_evidence(df_action, str(date_key), lookback_days=2).get("recent_logs_newest_first", []))
        return out

    sprint_id = str(sprint.get("sprint_id", "") or "")
    out["sprint"] = {
        "sprint_id": sprint_id,
        "name": str(sprint.get("name", "") or ""),
        "start_date": str(sprint.get("start_date", "") or ""),
        "end_date": str(sprint.get("end_date", "") or ""),
        "duration_days": int(sprint.get("duration_days", 14) or 14),
    }

    weight = 0.0
    hrv = 0.0
    rhr = 0.0
    if not df_health.empty:
        latest = _latest_health_values(df_health)
        weight = latest["Weight"]
        hrv = latest["HRV"]
        rhr = latest["RHR"]

    progress = None
    try:
        if weight > 0:
            progress = calculate_sprint_progress(sprint, weight)
    except Exception:
        progress = None
    if progress:
        out["sprint_progress"] = {
            "day": _safe_int(progress.get("day"), 0),
            "days_remaining": _safe_int(progress.get("days_remaining"), 0),
            "pace_status": str(progress.get("pace_status", "") or ""),
            "weight_delta": _safe_float(progress.get("weight_delta"), None),
            "required_daily_pace": _safe_float(progress.get("required_daily_pace"), None),
        }

    cal_evts = get_today_calendar_events(str(date_key))
    slots = build_available_slots(str(date_key), cal_evts)
    daily_state = build_daily_state(
        date_key=str(date_key),
        now_kst=get_current_kst(),
        df_action=df_action,
        cal_evts=cal_evts,
        available_slots=slots,
        sprint_progress=progress,
        current_hrv=hrv,
        current_rhr=rhr,
    )
    daily_state_brief = {
        "phase": daily_state.get("phase"),
        "late_mode": daily_state.get("late_mode"),
        "calendar_flags": daily_state.get("calendar_flags", {}),
        "meal_done": daily_state.get("meal_done", {}),
        "workout_done": daily_state.get("workout_done", {}),
        "intake_today": daily_state.get("intake_today", {}),
        "xc": daily_state.get("xc", {}),
        "urgency": daily_state.get("urgency", {}),
        "available_slots": daily_state.get("available_slots", []),
        "today_logs": list((daily_state.get("today_logs", []) or [])),
    }
    out["daily_state"] = daily_state_brief

    try:
        out["daily_five_focus"] = build_daily_five_focus_snapshot(str(date_key), sprint_id, df_action)
    except Exception:
        out["daily_five_focus"] = {
            "has_plan": False,
            "completed": 0,
            "total": 0,
            "completion_rate": 0.0,
            "remaining_count": 0,
            "remaining_tasks": [],
            "summary_line": "DF 계획 없음",
            "signature": "no_plan",
        }

    try:
        rows = fetch_sheet_data("Sprint_Daily_Tasks")
        tasks = [
            r for r in (rows or [])
            if str(r.get("Date", "")).strip() == str(date_key)
            and str(r.get("Sprint_ID", "")).strip() == sprint_id
        ]
        tasks = sorted(
            tasks,
            key=lambda x: (
                _task_index_from_task_id(x.get("Task_ID", "")) or 999,
                _safe_int(x.get("Priority", 99), 99),
            ),
        )
        out["daily_five_tasks"] = [
            {
                "task_id": str(t.get("Task_ID", "")).strip(),
                "priority": _safe_int(t.get("Priority", 0), 0),
                "category": str(t.get("Category", "")).strip(),
                "title": str(t.get("Title", "")).strip(),
                "description": str(t.get("Description", "")).strip(),
                "why": str(t.get("Why", "")).strip(),
                "completed": _to_boolish(t.get("Completed", "")),
            }
            for t in tasks
        ]
    except Exception:
        out["daily_five_tasks"] = []

    try:
        recent = build_recent_action_evidence(df_action, str(date_key), lookback_days=2)
        out["recent_logs"] = list(recent.get("recent_logs_newest_first", []))
    except Exception:
        out["recent_logs"] = []

    return out


def ai_generate_pitwall_consultation(user_message, consult_context, chat_history=None):
    txt = str(user_message or "").strip()
    if not txt:
        return {"coach_reply": "", "plan_patch": {"enabled": False, "changes": []}}

    provider = _resolve_provider(COACHING_PROVIDER)
    if not _coaching_has_provider_key(provider):
        provider_name = "Claude" if provider == "anthropic" else "OpenAI"
        return {
            "coach_reply": f"{provider_name} API 키가 없어 상담을 생성하지 못했습니다.",
            "plan_patch": {"enabled": False, "changes": []},
        }

    history_lines = []
    for h in (chat_history or [])[-4:]:
        role = str(h.get("role", "user"))
        tag = "COACH" if role == "assistant" else "USER"
        history_lines.append(f"[{tag}] {str(h.get('text', '')).strip()}")
    history_text = "\n".join(history_lines) if history_lines else "(no history)"

    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()
    korean_style_context = build_korean_style_context()
    compact_context = _pitwall_compact_context(consult_context)
    context_json = json.dumps(compact_context, ensure_ascii=False, indent=2)
    wants_patch = _pitwall_wants_patch(txt)
    patch_targets = _extract_df_task_targets(txt)
    patch_targets_json = json.dumps(patch_targets, ensure_ascii=False)
    chat_model_openai = str(
        st.secrets.get("PITWALL_CHAT_MODEL_OPENAI", st.secrets.get("PITWALL_CHAT_MODEL", "gpt-4o-mini"))
        or "gpt-4o-mini"
    ).strip() or "gpt-4o-mini"
    patch_model_openai = str(
        st.secrets.get("PITWALL_PATCH_MODEL_OPENAI", st.secrets.get("PITWALL_PATCH_MODEL", "gpt-4o"))
        or "gpt-4o"
    ).strip() or "gpt-4o"
    chat_model_anthropic = str(
        st.secrets.get("PITWALL_CHAT_MODEL_ANTHROPIC", st.secrets.get("PITWALL_CHAT_MODEL", COACHING_MODEL_ANTHROPIC))
        or COACHING_MODEL_ANTHROPIC
    ).strip() or COACHING_MODEL_ANTHROPIC
    patch_model_anthropic = str(
        st.secrets.get("PITWALL_PATCH_MODEL_ANTHROPIC", st.secrets.get("PITWALL_PATCH_MODEL", COACHING_MODEL_ANTHROPIC))
        or COACHING_MODEL_ANTHROPIC
    ).strip() or COACHING_MODEL_ANTHROPIC

    try:
        if not wants_patch:
            prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

역할: Pit Wall 상담 코치
언어: 한국어 존댓말

[목표]
- 사용자의 질문에 대해 실질적인 행동 변화를 유도하는 코칭을 제공합니다.
- 과도한 서론 없이 핵심만 짧고 강하게 답합니다.
- 답변은 현재 사용자의 스프린트/컨디션 맥락을 반영해 작성하십시오.
- 지시문만 나열하지 말고, 해석 + 우선순위 + 근거가 자연스럽게 드러나게 작성하십시오.
- 고정 템플릿을 강제하지 않습니다. 다만 문장은 구체적이고 실행 가능해야 합니다.
- 일반론/상투문구를 금지합니다. 반드시 현재 사용자 상태와 연결해 설명하십시오.
- 필요 시 단호한 톤을 사용해도 되지만, 모욕적 표현은 금지합니다.

[대화 이력]
{history_text}

[사용자 최신 질문]
{txt}

[상태 컨텍스트 JSON]
{context_json}
"""
            coach_reply = _coaching_text_completion(
                prompt=prompt,
                provider=provider,
                model_openai=chat_model_openai,
                model_anthropic=chat_model_anthropic,
                max_tokens=420,
                temperature=0.6,
            )
            if not coach_reply:
                coach_reply = "오늘 남은 DF 항목 중 최우선 1개를 먼저 확정하고, 가능한 시간대에 20분 단위로 마무리해 주세요."
            coach_reply = _normalize_pitwall_reply_text(coach_reply, compact_context)
            return {"coach_reply": coach_reply, "plan_patch": {"enabled": False, "changes": []}}

        prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

역할: Pit Wall 상담 코치
언어: 한국어 존댓말

[목표]
- 사용자의 질문에 대해 실질적인 행동 변화를 유도하는 코칭을 제공합니다.
- 필요하면 오늘 Daily Five(task_1~task_5) 수정 제안을 JSON patch 형태로 제공합니다.
- patch는 기존 Task_ID를 업데이트하는 변경만 허용합니다. (신규 생성/삭제 금지)
- 캘린더/슬롯/로그 사실과 모순되지 않게 작성하십시오.
- 사용자가 특정 DF 번호(예: DF3)를 언급하면 해당 task_id(task_3)를 changes에 반드시 포함하십시오.

[대화 이력]
{history_text}

[사용자 최신 질문]
{txt}

[상태 컨텍스트 JSON]
{context_json}

[PATCH_TARGET_HINT]
{patch_targets_json}

[출력 형식 - JSON ONLY]
반드시 json object 1개만 출력하십시오.
{{
  "coach_reply": "사용자에게 보여줄 답변",
  "plan_patch": {{
    "enabled": true/false,
    "date_key": "YYYY-MM-DD",
    "reason": "왜 수정이 필요한지 1-2문장",
    "changes": [
      {{
        "task_id": "task_1",
        "title": "...",
        "description": "...",
        "why": "...",
        "priority": 1,
        "category": "workout/diet/recovery/hydration",
        "urgency_level": "high/medium/low"
      }}
    ]
  }}
}}
"""
        result = _coaching_json_completion(
            prompt=prompt,
            provider=provider,
            model_openai=patch_model_openai,
            model_anthropic=patch_model_anthropic,
            max_tokens=900,
            temperature=0.6,
        )
    except Exception as e:
        return {
            "coach_reply": f"상담 생성 중 오류가 발생했습니다: {e}",
            "plan_patch": {"enabled": False, "changes": []},
        }

    coach_reply = str(result.get("coach_reply", "") or "").strip()
    if not coach_reply:
        coach_reply = "현재 데이터 기준으로 계획 조정이 필요합니다. 아래 수정안을 검토해 주세요."
    coach_reply = _normalize_pitwall_reply_text(coach_reply, compact_context)

    raw_patch = result.get("plan_patch", {}) or {}
    patch_date = str(raw_patch.get("date_key", "") or str((consult_context or {}).get("date_key", get_mission_date_key())))
    raw_changes = raw_patch.get("changes", []) or []
    safe_changes = []
    for c in raw_changes[:8]:
        if not isinstance(c, dict):
            continue
        task_id = str(c.get("task_id", "") or "").strip()
        if not task_id:
            continue
        one = {"task_id": task_id}
        for k in PITWALL_PATCH_FIELD_MAP.keys():
            if k not in c:
                continue
            if k == "priority":
                p = _safe_int(c.get("priority", 0), 0)
                if p > 0:
                    one["priority"] = max(1, min(5, p))
            else:
                v = str(c.get(k, "") or "").strip()
                if v:
                    one[k] = v
        if len(one) > 1:
            safe_changes.append(one)

    patch = {
        "enabled": bool(raw_patch.get("enabled", False)) and bool(safe_changes),
        "date_key": patch_date,
        "reason": str(raw_patch.get("reason", "") or "").strip(),
        "changes": safe_changes,
    }
    return {"coach_reply": coach_reply, "plan_patch": patch}


def apply_pitwall_plan_patch(sprint_id, plan_patch):
    sprint_id_str = str(sprint_id or "").strip()
    if not sprint_id_str:
        return {"ok": False, "updated": 0, "message": "활성 스프린트가 없어 수정안을 반영할 수 없습니다."}

    patch = dict(plan_patch or {})
    changes = list(patch.get("changes", []) or [])
    date_key = str(patch.get("date_key", "") or get_mission_date_key()).strip()
    if not changes:
        return {"ok": False, "updated": 0, "message": "반영할 변경 항목이 없습니다."}

    try:
        sheet = get_db_connection("Sprint_Daily_Tasks")
        headers = _get_or_init_headers(sheet, SPRINT_DAILY_TASKS_DEFAULT_HEADERS)
        rows = sheet.get_all_records()
    except Exception as e:
        return {"ok": False, "updated": 0, "message": f"시트 접근 오류: {e}"}

    updated = 0
    missing = []
    for ch in changes:
        task_id = str(ch.get("task_id", "") or "").strip()
        if not task_id:
            continue
        target_row = None
        for row_num, r in enumerate(rows, start=2):
            if str(r.get("Date", "")).strip() != date_key:
                continue
            if str(r.get("Sprint_ID", "")).strip() != sprint_id_str:
                continue
            if str(r.get("Task_ID", "")).strip().lower() == task_id.lower():
                target_row = row_num
                break

        if not target_row:
            missing.append(task_id)
            continue

        value_map = {}
        for src_key, col_name in PITWALL_PATCH_FIELD_MAP.items():
            if src_key not in ch:
                continue
            raw_val = ch.get(src_key)
            if src_key == "priority":
                v = _safe_int(raw_val, 0)
                if v <= 0:
                    continue
                value_map[col_name] = max(1, min(5, v))
            else:
                v = str(raw_val or "").strip()
                if not v:
                    continue
                value_map[col_name] = v

        if not value_map:
            continue

        try:
            _update_row_fields_by_header(
                sheet=sheet,
                headers=headers,
                row_num=target_row,
                value_map=value_map,
                value_input_option="RAW",
            )
            updated += 1
        except Exception as e:
            print("pitwall patch update error:", e)

    if updated > 0:
        try:
            fetch_sheet_data.clear()
        except Exception:
            pass
        invalidate_dailyfive_local_cache(date_key, sprint_id_str)
        invalidate_realtime_plan_cache(date_key)
        return {
            "ok": True,
            "updated": updated,
            "message": f"{updated}개 task 변경을 반영했습니다."
        }

    miss_txt = ", ".join(missing[:5]) if missing else "적용 가능한 변경 없음"
    return {
        "ok": False,
        "updated": 0,
        "message": f"반영된 변경이 없습니다. (미매칭 task_id: {miss_txt})"
    }


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


def summarize_diet_quality_for_day(df_action, date_key):
    out = {"risk_level": "unknown", "risk_tags": [], "intake_logs_count": 0}
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out

    day = df_action[df_action["Date"] == date_key].copy()
    if day.empty:
        return out
    if "Category" not in day.columns:
        return out

    intake = day[day["Category"].astype(str).str.contains("섭취", na=False)].copy()
    if intake.empty:
        out["risk_level"] = "low"
        return out

    txt = " ".join(intake.get("User_Input", "").astype(str).tolist())
    out["intake_logs_count"] = int(len(intake))

    tags = set()
    for k in BAD_FOOD_KEYS:
        if str(k) in txt:
            tags.add(str(k))
    out["risk_tags"] = sorted(tags)

    risk_score = 0
    if tags:
        risk_score += 1 + min(2, len(tags))
    if any(b in txt for b in BEVERAGE_TOKENS):
        risk_score += 1

    if risk_score >= 3:
        out["risk_level"] = "high"
    elif risk_score >= 1:
        out["risk_level"] = "medium"
    else:
        out["risk_level"] = "low"
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
    vals = _latest_health_values(day, defaults={"Weight": out["weight"], "HRV": out["hrv"], "RHR": out["rhr"]})
    out["weight"] = vals["Weight"]
    out["hrv"] = vals["HRV"]
    out["rhr"] = vals["RHR"]
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
        termin_brief = []
        for e in (t_ev.get("Termin", []) or []):
            title = str(e.get("title", "") or "").strip()
            if not title or _is_canceled_event_title(title):
                continue
            if bool(e.get("is_all_day")):
                termin_brief.append(f"[종일] {title}")
                continue
            s_dt = e.get("start_dt")
            e_dt = e.get("end_dt")
            try:
                tm_txt = f"{s_dt.strftime('%H:%M')}-{e_dt.strftime('%H:%M')}"
            except Exception:
                tm_txt = "--:--"
            termin_brief.append(f"[{tm_txt}] {title}")
        return t_key, t_slots, t_enabled, termin_brief[:6]
    except:
        return "", [], [], []


def _build_tomorrow_schedule_hint(tomorrow_key, tomorrow_slots, tomorrow_enabled, termin_brief):
    date_txt = str(tomorrow_key or "").strip()
    if not date_txt:
        date_txt = "내일"
    enabled_labels = [str(s.get("label") or s.get("slot_id") or "").strip() for s in (tomorrow_enabled or [])]
    enabled_labels = [x for x in enabled_labels if x]
    if enabled_labels:
        slot_txt = ", ".join(enabled_labels[:3])
    else:
        slot_txt = "활성 운동 슬롯 없음"

    if termin_brief:
        return (
            f"내일 일정 예측({date_txt}): {', '.join(termin_brief[:2])}. "
            f"운영 원칙은 {slot_txt} 중심으로 잡으십시오."
        )
    return (
        f"내일 일정 예측({date_txt}): 큰 고정 약속은 현재 확인되지 않습니다. "
        f"운영 원칙은 {slot_txt} 중심으로 잡으십시오."
    )


def _pick_next_action_from_slots(enabled_slots):
    if not enabled_slots:
        return "내일 07:30에 체중을 측정하고, 오전 중 10분 걷기 1회를 먼저 실행하십시오."
    s = enabled_slots[0]
    label = str(s.get("label") or s.get("slot_id") or "다음 가용 슬롯")
    start = str(s.get("start") or "")
    return f"내일 {label}({start})에 실행할 운동 1개를 확정하고 먼저 수행하십시오."


def summarize_today_meal_timeline(df_action, date_key):
    out = {
        "meal_count": 0,
        "entries": [],
        "lunch_line": "기록 없음",
        "dinner_line": "기록 없음",
    }
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return out
    day = df_action[df_action["Date"] == date_key].copy()
    if day.empty or "Category" not in day.columns:
        return out
    meals = day[day["Category"].astype(str).str.contains("섭취", na=False)].copy()
    if meals.empty:
        return out
    if "Action_Time" not in meals.columns:
        meals["Action_Time"] = ""
    meals = meals.sort_values("Action_Time", na_position="last")

    parsed = []
    for _, r in meals.iterrows():
        t = str(r.get("Action_Time", "") or "").strip() or "--:--"
        txt = str(r.get("User_Input", "") or "").strip()
        js = _safe_json_obj(r.get("AI_Analysis_JSON", "{}"))
        kcal = _safe_int(js.get("calories", 0), 0)
        bucket = _meal_bucket_by_time(t)
        item = {
            "time": t,
            "text": txt,
            "kcal": int(kcal),
            "bucket": bucket or "",
        }
        parsed.append(item)

    out["meal_count"] = len(parsed)
    out["entries"] = parsed[:8]

    lunch_cand = [x for x in parsed if x.get("bucket") == "lunch"]
    dinner_cand = [x for x in parsed if x.get("bucket") == "dinner"]
    lunch = lunch_cand[0] if lunch_cand else (parsed[0] if parsed else None)
    dinner = dinner_cand[-1] if dinner_cand else (parsed[-1] if parsed else None)

    def _to_line(entry):
        if not entry:
            return "기록 없음"
        kcal_txt = f" ({entry.get('kcal', 0)}kcal)" if int(entry.get("kcal", 0) or 0) > 0 else ""
        return f"[{entry.get('time', '--:--')}] {entry.get('text', '').strip()}{kcal_txt}"

    out["lunch_line"] = _to_line(lunch)
    out["dinner_line"] = _to_line(dinner)
    return out


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
    xc=None,
):
    action_summary = summarize_action_range(df_action, date_key, date_key)
    health_summary = summarize_health_for_day(df_health, date_key, current_weight, current_hrv, current_rhr)
    day_score_detail = compute_day_score_detail(date_key, df_action)
    diet_quality = summarize_diet_quality_for_day(df_action, date_key)
    meal_timeline = summarize_today_meal_timeline(df_action, date_key)
    recent_evidence = build_recent_action_evidence(df_action, date_key, lookback_days=2)
    kcal_target = int(get_daily_kcal_target())
    kcal_delta = int(int(action_summary.get("intake_kcal", 0) or 0) - kcal_target)
    tomorrow_key, tomorrow_slots, tomorrow_enabled, tomorrow_termin_brief = _get_tomorrow_slots(date_key)
    tomorrow_schedule_hint = _build_tomorrow_schedule_hint(
        tomorrow_key=tomorrow_key,
        tomorrow_slots=tomorrow_slots,
        tomorrow_enabled=tomorrow_enabled,
        termin_brief=tomorrow_termin_brief,
    )

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
    sprint_snapshot = {
        "day": _safe_int((sprint_progress or {}).get("day", 0), 0) if sprint_progress else None,
        "duration_days": _safe_int((sprint or {}).get("duration_days", 0), 0) if sprint else None,
        "days_remaining": _safe_int((sprint_progress or {}).get("days_remaining", 0), 0) if sprint_progress else None,
        "weight_start": (_safe_float((sprint_progress or {}).get("weight_start"), 0.0) if sprint_progress else None),
        "weight_current": (_safe_float((sprint_progress or {}).get("weight_current"), 0.0) if sprint_progress else None),
        "weight_target": (_safe_float((sprint_progress or {}).get("weight_target"), 0.0) if sprint_progress else None),
        "weight_expected": (_safe_float((sprint_progress or {}).get("weight_expected"), 0.0) if sprint_progress else None),
        "pace_status": (sprint_progress.get("pace_status") if sprint_progress else None),
    }
    payload = {
        "kind": "daily",
        "date_key": date_key,
        "generated_at_kst": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
        "health": health_summary,
        "action_summary": action_summary,
        "meal_timeline": meal_timeline,
        "diet_quality": {
            "risk_level": str(diet_quality.get("risk_level", "unknown")),
            "risk_tags": list(diet_quality.get("risk_tags", []) or []),
            "repeat_bad_food_days_d2_to_d0": int(recent_evidence.get("repeat_bad_food_days", 0) or 0),
            "repeat_bad_food_tags_d2_to_d0": list(recent_evidence.get("repeat_bad_food_tags", []) or []),
        },
        "kcal_target": {
            "target_today": int(kcal_target),
            "delta_today": int(kcal_delta),
        },
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
            "snapshot": sprint_snapshot,
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
            "tomorrow_termin_brief": tomorrow_termin_brief,
            "tomorrow_schedule_hint": tomorrow_schedule_hint,
        },
        "prev_xc_feedback": prev_xc_feedback,
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
        xc_reason = list((((payload or {}).get("xc", {}) or {}).get("reason", []) or []))
        prev_gap = (((payload or {}).get("prev_xc_feedback", {}) or {}).get("gap_kg"))
        meal_timeline = ((payload or {}).get("meal_timeline", {}) or {})
        lunch_line = str(meal_timeline.get("lunch_line", "기록 없음") or "기록 없음")
        dinner_line = str(meal_timeline.get("dinner_line", "기록 없음") or "기록 없음")
        sprint_snapshot = (((payload or {}).get("sprint", {}) or {}).get("snapshot", {}) or {})
        sprint_day = _safe_int(sprint_snapshot.get("day", 0), 0)
        sprint_total = _safe_int(sprint_snapshot.get("duration_days", 0), 0)
        pace_status = str(sprint_snapshot.get("pace_status", "") or "")
        pace_txt = {"ahead": "페이스 앞섬", "on-track": "페이스 유지", "behind": "페이스 뒤처짐"}.get(pace_status, "페이스 정보 없음")

        if workouts > 0 or df_done >= 2 or (intake >= 1000 and intake <= 2200):
            praise = f"오늘은 기록 기반 실행이 남아 있습니다. 운동 {workouts}회({minutes}분), DF {df_done}/{df_total}는 유지 자산입니다."
        if alcohol_n > 0:
            warning = f"음주 기록 {alcohol_n}건이 확인됩니다. 내일 컨디션 하락을 전제로 보수 운영이 필요합니다."
        elif workouts <= 0 and intake >= 1800:
            warning = "섭취 대비 활동량이 부족합니다. 이 패턴이 2일 연속이면 스프린트 미달 위험이 급증합니다."
        if meals <= 1:
            critique = "식사 기록이 너무 적어 실제 섭취가 과소평가될 가능성이 큽니다. 기록 정확도를 먼저 복구하십시오."
        elif workouts <= 0:
            critique = "오늘은 실행 여건이 부족해 행동량이 낮게 반영됐습니다. 내일은 일정 안에서 우선순위 1개만 먼저 고정하는 방식이 유리합니다."
        else:
            critique = "실행은 있었지만 강도 또는 일관성이 목표 대비 부족할 수 있습니다."

        if (prev_gap is not None) and (_safe_float(prev_gap, 0.0) > 0):
            warning = (warning + " " if warning else "") + f"전일 xC 미달분 {_safe_float(prev_gap, 0.0):.2f}kg가 남아 있습니다."
        if xc_val is not None:
            critique = f"{critique} 오늘 xC 기준은 {float(xc_val):.2f}kg였습니다."
        if xc_reason:
            critique = f"{critique} xC 근거: {str(xc_reason[0])}."

        tomorrow_enabled = (((payload or {}).get("calendar", {}) or {}).get("tomorrow_enabled_slots", []) or [])
        tomorrow_hint = str((((payload or {}).get("calendar", {}) or {}).get("tomorrow_schedule_hint", "") or "").strip())
        next_action = _pick_next_action_from_slots(tomorrow_enabled)
        if tomorrow_hint:
            next_action = f"{next_action}\n{tomorrow_hint}".strip()

        overview = (
            f"스프린트 {sprint_day}/{sprint_total}일차({pace_txt}). "
            f"오늘 기록 기준 섭취 {intake}kcal, 식사 {meals}회, 운동 {workouts}회({minutes}분), "
            f"영양제 {supp_n}개, 음주 {alcohol_n}건. "
            f"점심: {lunch_line}. 저녁: {dinner_line}."
        )
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
            f"주간 기록 요약: 섭취 {intake}kcal, 식사 {meals}회, 운동 {workouts}회({minutes}분), "
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


def apply_wrapup_consistency_guard(result, kind, payload):
    if not isinstance(result, dict):
        return result
    if str(kind or "") != "daily":
        return result

    action = (payload or {}).get("action_summary", {}) or {}
    kcal_obj = (payload or {}).get("kcal_target", {}) or {}
    diet_q = (payload or {}).get("diet_quality", {}) or {}
    intake = _safe_int(action.get("intake_kcal", 0), 0)
    target = _safe_int(kcal_obj.get("target_today", get_daily_kcal_target()), get_daily_kcal_target())
    delta = _safe_int(kcal_obj.get("delta_today", intake - target), intake - target)
    risk_level = str(diet_q.get("risk_level", "unknown") or "unknown")
    repeat_days = _safe_int(diet_q.get("repeat_bad_food_days_d2_to_d0", 0), 0)
    risk_tags = list(diet_q.get("risk_tags", []) or [])

    conflict = (delta >= 120) or (risk_level == "high") or (repeat_days >= 2)
    if not conflict:
        return result

    pos_tokens = ["균형", "안정", "컨트롤", "양호", "잘 잡", "문제없", "좋았"]
    def has_pos(text):
        low = str(text or "").lower()
        return any(t in low for t in pos_tokens)

    overview = str(result.get("overview", "") or "").strip()
    praise = str(result.get("praise", "") or "").strip()
    warning = str(result.get("warning", "") or "").strip()
    critique = str(result.get("critique", "") or "").strip()

    if has_pos(overview):
        overview = (
            f"오늘 섭취는 {intake}kcal로 기준 {target}kcal 대비 {delta:+d}kcal이며, "
            "식사 품질 리스크를 감안하면 안정적 패턴으로 보기 어렵습니다."
        )
    if has_pos(praise):
        praise = ""

    tags_txt = ", ".join(risk_tags[:4]) if risk_tags else "고위험 메뉴"
    warn_line = (
        f"식사 품질 리스크({risk_level})가 감지되었습니다({tags_txt}). "
        "내일은 동일 패턴 반복을 차단해야 합니다."
    )
    if warn_line not in warning:
        warning = f"{warning}\n{warn_line}".strip() if warning else warn_line
    if not critique:
        critique = "오늘은 칼로리 합계보다도 식사 구성 품질이 더 큰 리스크였습니다."

    result["overview"] = overview
    result["praise"] = praise
    result["warning"] = warning
    result["critique"] = critique
    return result


def apply_wrapup_forecast_guard(result, kind, payload):
    if not isinstance(result, dict):
        return result
    if str(kind or "") != "daily":
        return result
    cal_obj = (payload or {}).get("calendar", {}) or {}
    hint = str(cal_obj.get("tomorrow_schedule_hint", "") or "").strip()
    if not hint:
        return result
    next_action = str(result.get("next_action", "") or "").strip()
    if hint not in next_action:
        next_action = f"{next_action}\n{hint}".strip() if next_action else hint
        result["next_action"] = next_action
    return result


def ai_generate_wrapup(kind, payload):
    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()
    korean_style_context = build_korean_style_context()
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)

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
            "- overview에는 스프린트 진행(몇 일차/총 일수/페이스), 점심/저녁 기록, 핵심 수치(섭취 kcal 또는 운동분 또는 xC)를 반드시 포함하십시오.\n"
            "- 칭찬할 근거가 없으면 praise는 빈 문자열로 두십시오.\n"
            "- 경고/비판은 회피하지 말고 행동 변화 관점에서 분명히 작성하십시오.\n"
            "- critique에는 오늘 xC 수치와 xC reason 중 최소 1개를 반영하십시오.\n"
            "- next_action 마지막 문장에는 calendar.tomorrow_schedule_hint를 반영해, 내일 일정 기반 운영 예측을 반드시 넣으십시오.\n"
            "- 내일 달성 가능성(높음/중간/낮음)을 warning 또는 critique에 명시하십시오.\n"
            "- kcal_target.delta_today가 양수이거나 diet_quality.risk_level이 high면 '균형/안정/컨트롤 양호' 표현을 쓰지 마십시오."
        )

    prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

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
        result = _coaching_json_completion(
            prompt=prompt,
            provider=COACHING_PROVIDER,
            model_openai=COACHING_MODEL_OPENAI,
            model_anthropic=COACHING_MODEL_ANTHROPIC,
            max_tokens=1200,
            temperature=0.6,
        )
        result["generated_at"] = get_current_kst().strftime("%H:%M")
        result = _normalize_wrapup_result(result, kind)
        result = apply_wrapup_consistency_guard(result, kind, payload)
        result = apply_wrapup_forecast_guard(result, kind, payload)
        return result
    except Exception as e:
        fb = build_rule_based_wrapup(kind, payload)
        fb["warning"] = (str(fb.get("warning", "") or "").strip() + "\n" + format_ai_error_message(e)).strip()
        fb["fallback_mode"] = "ai_error"
        fb = _normalize_wrapup_result(fb, kind)
        fb = apply_wrapup_consistency_guard(fb, kind, payload)
        fb = apply_wrapup_forecast_guard(fb, kind, payload)
        return fb


def get_or_create_wrapup(kind, cache_key, payload):
    cached = load_wrapup_cache(kind, cache_key)
    if cached:
        patched = apply_wrapup_consistency_guard(_normalize_wrapup_result(cached, kind), kind, payload)
        patched = apply_wrapup_forecast_guard(patched, kind, payload)
        if patched != cached:
            save_wrapup_cache(kind, cache_key, patched)
        return patched
    result = ai_generate_wrapup(kind, payload)
    if (result or {}).get("fallback_mode") != "ai_error":
        save_wrapup_cache(kind, cache_key, result)
        clear_old_caches()
    return result


def _iter_date_keys(start_key, end_key):
    try:
        s = datetime.strptime(str(start_key), "%Y-%m-%d").date()
        e = datetime.strptime(str(end_key), "%Y-%m-%d").date()
    except Exception:
        return []
    if e < s:
        return []
    out = []
    cur = s
    while cur <= e:
        out.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return out


def build_sprint_retro_payload(sprint, df_health, df_action):
    if not sprint:
        return {}
    start_date = sprint.get("start_date")
    end_date = sprint.get("end_date")
    if not start_date or not end_date:
        return {}
    start_key = start_date.strftime("%Y-%m-%d")
    end_key = end_date.strftime("%Y-%m-%d")
    date_keys = _iter_date_keys(start_key, end_key)
    if not date_keys:
        return {}

    action_summary = summarize_action_range(df_action, start_key, end_key)
    health_summary = summarize_health_range(
        df_health,
        start_key,
        end_key,
        _safe_float(sprint.get("final_wt"), 0.0),
        0.0,
        0.0,
    )

    weight_by_date = {k: None for k in date_keys}
    hrv_by_date = {k: None for k in date_keys}
    rhr_by_date = {k: None for k in date_keys}
    if df_health is not None and (not df_health.empty) and ("Date" in df_health.columns):
        h = df_health.copy()
        h["Date_Key"] = pd.to_datetime(h["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        h = h[(h["Date_Key"] >= start_key) & (h["Date_Key"] <= end_key)]
        if not h.empty:
            if "Weight" in h.columns:
                h["Weight_num"] = pd.to_numeric(h["Weight"], errors="coerce")
            else:
                h["Weight_num"] = np.nan
            if "HRV" in h.columns:
                h["HRV_num"] = pd.to_numeric(h["HRV"], errors="coerce")
            else:
                h["HRV_num"] = np.nan
            if "RHR" in h.columns:
                h["RHR_num"] = pd.to_numeric(h["RHR"], errors="coerce")
            else:
                h["RHR_num"] = np.nan
            h = h.sort_values(["Date_Key"])
            for dk, grp in h.groupby("Date_Key"):
                if dk in weight_by_date:
                    wv = grp["Weight_num"].dropna()
                    hv = grp["HRV_num"].dropna()
                    rv = grp["RHR_num"].dropna()
                    weight_by_date[dk] = float(wv.iloc[-1]) if not wv.empty else None
                    hrv_by_date[dk] = float(hv.iloc[-1]) if not hv.empty else None
                    rhr_by_date[dk] = float(rv.iloc[-1]) if not rv.empty else None

    intake_by_date = {k: 0 for k in date_keys}
    workout_min_by_date = {k: 0 for k in date_keys}
    alcohol_by_date = {k: 0 for k in date_keys}
    if df_action is not None and (not df_action.empty) and ("Date" in df_action.columns):
        a = df_action.copy()
        a["Date_Key"] = pd.to_datetime(a["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        a = a[(a["Date_Key"] >= start_key) & (a["Date_Key"] <= end_key)]
        if not a.empty:
            for _, row in a.iterrows():
                dk = str(row.get("Date_Key", "") or "")
                if dk not in intake_by_date:
                    continue
                cat = str(row.get("Category", "") or "")
                text = str(row.get("User_Input", "") or "")
                js = _safe_json_obj(row.get("AI_Analysis_JSON", "{}"))
                if "섭취" in cat:
                    intake_by_date[dk] += _safe_int(js.get("calories", 0), 0)
                if "운동" in cat:
                    dur = _safe_int(js.get("duration", js.get("time", 0)), 0)
                    if dur <= 0:
                        dur = _extract_minutes_from_text(text)
                    workout_min_by_date[dk] += int(max(0, dur))
                if "음주" in cat:
                    alcohol_by_date[dk] += 1

    df_comp_rate_by_date = {k: None for k in date_keys}
    pace_by_date = {k: "" for k in date_keys}
    try:
        df_prog = pd.DataFrame(fetch_sheet_data("Daily_Sprint_Progress"))
        if not df_prog.empty:
            df_prog["Date_Key"] = pd.to_datetime(df_prog.get("Date", ""), errors="coerce").dt.strftime("%Y-%m-%d")
            df_prog = df_prog[
                (df_prog["Date_Key"] >= start_key) &
                (df_prog["Date_Key"] <= end_key) &
                (df_prog.get("Sprint_ID", "").astype(str).str.strip() == str(sprint.get("sprint_id", "")).strip())
            ].copy()
            if not df_prog.empty:
                comp = pd.to_numeric(df_prog.get("Completed", 0), errors="coerce").fillna(0)
                total = pd.to_numeric(df_prog.get("Total", 0), errors="coerce").replace(0, np.nan)
                rate = (comp / total).replace([np.inf, -np.inf], np.nan)
                df_prog["Comp_Rate"] = rate
                for _, row in df_prog.iterrows():
                    dk = str(row.get("Date_Key", "") or "")
                    if dk in df_comp_rate_by_date:
                        rv = _safe_float(row.get("Comp_Rate"), None)
                        df_comp_rate_by_date[dk] = rv
                        pace_by_date[dk] = str(row.get("Pace_Status", "") or "").strip().lower()
    except Exception as e:
        print("build_sprint_retro_payload progress read error:", e)

    pace_counts = {"ahead": 0, "on-track": 0, "behind": 0}
    for p in pace_by_date.values():
        if p in pace_counts:
            pace_counts[p] += 1

    goal_obj = get_sprint_goals(str(sprint.get("sprint_id", ""))).get("weight", {}) or {}
    target_weight = _safe_float(goal_obj.get("target_value"), None)
    start_weight = health_summary.get("start_weight")
    if start_weight is None:
        valid_w = [w for w in weight_by_date.values() if w is not None]
        start_weight = float(valid_w[0]) if valid_w else None
    if target_weight is None:
        target_weight = _safe_float(sprint.get("final_wt"), None)

    payload = {
        "kind": "sprint_retro",
        "generated_at_kst": get_current_kst().strftime("%Y-%m-%d %H:%M:%S"),
        "sprint": {
            "sprint_id": str(sprint.get("sprint_id", "") or ""),
            "name": str(sprint.get("name", "") or ""),
            "status": str(sprint.get("status", "") or ""),
            "start_date": start_key,
            "end_date": end_key,
            "duration_days": int(_safe_int(sprint.get("duration_days"), len(date_keys))),
            "result": str(sprint.get("result", "") or ""),
            "final_wt": _safe_float(sprint.get("final_wt"), None),
            "description": str(sprint.get("description", "") or ""),
            "target_weight": target_weight,
            "start_weight": start_weight,
            "closed_at": str(sprint.get("closed_at", "") or ""),
        },
        "action_summary": action_summary,
        "health_summary": health_summary,
        "series": {
            "date_keys": date_keys,
            "weight": [weight_by_date.get(k) for k in date_keys],
            "hrv": [hrv_by_date.get(k) for k in date_keys],
            "rhr": [rhr_by_date.get(k) for k in date_keys],
            "intake_kcal": [int(intake_by_date.get(k, 0) or 0) for k in date_keys],
            "workout_minutes": [int(workout_min_by_date.get(k, 0) or 0) for k in date_keys],
            "alcohol_logs": [int(alcohol_by_date.get(k, 0) or 0) for k in date_keys],
            "df_completion_rate": [df_comp_rate_by_date.get(k) for k in date_keys],
            "pace_status": [pace_by_date.get(k, "") for k in date_keys],
        },
        "pace_counts": pace_counts,
    }
    return payload


def _normalize_sprint_retro_result(result):
    out = dict(result or {})
    out["headline"] = str(out.get("headline", "") or "").strip()
    out["overview"] = str(out.get("overview", "") or "").strip()
    insights = out.get("insights", []) or []
    if not isinstance(insights, list):
        insights = []
    out["insights"] = [str(x).strip() for x in insights if str(x).strip()][:5]

    kpt = out.get("keep_problem_try", {}) or {}
    if not isinstance(kpt, dict):
        kpt = {}
    keep = [str(x).strip() for x in (kpt.get("keep", []) or []) if str(x).strip()][:3]
    problem = [str(x).strip() for x in (kpt.get("problem", []) or []) if str(x).strip()][:3]
    trys = [str(x).strip() for x in (kpt.get("try", []) or []) if str(x).strip()][:3]
    out["keep_problem_try"] = {"keep": keep, "problem": problem, "try": trys}
    out["generated_at"] = str(out.get("generated_at", "") or "").strip() or get_current_kst().strftime("%H:%M")
    return out


def build_rule_based_sprint_retro(payload):
    sprint = (payload or {}).get("sprint", {}) or {}
    action = (payload or {}).get("action_summary", {}) or {}
    health = (payload or {}).get("health_summary", {}) or {}
    pace_counts = (payload or {}).get("pace_counts", {}) or {}

    start_w = _safe_float(sprint.get("start_weight"), None)
    target_w = _safe_float(sprint.get("target_weight"), None)
    end_w = _safe_float(health.get("end_weight"), _safe_float(sprint.get("final_wt"), None))
    wchg = _safe_float(health.get("weight_change_kg"), None)
    if (wchg is None) and (start_w is not None) and (end_w is not None):
        wchg = float(start_w - end_w)

    intake = _safe_int(action.get("intake_kcal", 0), 0)
    workouts = _safe_int(action.get("workout_sessions", 0), 0)
    workout_minutes = _safe_int(action.get("workout_minutes", 0), 0)
    alcohol_logs = _safe_int(action.get("alcohol_logs", 0), 0)
    df_rates = (payload or {}).get("series", {}).get("df_completion_rate", []) or []
    valid_df = [float(x) for x in df_rates if x is not None]
    avg_df = float(np.mean(valid_df)) if valid_df else 0.0

    headline = f"{str(sprint.get('name', '') or 'Sprint')} 회고"
    overview = (
        f"{str(sprint.get('start_date', ''))}~{str(sprint.get('end_date', ''))} 동안 "
        f"체중 변화는 {wchg:+.2f}kg"
        if wchg is not None else
        f"{str(sprint.get('start_date', ''))}~{str(sprint.get('end_date', ''))} 회고 데이터입니다."
    )
    if (target_w is not None) and (end_w is not None):
        overview += f", 종료 체중 {end_w:.1f}kg / 목표 {target_w:.1f}kg."
    else:
        overview += "."
    insights = [
        f"운동 {workouts}회, 총 {workout_minutes}분으로 행동량은 누적되었습니다.",
        f"음주 로그 {alcohol_logs}건이 체중 반등 리스크를 키웠습니다.",
        f"DF 평균 완료율은 {avg_df * 100:.0f}%이며, behind 일수는 {int(pace_counts.get('behind', 0))}일입니다.",
    ]

    keep = []
    if workouts >= 5:
        keep.append(f"운동 루틴 유지: 스프린트 기간 {workouts}회({workout_minutes}분).")
    if avg_df >= 0.6:
        keep.append(f"일일 실행 유지: DF 평균 완료율 {avg_df * 100:.0f}%.")
    if alcohol_logs <= 1:
        keep.append("음주 노출이 낮아 회복 리듬을 크게 해치지 않았습니다.")

    problem = []
    if alcohol_logs >= 2:
        problem.append(f"음주 {alcohol_logs}건으로 다음날 붓기/체중 반등이 반복되었습니다.")
    if int(pace_counts.get("behind", 0)) >= int(max(3, (sprint.get("duration_days", 0) or 0) // 3)):
        problem.append(f"페이스 뒤처짐이 {int(pace_counts.get('behind', 0))}일 누적되었습니다.")
    if (wchg is not None) and (wchg <= 0):
        problem.append(f"체중 변화가 {wchg:+.2f}kg로 목표 감량 흐름을 만들지 못했습니다.")

    trys = []
    trys.append("다음 스프린트 규칙: 음주 주 1회 이하, 1회 최대 2잔.")
    trys.append("다음 스프린트 규칙: 점심은 밥/면 대신 단백질+채소 조합을 주 5일 적용.")
    trys.append("다음 스프린트 규칙: 13일 중 운동 8회 이상, 1회 30분 이상 고정.")

    return _normalize_sprint_retro_result({
        "headline": headline,
        "overview": overview,
        "insights": insights,
        "keep_problem_try": {
            "keep": keep[:3],
            "problem": problem[:3],
            "try": trys[:3],
        },
        "generated_at": get_current_kst().strftime("%H:%M"),
        "fallback_mode": "rule_based",
    })


def ai_generate_sprint_retro(payload):
    persona_context = build_common_persona_context()
    north_star_context = build_north_star_context()
    korean_style_context = build_korean_style_context()
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    prompt = f"""
{persona_context}
{north_star_context}
{korean_style_context}

역할: Sprint 회고 코치
언어: 한국어 존댓말

[목표]
- 직전 sprint를 행동 변화 관점으로 회고합니다.
- 평균값 나열이 아니라, 실제 로그 흐름과 페이스 변화를 해석합니다.
- keep/problem/try는 각 최대 3개까지만 작성합니다.
- try는 다음 sprint에 바로 적용할 수 있게 수치/규칙을 포함합니다.
- 장황한 중복 설명을 피하고, 자연스러운 사람 말투로 작성하십시오.

[입력 사실(JSON)]
{payload_json}

[출력 형식 - JSON ONLY]
{{
  "headline": "짧은 제목",
  "overview": "종합 총평 3~5문장",
  "insights": ["핵심 인사이트 1", "핵심 인사이트 2"],
  "keep_problem_try": {{
    "keep": ["최대 3개"],
    "problem": ["최대 3개"],
    "try": ["최대 3개, 다음 sprint 실행 규칙/수치 포함"]
  }}
}}
"""
    try:
        result = _coaching_json_completion(
            prompt=prompt,
            provider=COACHING_PROVIDER,
            model_openai=COACHING_MODEL_OPENAI,
            model_anthropic=COACHING_MODEL_ANTHROPIC,
            max_tokens=1400,
            temperature=0.7,
        )
        result = _normalize_sprint_retro_result(result)
        result["generated_at"] = get_current_kst().strftime("%H:%M")
        return result
    except Exception as e:
        fb = build_rule_based_sprint_retro(payload)
        fb["fallback_mode"] = "ai_error"
        fb["overview"] = f"{fb.get('overview', '')}\n{format_ai_error_message(e)}".strip()
        return fb


def get_or_create_sprint_retro(cache_key, payload):
    kind = "sprint_retro"
    cached = load_wrapup_cache(kind, cache_key)
    if cached:
        return _normalize_sprint_retro_result(cached)
    result = ai_generate_sprint_retro(payload)
    if (result or {}).get("fallback_mode") != "ai_error":
        save_wrapup_cache(kind, cache_key, result)
        clear_old_caches()
    return result


def render_sprint_retro_block(retro, payload):
    retro = _normalize_sprint_retro_result(retro)
    sprint = (payload or {}).get("sprint", {}) or {}
    series = (payload or {}).get("series", {}) or {}
    date_keys = list(series.get("date_keys", []) or [])
    st.markdown(
        f"""<h3 style="margin-bottom: 10px;">Sprint Retrospective <span class="time-badge">{retro.get('generated_at', get_current_kst().strftime('%H:%M'))} 생성</span></h3>""",
        unsafe_allow_html=True,
    )
    st.caption(f"{str(sprint.get('sprint_id', '')).strip()} · {str(sprint.get('start_date', ''))} ~ {str(sprint.get('end_date', ''))}")
    with st.container(border=True):
        headline = str(retro.get("headline", "") or "").strip()
        if headline:
            st.markdown(f"**{headline}**")
        st.markdown(str(retro.get("overview", "") or "-"))
        insights = retro.get("insights", []) or []
        if insights:
            st.markdown("**핵심 인사이트**")
            for item in insights:
                st.markdown(f"- {item}")

    if date_keys:
        weight_vals = series.get("weight", []) or []
        start_w = _safe_float(sprint.get("start_weight"), None)
        target_w = _safe_float(sprint.get("target_weight"), None)
        weight_df = pd.DataFrame({"Date": date_keys, "실측체중": weight_vals})
        if (start_w is not None) and (target_w is not None) and len(weight_df) > 1:
            weight_df["목표선"] = np.linspace(start_w, target_w, len(weight_df))
        weight_df["Date"] = pd.to_datetime(weight_df["Date"], errors="coerce")
        weight_df = weight_df.set_index("Date")
        st.markdown("**체중 추이(실측 vs 목표선)**")
        st.line_chart(weight_df, use_container_width=True)

        behavior_df = pd.DataFrame({
            "Date": date_keys,
            "섭취kcal": series.get("intake_kcal", []) or [],
            "운동분": series.get("workout_minutes", []) or [],
        })
        behavior_df["Date"] = pd.to_datetime(behavior_df["Date"], errors="coerce")
        behavior_df = behavior_df.set_index("Date")
        st.markdown("**행동 추이(섭취/운동)**")
        st.bar_chart(behavior_df, use_container_width=True)

        recovery_df = pd.DataFrame({
            "Date": date_keys,
            "HRV": series.get("hrv", []) or [],
            "RHR": series.get("rhr", []) or [],
        })
        recovery_df["Date"] = pd.to_datetime(recovery_df["Date"], errors="coerce")
        recovery_df = recovery_df.set_index("Date")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**HRV 추이**")
            st.line_chart(recovery_df[["HRV"]], use_container_width=True)
        with c2:
            st.markdown("**RHR 추이**")
            st.line_chart(recovery_df[["RHR"]], use_container_width=True)

    kpt = (retro.get("keep_problem_try", {}) or {})
    k_keep = list(kpt.get("keep", []) or [])[:3]
    k_prob = list(kpt.get("problem", []) or [])[:3]
    k_try = list(kpt.get("try", []) or [])[:3]
    st.markdown("**Keep / Problem / Try**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Keep**")
        if k_keep:
            for x in k_keep:
                st.markdown(f"- {x}")
        else:
            st.markdown("- (없음)")
    with c2:
        st.markdown("**Problem**")
        if k_prob:
            for x in k_prob:
                st.markdown(f"- {x}")
        else:
            st.markdown("- (없음)")
    with c3:
        st.markdown("**Try**")
        if k_try:
            for x in k_try:
                st.markdown(f"- {x}")
        else:
            st.markdown("- (없음)")


def render_wrapup_block(kind, wrapup, xc=None):
    title = "Daily Wrap-up" if kind == "daily" else "Weekly Wrap-up"
    label = "내일 첫 행동" if kind == "daily" else "다음 주 첫 행동"
    st.markdown(
        f"""<h3 style="margin-bottom: 10px;">{title} <span class="time-badge">{wrapup.get('generated_at', get_current_kst().strftime('%H:%M'))} 기준</span></h3>""",
        unsafe_allow_html=True,
    )
    if xc and (xc.get("xc_value_kg") is not None):
        st.caption(format_xc_caption_text(xc.get("xc_value_kg")))

    with st.container(border=True):
        st.markdown(f"**종합 평가:** {wrapup.get('overview', '-')}")
        praise = str(wrapup.get("praise", "") or "").strip()
        if praise:
            st.success(f"✅ 칭찬: {praise}")
        warning = str(wrapup.get("warning", "") or "").strip()
        if warning:
            st.markdown(
                f"""
<div style="background:#FEF3C7; border:1px solid #F59E0B; border-radius:10px; padding:10px 12px; color:#1F2937; font-weight:600;">
⚠️ 경고: {warning}
</div>
""",
                unsafe_allow_html=True,
            )
        critique = str(wrapup.get("critique", "") or "").strip()
        if critique:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            st.markdown(f"**비판/진단:** {critique}")
        next_action = str(wrapup.get("next_action", "") or "").strip()
        if next_action:
            st.markdown(f"**{label}:** {next_action}")

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


def _safe_num_from_str(v, default=0.0):
    try:
        return float(v)
    except Exception:
        m = re.search(r"-?\d+(?:\.\d+)?", str(v or ""))
        if not m:
            return float(default)
        try:
            return float(m.group(0))
        except Exception:
            return float(default)


def _split_food_items(text):
    raw = str(text or "")
    if not raw.strip():
        return []

    # 쉼표/슬래시/플러스는 괄호 바깥에서만 분리한다.
    top = []
    buf = []
    depth = 0
    for ch in raw:
        if ch in "([{":
            depth += 1
            buf.append(ch)
            continue
        if ch in ")]}":
            depth = max(0, depth - 1)
            buf.append(ch)
            continue
        if depth == 0 and ch in {",", "/", "+"}:
            part = "".join(buf).strip()
            if part:
                top.append(part)
            buf = []
            continue
        buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        top.append(tail)

    parts = []
    for seg in top:
        sub = re.split(r"\n|\s+및\s+|\s+그리고\s+", seg)
        for p in sub:
            p = str(p or "").strip()
            if p:
                parts.append(p)
    return parts


def _is_negated_food_mention(item_text, keyword):
    t = str(item_text or "")
    if (not keyword) or (keyword not in t):
        return False
    for m in re.finditer(re.escape(keyword), t):
        s = max(0, m.start() - 10)
        e = min(len(t), m.end() + 10)
        ctx = t[s:e]
        if re.search(r"(없이|제외|빼고|없음|미포함|안\s*먹|x)", ctx, flags=re.IGNORECASE):
            return True
    return False


def _extract_portion_multiplier(item_text):
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
    if ml:
        return max(0.1, float(ml.group(1)) / 250.0)

    return 1.0


def estimate_nutrition_heuristic(user_text):
    txt = str(user_text or "").strip()
    items = _split_food_items(txt)
    if not items:
        items = [txt]

    total_kcal = 0.0
    total_carbs = 0.0
    total_protein = 0.0
    total_fat = 0.0
    matched = []
    keys = sorted(HEURISTIC_NUTRITION_PROFILE.keys(), key=len, reverse=True)

    for item in items:
        chosen = None
        for k in keys:
            if k in item:
                if _is_negated_food_mention(item, k):
                    continue
                chosen = k
                break
        if not chosen:
            continue
        profile = HEURISTIC_NUTRITION_PROFILE.get(chosen, {})
        mult = _extract_portion_multiplier(item)
        total_kcal += float(profile.get("kcal", 0.0)) * mult
        total_carbs += float(profile.get("carbs", 0.0)) * mult
        total_protein += float(profile.get("protein", 0.0)) * mult
        total_fat += float(profile.get("fat", 0.0)) * mult
        matched.append(chosen)

    if total_kcal <= 0:
        total_kcal = float(_estimate_kcal_floor_from_text(txt))

    if (total_carbs + total_protein + total_fat) <= 0 and total_kcal > 0:
        # Default macro split when token-macro mapping is missing.
        total_carbs = (total_kcal * 0.50) / 4.0
        total_protein = (total_kcal * 0.20) / 4.0
        total_fat = (total_kcal * 0.30) / 9.0

    return {
        "calories": int(round(total_kcal)),
        "carbs": round(total_carbs, 1),
        "protein": round(total_protein, 1),
        "fat": round(total_fat, 1),
        "matched": matched,
    }


def _estimate_kcal_floor_from_text(user_text):
    txt = str(user_text or "")
    items = _split_food_items(txt)
    item_n = max(1, len(items))

    # 단순 안전 추정: 1개 메뉴 기준 450kcal, 튀김/면류/중식 키워드는 가산
    base = 450 * item_n
    bonus = 0
    heavy_tokens = ["치킨", "탕수육", "피자", "햄버거", "라면", "짜장", "볶음", "튀김", "돈까스"]
    for t in heavy_tokens:
        if t in txt:
            bonus += 180

    est = int(base + bonus)
    return max(350, est)


@st.cache_data(ttl=3600 * 24 * 14, show_spinner=False)
def estimate_nutrition_from_text(user_text, timeout_sec=OPENAI_NUTRITION_TIMEOUT_SEC):
    txt = str(user_text or "").strip()
    if not txt:
        return {
            "calories": 0,
            "protein": 0.0,
            "fat": 0.0,
            "carbs": 0.0,
            "matched": [],
            "source": "openai",
        }

    if not OPENAI_API_KEY:
        return {
            "calories": 0,
            "protein": 0.0,
            "fat": 0.0,
            "carbs": 0.0,
            "matched": [],
            "source": "openai",
        }

    prompt = f"""
You are a nutrition estimator. Return JSON only.
Estimate calories and macros for this Korean food log text:
"{txt}"

JSON schema:
{{
  "calories": number,
  "carbs": number,
  "protein": number,
  "fat": number,
  "matched": ["item1", "item2"]
}}

Rules:
- Use realistic Korean serving assumptions.
- If quantity is missing, use a typical single serving.
- calories must be >= 0.
- carbs/protein/fat are grams and must be >= 0.
""".strip()

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            timeout=float(max(0.6, timeout_sec)),
        )
        obj = json.loads(resp.choices[0].message.content or "{}")
        calories = max(0, int(round(_safe_num_from_str(obj.get("calories", 0), 0.0))))
        carbs = max(0.0, float(_safe_num_from_str(obj.get("carbs", 0), 0.0)))
        protein = max(0.0, float(_safe_num_from_str(obj.get("protein", 0), 0.0)))
        fat = max(0.0, float(_safe_num_from_str(obj.get("fat", 0), 0.0)))
        matched = obj.get("matched", [])
        if not isinstance(matched, list):
            matched = []

        if calories <= 0 and (carbs > 0 or protein > 0 or fat > 0):
            calories = int(round(carbs * 4 + protein * 4 + fat * 9))

        return {
            "calories": int(calories),
            "protein": round(protein, 1),
            "fat": round(fat, 1),
            "carbs": round(carbs, 1),
            "matched": [str(x) for x in matched[:5]],
            "source": "openai",
        }
    except Exception:
        return {
            "calories": 0,
            "protein": 0.0,
            "fat": 0.0,
            "carbs": 0.0,
            "matched": [],
            "source": "openai",
        }


def parse_log_quick(category, user_text, log_time):
    """
    Tab3 저장 파서.
    섭취는 OpenAI 추정, 실패 시 휴리스틱 fallback.
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

    def _sum_float(pattern):
        vals = re.findall(pattern, txt, flags=re.IGNORECASE)
        if not vals:
            return 0.0
        s = 0.0
        for v in vals:
            try:
                if isinstance(v, tuple):
                    v = v[0]
                s += float(v)
            except Exception:
                continue
        return s

    def _extract_ml_for_keyword(keyword):
        # e.g. "맥주 500미리", "500ml 맥주", "소주 200ml"
        patterns = [
            rf"{keyword}[^0-9]{{0,10}}(\d+(?:\.\d+)?)\s*(?:ml|밀리|미리|cc)",
            rf"(\d+(?:\.\d+)?)\s*(?:ml|밀리|미리|cc)[^가-힣]{{0,4}}{keyword}",
        ]
        total = 0.0
        for p in patterns:
            total += _sum_float(p)
        return total

    def _extract_total_minutes():
        # Aggregate all durations in one sentence: "1시간 코어 20분" => 80
        mins = 0.0
        mins += _sum_float(r"(\d+(?:\.\d+)?)\s*(?:시간|hr|hour|hours|h)") * 60.0
        mins += _sum_float(r"(\d+(?:\.\d+)?)\s*(?:분|min|minute|minutes|m)")
        return int(round(mins))

    if "섭취" in category:
        # 기본값은 fast 모드(휴리스틱만)로 저장 지연을 최소화한다.
        # 필요 시 secrets의 NUTRITION_PARSE_MODE=balanced/openai 로 전환 가능.
        h_fast = estimate_nutrition_heuristic(txt)
        fast_matched = bool((h_fast.get("matched", []) or []))

        if NUTRITION_PARSE_MODE == "fast":
            est = h_fast
            nutrition_source = "heuristic_fast"
        elif NUTRITION_PARSE_MODE == "openai" and OPENAI_API_KEY:
            est = estimate_nutrition_from_text(txt, timeout_sec=OPENAI_NUTRITION_TIMEOUT_SEC)
            used_openai = int(est.get("calories", 0) or 0) > 0
            if not used_openai:
                est = h_fast
            nutrition_source = "openai" if used_openai else "heuristic"
        elif fast_matched:
            est = h_fast
            nutrition_source = "heuristic"
        else:
            if (NUTRITION_PARSE_MODE in {"balanced", "openai"}) and OPENAI_API_KEY:
                est = estimate_nutrition_from_text(txt, timeout_sec=OPENAI_NUTRITION_TIMEOUT_SEC)
                used_openai = int(est.get("calories", 0) or 0) > 0
                nutrition_source = "openai" if used_openai else "heuristic"
            else:
                est = h_fast
                nutrition_source = "heuristic"

        kcal = int(est.get("calories", 0) or 0)
        carbs = float(est.get("carbs", 0.0) or 0.0)
        protein = float(est.get("protein", 0.0) or 0.0)
        fat = float(est.get("fat", 0.0) or 0.0)
        if kcal <= 0:
            # fallback heuristic (외부 조회 실패 시)
            kcal = _first_int(r"(\d{2,4})\s*kcal", 0)
            if kcal <= 0:
                h_est = estimate_nutrition_heuristic(txt)
                kcal = int(h_est.get("calories", 0) or 0)
                carbs = float(h_est.get("carbs", 0.0) or 0.0)
                protein = float(h_est.get("protein", 0.0) or 0.0)
                fat = float(h_est.get("fat", 0.0) or 0.0)

        if (carbs <= 0 and protein <= 0 and fat <= 0) and kcal > 0:
            if nutrition_source == "heuristic":
                h_est2 = estimate_nutrition_heuristic(txt)
                carbs = float(h_est2.get("carbs", 0.0) or 0.0)
                protein = float(h_est2.get("protein", 0.0) or 0.0)
                fat = float(h_est2.get("fat", 0.0) or 0.0)
            if carbs <= 0 and protein <= 0 and fat <= 0:
                carbs = round((kcal * 0.50) / 4.0, 1)
                protein = round((kcal * 0.20) / 4.0, 1)
                fat = round((kcal * 0.30) / 9.0, 1)

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
            "nutrition_source": nutrition_source,
            "summary": f"섭취 기록 (약 {int(kcal)}kcal)" if kcal > 0 else "섭취 기록",
        }

    if "운동" in category:
        mins = _extract_total_minutes()
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
        # count-based
        soju_bottle = _sum_float(r"소주\s*(\d+(?:\.\d+)?)\s*병")
        soju_glass = _sum_float(r"소주\s*(\d+(?:\.\d+)?)\s*잔")
        beer_can = _sum_float(r"맥주\s*(\d+(?:\.\d+)?)\s*(?:캔|병)")
        beer_glass = _sum_float(r"맥주\s*(\d+(?:\.\d+)?)\s*잔")
        wine_bottle = _sum_float(r"와인\s*(\d+(?:\.\d+)?)\s*병")
        wine_glass = _sum_float(r"와인\s*(\d+(?:\.\d+)?)\s*잔")

        # volume-based fallback/addition
        soju_ml = _extract_ml_for_keyword("소주")
        beer_ml = _extract_ml_for_keyword("맥주")
        wine_ml = _extract_ml_for_keyword("와인")

        # 기준:
        # 소주 1병(360ml)=7잔 -> 1잔≈51.4ml
        # 맥주 1캔(355ml)=1.5잔 -> 1잔≈236.7ml
        # 와인 1병(750ml)=5잔 -> 1잔=150ml
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
        mins = _extract_total_minutes()
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
        marks = extract_df_marks_from_text(txt, allow_plain_numbers=True)
        return {
            "activity_type": "daily_five_completion",
            "df_marks": marks,
            "count": int(len(marks)),
            "summary": f"Daily Five 수행 체크 ({', '.join(marks)})" if marks else "Daily Five 체크 기록",
        }

    return {"summary": txt[:120]}


def handle_log_form_submit():
    try:
        txt = str(st.session_state.get("log_text_widget", "") or "").strip()
        if not txt:
            st.session_state["_log_submit_feedback"] = {"ok": False, "msg": "⚠️ 내용을 입력해주세요."}
            return

        now_kst = get_current_kst()
        raw_date = st.session_state.get("log_date_widget", now_kst.date())
        try:
            date_obj = pd.to_datetime(raw_date).date()
        except Exception:
            date_obj = now_kst.date()

        # UI uses slider keys (log_hour_slider_widget / log_minute_slider_widget).
        # Keep backward compatibility with legacy keys.
        raw_hour = st.session_state.get(
            "log_hour_slider_widget",
            st.session_state.get("log_hour_widget", now_kst.hour),
        )
        raw_minute = st.session_state.get(
            "log_minute_slider_widget",
            st.session_state.get("log_minute_widget", (now_kst.minute // 5) * 5),
        )
        hour = int(raw_hour or 0)
        minute = int(raw_minute or 0)
        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        category = str(st.session_state.get("log_category_widget", "") or "").strip()
        log_time = f"{hour:02d}:{minute:02d}"
        date_key = date_obj.strftime("%Y-%m-%d")

        parsed = parse_log_quick(category, txt, log_time)
        get_db_connection("Action_Log").append_row([
            date_key,
            log_time,
            category,
            txt,
            json.dumps(parsed, ensure_ascii=False),
            ""
        ])
        try:
            fetch_sheet_data.clear()
        except Exception:
            pass

        # DF 저장 직후에는 Sprint_Daily_Tasks Completed 동기화를 즉시 수행
        try:
            if str(category or "").upper() == "DF":
                sprint_now = get_active_sprint()
                if sprint_now and sprint_now.get("sprint_id"):
                    df_action_latest = pd.DataFrame(get_db_connection("Action_Log").get_all_records())
                    _ = get_daily_five_completion(
                        date_key=date_key,
                        sprint_id=sprint_now["sprint_id"],
                        df_action=df_action_latest,
                    )
        except Exception as e:
            print("df completion immediate sync error:", e)

        try:
            # DF 체크 저장은 Action Plan 즉시 재생성 필요도가 낮아 캐시 무효화를 생략한다.
            if str(category or "").upper() != "DF":
                d_mission = get_mission_date_key()
                invalidate_realtime_plan_cache(date_key)
                if d_mission != date_key:
                    invalidate_realtime_plan_cache(d_mission)
        except Exception as _cache_e:
            print("realtime cache invalidation error:", _cache_e)

        st.session_state["_today_summary_nonce"] = get_current_kst().strftime("%Y-%m-%d %H:%M:%S.%f")
        st.session_state["_log_submit_feedback"] = {"ok": True, "msg": "✅ 저장 완료!"}
    except Exception as e:
        st.session_state["_log_submit_feedback"] = {"ok": False, "msg": f"저장 실패: {e}"}


# ==========================================
# [메인 UI]
# ==========================================
_rollover_updates = run_daily_sprint_rollover_once()
if DEBUG_MODE and _rollover_updates > 0:
    print(f"sprint rollover updated rows: {_rollover_updates}")
_schema_synced = run_sheet_schema_sync_once()
if DEBUG_MODE and _schema_synced:
    print("sprint sheet schema synced")
_progress_backfilled = run_daily_progress_backfill_once()
if DEBUG_MODE and _progress_backfilled > 0:
    print(f"daily sprint progress backfilled rows: {_progress_backfilled}")

_dashboard_subpage = get_dashboard_subpage()
if _dashboard_subpage == "makjang":
    st.markdown("### 일상 막장 지수 상세")
    c_back, c_empty = st.columns([0.18, 0.82])
    with c_back:
        if st.button("← 대시보드", width="stretch"):
            set_dashboard_subpage("")
            st.rerun()
    with c_empty:
        st.caption("최근 3일 점수 산정 근거")

    try:
        date_key_mj = get_mission_date_key()
        df_action_mj = pd.DataFrame(fetch_sheet_data("Action_Log"))
        mj_detail = compute_makjang_3day_score(date_key_mj, df_action_mj)
        st.metric("일상 막장 지수", f"{int(mj_detail.get('score', 0))}/100")
        render_makjang_score_drilldown(mj_detail)
    except Exception as e:
        st.error(f"막장지수 상세 로딩 실패: {e}")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["DASHBOARD", "SPRINT", "LOG", "PIT WALL", "PLAYERS BOX"])

# [TAB 1] Dashboard
with tab1:
    try:
        df_h = pd.DataFrame(fetch_sheet_data("Health_Log"))
        df_a = pd.DataFrame(fetch_sheet_data("Action_Log"))

        if not df_h.empty:
            now_kst = get_current_kst()
            date_key = get_mission_date_key()

            # 1) 캘린더 -> 슬롯 생성
            cal_evts = get_today_calendar_events(date_key)
            available_slots = build_available_slots(date_key, cal_evts)

            # 2) 오늘 액션 로그
            today_logs = df_a[df_a['Date'] == date_key]
            if "Category" in today_logs.columns:
                today_logs = today_logs[~today_logs["Category"].astype(str).str.upper().str.contains("DF", na=False)]
            today_acts = [f"[{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in today_logs.iterrows()]

            # 3) Health 최신값 (w_c 먼저!)
            latest_health = _latest_health_values(df_h)
            hrv_c = latest_health["HRV"]
            rhr_c = latest_health["RHR"]
            w_c   = latest_health["Weight"]

            # 4) xC 계산
            xc = None
            sprint = None
            progress = None
            daily_state = {}
            try:
                sprint = get_active_sprint()
                if sprint:
                    progress = calculate_sprint_progress(sprint, w_c)
                    daily_state = build_daily_state(
                        date_key=date_key,
                        now_kst=now_kst,
                        df_action=df_a,
                        cal_evts=cal_evts,
                        available_slots=available_slots,
                        sprint_progress=progress,
                        current_hrv=hrv_c,
                        current_rhr=rhr_c,
                    )
                    xc = get_or_create_daily_xc(date_key, sprint, daily_state)
                    if xc and (xc.get("xc_value_kg") is not None):
                        daily_state["xc"] = {
                            "xc_value_kg": float(xc.get("xc_value_kg")),
                            "xc_reason": list(xc.get("xc_reason", []) or []),
                        }
                        daily_state["urgency"] = compute_urgency(daily_state)
            except Exception as e:
                print("xC error:", e)
                xc = None

            daily_five_focus = {
                "has_plan": False,
                "completed": 0,
                "total": 0,
                "completion_rate": 0.0,
                "remaining_count": 0,
                "remaining_tasks": [],
                "summary_line": "DF 계획 없음",
                "signature": "no_plan",
            }
            if sprint and progress and daily_state:
                try:
                    daily_five_focus = build_daily_five_focus_snapshot(date_key, sprint["sprint_id"], df_a)
                    daily_five_status_for_sheet = {
                        "has_plan": bool(daily_five_focus.get("has_plan", False)),
                        "completed": int(daily_five_focus.get("completed", 0)),
                        "total": int(daily_five_focus.get("total", 0)),
                        "completion_rate": float(daily_five_focus.get("completion_rate", 0.0)),
                    }
                    persist_daily_sprint_progress(
                        date_key=date_key,
                        sprint_id=sprint["sprint_id"],
                        daily_state=daily_state,
                        daily_five_status=daily_five_status_for_sheet,
                        sprint_progress=progress,
                    )
                except Exception as e:
                    print("persist daily sprint progress (tab1) error:", e)

            
            mission = calculate_mission_status(w_c)
            
            mj = compute_makjang_3day_score(date_key, df_a)
            mj_score = mj["score"]
            last_updated_badge = _get_health_last_update_badge(df_h, now_kst)

            st.markdown(
                f"""<h3 style="margin-bottom: 10px;">Real-time Bio-Stat <span class="time-badge">{last_updated_badge} 기준</span></h3>""",
                unsafe_allow_html=True,
            )

            hrv_icon = "🟢" if hrv_c >= 45 else "🔴"
            rhr_icon = "🟢" if rhr_c <= 65 else "🔴"

            dashboard_html = f"""
<div style="display: flex; gap: 8px; margin-bottom: 20px; width: 100%;">
<div style="flex: 1; background: #0d1627; padding: 12px 5px; border-radius: 12px; border: 1px solid #1f2d46; text-align: center;">
<div style="font-size: 14px; color: #8fa8c7; font-weight: 600; margin-bottom: 4px;">HRV</div>
<div style="font-size: 33px; font-weight: 900; color: #f8fafc; margin-bottom: 4px;">{hrv_c:.1f}</div>
<div style="font-size: 11px; color: #8fa8c7;">{hrv_icon} (평균:40)</div>
</div>
<div style="flex: 1; background: #0d1627; padding: 12px 5px; border-radius: 12px; border: 1px solid #1f2d46; text-align: center;">
<div style="font-size: 14px; color: #8fa8c7; font-weight: 600; margin-bottom: 4px;">RHR</div>
<div style="font-size: 33px; font-weight: 900; color: #f8fafc; margin-bottom: 4px;">{rhr_c:.1f}</div>
<div style="font-size: 11px; color: #8fa8c7;">{rhr_icon} (평균:65)</div>
</div>
<a href="?dash=makjang" style="flex:1; display:flex; align-items:stretch; text-decoration:none; color:inherit; -webkit-tap-highlight-color: transparent;">
<div style="width:100%; min-height:100%; background: #0d1627; padding: 14px 8px; border-radius: 12px; border: 1px solid #1f2d46; text-align: center; cursor:pointer;">
<div style="font-size: 14px; color: #8fa8c7; font-weight: 600; margin-bottom: 4px;">일상 막장 지수</div>
<div style="font-size: 33px; font-weight: 900; color: #f8fafc; margin-bottom: 4px;">{mj_score}</div>
<div style="font-size: 11px; color: #8fa8c7;">/100 </div>
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
                today_latest = _latest_health_values(
                    today_h,
                    defaults={"Weight": w_c, "HRV": hrv_c, "RHR": rhr_c}
                )
                m_weight = today_latest["Weight"]
                m_hrv = today_latest["HRV"]
                m_rhr = today_latest["RHR"]
                m_ctx = prepare_full_context(df_h, df_a, m_weight, True)

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
                            m_hrv,
                            m_rhr,
                            m_weight,
                            m_ctx,
                            cal_txt
                        )
                        ck_res["generated_at_kst"] = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
                        ck_res["date_key"] = date_key
                        save_checkin_cache(date_key, ck_res)
                        clear_old_caches()

                generated_at = str((ck_res or {}).get("generated_at_kst", "") or "")
                checkin_time = generated_at[11:16] if len(generated_at) >= 16 else now_kst.strftime('%H:%M')

                try:
                    sprint = get_active_sprint()
                    if sprint:
                        if not load_dailyfive_cache(date_key, sprint['sprint_id']):
                            ywr = summarize_yesterday_workout_review(df_a, date_key)
                            five = ai_generate_daily_five(
                                date_key,
                                sprint,
                                {'weight': m_weight, 'hrv': m_hrv, 'rhr': m_rhr},
                                {'available_slots': available_slots, 'yesterday_workout_review': ywr}  # ✅ [FIX]
                            )
                            if five:
                                save_dailyfive_cache(date_key, sprint['sprint_id'], five)
                        # DF 로그가 tasks 생성보다 먼저 들어온 경우를 포함해, 렌더 시점에 완료 상태를 재동기화
                        try:
                            _ = get_daily_five_completion(date_key, sprint['sprint_id'], df_a)
                        except Exception as e:
                            print("daily five completion sync (tab1 render) error:", e)
                except:
                    pass

                headline = polish_korean_coaching_text((ck_res or {}).get("headline") or "오늘 컨디션 체크")
                checkin_analysis = polish_korean_coaching_text((ck_res or {}).get("analysis", "-"))
                mission_workout = polish_korean_coaching_text(ck_res.get("mission_workout", "-"))
                mission_diet = polish_korean_coaching_text(ck_res.get("mission_diet", "-"))
                mission_recovery = polish_korean_coaching_text(ck_res.get("mission_recovery", "-"))
                checkin_analysis_html = _html_escape_multiline(checkin_analysis)
                mission_workout_html = _html_escape_multiline(mission_workout)
                mission_diet_html = _html_escape_multiline(mission_diet)
                mission_recovery_html = _html_escape_multiline(mission_recovery)
                with st.container(border=True):
                    st.markdown(
                        f"""<h3 style="margin:0 0 8px 0;">☀️ Daily Check-in <span class="time-badge">{checkin_time} 생성</span></h3>""",
                        unsafe_allow_html=True,
                    )
                    st.subheader(f"{headline}")
                    st.markdown(
                        f"""<div><strong>분석:</strong> {checkin_analysis_html}</div>""",
                        unsafe_allow_html=True,
                    )
                    st.write("")
                    st.markdown("**오늘의 전략**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"""<div class="strategy-box workout-box"><span class="strategy-title">운동</span>{mission_workout_html}</div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div class="strategy-box diet-box"><span class="strategy-title">식단</span>{mission_diet_html}</div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""<div class="strategy-box recovery-box"><span class="strategy-title">회복</span>{mission_recovery_html}</div>""", unsafe_allow_html=True)
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
                        xc=xc,
                    )
                wrapup = get_or_create_wrapup(
                    kind=wrapup_kind,
                    cache_key=f"{date_key}_{WRAPUP_CACHE_VERSION}",
                    payload=wrapup_payload,
                )
                render_wrapup_block(wrapup_kind, wrapup, xc=xc)
            else:
                daily_five_sig = str(daily_five_focus.get("signature", "") or "")
                # ✅ [FIX] Action Plan 호출: calendar를 logs에 섞어 넣지 말고 slots로 전달
                ap = ai_generate_action_plan(
                    hrv_c, rhr_c, w_c,
                    rt_ctx,
                    today_acts,
                    available_slots,
                    daily_five_sig=daily_five_sig,
                )

                with st.container(border=True):
                    st.markdown(f"""<h3 style="margin-bottom: 10px;">Action Plan <span class="time-badge">{ap.get('generated_at', now_kst.strftime('%H:%M'))} 기준</span></h3>""", unsafe_allow_html=True)
                    if xc and (xc.get("xc_value_kg") is not None):
                        st.caption(format_xc_caption_text(xc.get("xc_value_kg")))
                    st.markdown("**지금 상황**")
                    st.markdown(format_coaching_readability_markdown(ap.get("current_analysis", "")))
                    st.markdown("")
                    st.markdown("**현 시점 제안**")
                    st.markdown(format_coaching_readability_markdown(ap.get("next_actions", "")))
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
                df_h = pd.DataFrame(fetch_sheet_data("Health_Log"))
                if df_h.empty:
                    return None
                latest = _latest_health_values(df_h)
                return {
                    'weight': latest["Weight"],
                    'hrv': latest["HRV"],
                    'rhr': latest["RHR"]
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
                    today_kst = get_current_kst().date()
                    latest_ended = get_latest_ended_sprint(today_kst.strftime("%Y-%m-%d"))
                    should_show_retro = (
                        bool(latest_ended) and
                        bool(latest_ended.get("end_date")) and
                        (today_kst == (latest_ended["end_date"] + timedelta(days=1)))
                    )
                    if should_show_retro:
                        df_h_retro = pd.DataFrame(fetch_sheet_data("Health_Log"))
                        df_action_retro = pd.DataFrame(fetch_sheet_data("Action_Log"))
                        retro_payload = build_sprint_retro_payload(
                            latest_ended,
                            df_h_retro,
                            df_action_retro,
                        )
                        if retro_payload:
                            retro_cache_key = (
                                f"{latest_ended.get('sprint_id','')}_"
                                f"{latest_ended.get('end_date').strftime('%Y-%m-%d')}_"
                                f"{WRAPUP_CACHE_VERSION}"
                            )
                            retro = get_or_create_sprint_retro(retro_cache_key, retro_payload)
                            render_sprint_retro_block(retro, retro_payload)
                        else:
                            st.info("직전 Sprint 회고를 생성할 데이터가 부족합니다.")
                    else:
                        st.info("진행 중인 Sprint가 없습니다")
                else:
                    st.markdown(f"### Sprint: {sprint['name']}")

                    date_key = get_mission_date_key()

                    df_h = pd.DataFrame(fetch_sheet_data("Health_Log"))
                    
                    cal_events = get_today_calendar_events(date_key)
                    available_slots = build_available_slots(date_key, cal_events)

                    progress = calculate_sprint_progress(sprint, current_weight)
                    df_action_tab2 = pd.DataFrame(fetch_sheet_data("Action_Log"))
                    daily_state = build_daily_state(
                        date_key=date_key,
                        now_kst=get_current_kst(),
                        df_action=df_action_tab2,
                        cal_evts=cal_events,
                        available_slots=available_slots,
                        sprint_progress=progress,
                        current_hrv=current_hrv,
                        current_rhr=current_rhr,
                    )
                    xc = get_or_create_daily_xc(date_key, sprint, daily_state)
                    if xc and (xc.get("xc_value_kg") is not None):
                        daily_state["xc"] = {
                            "xc_value_kg": float(xc.get("xc_value_kg")),
                            "xc_reason": list(xc.get("xc_reason", []) or []),
                        }
                        daily_state["urgency"] = compute_urgency(daily_state)
                    xc_value = xc.get("xc_value_kg") if xc else None
                    try:
                        df_focus_tab2 = build_daily_five_focus_snapshot(date_key, sprint["sprint_id"], df_action_tab2)
                        daily_five_status_tab2 = {
                            "has_plan": bool(df_focus_tab2.get("has_plan", False)),
                            "completed": int(df_focus_tab2.get("completed", 0)),
                            "total": int(df_focus_tab2.get("total", 0)),
                            "completion_rate": float(df_focus_tab2.get("completion_rate", 0.0)),
                        }
                        persist_daily_sprint_progress(
                            date_key=date_key,
                            sprint_id=sprint["sprint_id"],
                            daily_state=daily_state,
                            daily_five_status=daily_five_status_tab2,
                            sprint_progress=progress,
                        )
                    except Exception as e:
                        print("persist daily sprint progress (tab2) error:", e)

                    if progress:
                        with st.container(border=True):
                            day = progress['day']
                            total = progress['sprint']['duration_days']
                            day_progress_pct = 0.0
                            if int(total) > 0:
                                day_progress_pct = min(100.0, max(0.0, (float(day) / float(total)) * 100.0))

                            st.caption(f"Day {day}/{total}")
                            st.markdown(
                                f"""
<div style="width:100%; height:16px; background:#22293a; border-radius:999px; overflow:hidden; margin:2px 0 4px 0;">
  <div style="height:100%; width:{day_progress_pct:.2f}%; background:linear-gradient(90deg, #1d7bf2 0%, #3ea3ff 100%); border-radius:999px;"></div>
</div>
""",
                                unsafe_allow_html=True,
                            )

                            st.write("")

                            status_html = f"""
                            <div style="display: flex; gap: 8px; margin-bottom: 16px; width: 100%;">
                            <div style="flex: 1; background: #0d1627; padding: 12px 5px; border-radius: 12px; border: 1px solid #1f2d46; text-align: center;">
                            <div style="font-size: 14px; color: #8fa8c7; font-weight: 600; margin-bottom: 4px;">시작</div>
                            <div style="font-size: 33px; font-weight: 900; color: #f8fafc; margin-bottom: 4px;">{progress['weight_start']:.1f}kg</div>
                            <div style="font-size: 11px; color: #8fa8c7;">기준</div>
                            </div>
                            <div style="flex: 1; background: #0d1627; padding: 12px 5px; border-radius: 12px; border: 1px solid #1f2d46; text-align: center;">
                            <div style="font-size: 14px; color: #8fa8c7; font-weight: 600; margin-bottom: 4px;">현재</div>
                            <div style="font-size: 33px; font-weight: 900; color: #f8fafc; margin-bottom: 4px;">{progress['weight_current']:.1f}kg</div>
                            <div style="font-size: 11px; color: #3B82F6;">{progress['weight_current'] - progress['weight_start']:.1f}kg</div>
                            </div>
                            <div style="flex: 1; background: #0d1627; padding: 12px 5px; border-radius: 12px; border: 1px solid #1f2d46; text-align: center;">
                            <div style="font-size: 14px; color: #8fa8c7; font-weight: 600; margin-bottom: 4px;">목표</div>
                            <div style="font-size: 33px; font-weight: 900; color: #f8fafc; margin-bottom: 4px;">{progress['weight_target']:.1f}kg</div>
                            <div style="font-size: 11px; color: #8fa8c7;">타깃</div>
                            </div>
                            </div>
                            """
                            st.markdown(status_html, unsafe_allow_html=True)

                            delta = progress['weight_delta']
                            pace_status = progress['pace_status']
                            prev_fb = get_prev_xc_feedback(sprint["sprint_id"], date_key)

                            # ✅ [FIX] 메시지/남은kg 계산을 pace_weight(=trend 우선) 기준으로 통일
                            remaining = progress['pace_weight'] - progress['weight_target']

                            prev_gap = _safe_float(prev_fb.get("gap_kg"), None)
                            prev_xc = _safe_float(prev_fb.get("prev_xc_kg"), None)
                            prev_actual = _safe_float(prev_fb.get("actual_change_kg"), None)
                            prev_date = str(prev_fb.get("date") or "").strip()
                            prev_ach = _safe_float(prev_fb.get("achievement_pct"), None)
                            if prev_date and (prev_gap is not None):
                                if prev_gap > 0:
                                    msg = (
                                        f"🧨 어제({prev_date}) xC 미달: 목표 {prev_xc:.2f}kg / 실제 {prev_actual:.2f}kg "
                                        f"(미달 {prev_gap:.2f}kg)"
                                    ) if (prev_xc is not None and prev_actual is not None) else (
                                        f"🧨 어제({prev_date}) xC 미달: {prev_gap:.2f}kg"
                                    )
                                    st.error(msg)
                                else:
                                    msg = (
                                        f"✅ 어제({prev_date}) xC 달성: 목표 {prev_xc:.2f}kg / 실제 {prev_actual:.2f}kg "
                                        f"(초과 {abs(prev_gap):.2f}kg)"
                                    ) if (prev_xc is not None and prev_actual is not None) else (
                                        f"✅ 어제({prev_date}) xC 달성"
                                    )
                                    if prev_ach is not None:
                                        msg = f"{msg} / 달성률 {prev_ach:.0f}%"
                                    st.success(msg)

                            if pace_status == 'ahead':
                                st.success(f"🟢 목표보다 {abs(delta):.1f}kg 앞서감! ({remaining:.1f}kg 남음)")
                            
                            elif pace_status == 'behind':
                                st.markdown(
                                    f"""
                                    <div style="
                                        background: #111f36;
                                        border: 1px solid #33527f;
                                        padding: 12px 14px;
                                        border-radius: 12px;
                                        margin: 6px 0 8px 0;
                                    ">
                                    <div style="
                                        color: #fca5a5;
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
                                st.info(f"페이스 기준선 구간 ({remaining:.1f}kg 남음)")

                            linear_expected = progress["weight_expected"]

                            st.caption(f"📏 기계식 페이스 {linear_expected:.2f}kg")

                            if xc_value is not None:
                                st.caption(format_xc_caption_text(xc_value))
                            else:
                                st.caption("xC 참고값 없음")


                    st.markdown("""<h3 style="margin-bottom: 10px;">Sprint: Daily Five <span class="time-badge">05:00 생성</span></h3>""", unsafe_allow_html=True)

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

                    # DF 로그가 먼저 저장된 경우를 포함해, 화면 진입 시 completion 컬럼을 보정
                    try:
                        _ = get_daily_five_completion(date_key, sprint['sprint_id'], df_action_tab2)
                    except Exception as e:
                        print("daily five completion sync (tab2 render) error:", e)

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

                        done_map = {}
                        try:
                            today_logs_tab2 = (
                                df_action_tab2[df_action_tab2["Date"] == date_key]
                                if ("Date" in df_action_tab2.columns) else df_action_tab2
                            )
                            marks_tab2 = collect_dailyfive_completion_marks(today_logs_tab2)
                            done_rows_tab2 = build_dailyfive_done_rows(daily_five.get("tasks", []), marks_tab2)
                            done_map = {int(r.get("index", 0)): bool(r.get("done")) for r in done_rows_tab2}
                        except Exception:
                            done_map = {}

                        for idx, task in enumerate(daily_five['tasks'], start=1):
                            done = bool(done_map.get(idx, False))
                            icon = "✅" if done else "⬜"
                            display_title = polish_korean_coaching_text(str(task.get("title", "") or "").strip())
                            display_desc = polish_korean_coaching_text(str(task.get("description", "") or "").strip())
                            display_why = polish_korean_coaching_text(str(task.get("why", "") or "").strip())
                            if done:
                                bg_color = "#111a2b"
                                title_color = "#cbd5e1"
                                done_badge = '<span style="font-size:11px; font-weight:700; color:#dbeafe; background:#334155; border-radius:8px; padding:2px 8px; margin-left:8px;">완료</span>'
                            else:
                                bg_color = "#0d1627"
                                title_color = "#f8fafc"
                                done_badge = ""

                            task_html = f"""
                            <div style="background: {bg_color}; padding: 16px; border-radius: 12px; border: 1px solid #1f2d46; border-left: 4px solid #4b83d6; margin-bottom: 10px;">
                            <div style="display: flex; align-items: flex-start; gap: 12px;">
                            <div style="font-size: 24px; line-height: 1;">{icon}</div>
                            <div style="flex: 1;">
                            <div style="font-weight: 700; color: {title_color}; font-size: 16px; margin-bottom: 6px;">{display_title}{done_badge}</div>
                            <div style="font-size: 13px; color: #9fb0c6; margin-bottom: 2px;">{display_desc}</div>
                            {f'<div style="font-size: 12px; color: #7f93b0; font-style: italic;">💡 {display_why}</div>' if display_why else ''}
                            </div>
                            </div>
                            </div>
                            """
                            st.markdown(task_html, unsafe_allow_html=True)

                    else:
                        st.warning("데일리 파이브 생성 실패")

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
    if "_today_summary_nonce" not in st.session_state:
        st.session_state["_today_summary_nonce"] = "0"

    st.markdown("### 오늘의 기록")

    @st.cache_data(ttl=300)
    def get_today_summary(date_str, nonce="0"):
        cal = 0
        mins = 0
        try:
            df_a = pd.DataFrame(fetch_sheet_data("Action_Log"))

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

    summary = get_today_summary(today_str, st.session_state.get("_today_summary_nonce", "0"))

    summary_html = f"""
    <div style="display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap;">
      <div style="flex:1; min-width:140px; background:#0d1627; padding:14px 8px; border-radius:12px; border:1px solid #1f2d46; text-align:center;">
        <div style="font-size:12px; color:#8fa8c7; font-weight:600; margin-bottom:6px;">섭취 칼로리</div>
        <div style="font-size:22px; font-weight:900; color:#f8fafc;">{summary['calories']} kcal</div>
      </div>

      <div style="flex:1; min-width:140px; background:#0d1627; padding:14px 8px; border-radius:12px; border:1px solid #1f2d46; text-align:center;">
        <div style="font-size:12px; color:#8fa8c7; font-weight:600; margin-bottom:6px;">운동 시간</div>
        <div style="font-size:22px; font-weight:900; color:#f8fafc;">{summary['minutes']} 분</div>
      </div>

      <div style="flex:1; min-width:140px; background:#0d1627; padding:14px 8px; border-radius:12px; border:1px solid #1f2d46; text-align:center;">
        <div style="font-size:12px; color:#8fa8c7; font-weight:600; margin-bottom:6px;">Dry Feb</div>
        <div style="font-size:22px; font-weight:900; color:#f8fafc;">{now_kst.day}/28일</div>
      </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 기록하기")

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
                hour_options = [f"{h:02d}" for h in range(0, 24)]
                log_hour_label = st.select_slider(
                    "시",
                    options=hour_options,
                    value=f"{default_hour:02d}",
                    key="log_hour_slider_widget",
                    label_visibility="collapsed",
                )
            with c3:
                minute_options = [f"{m:02d}" for m in range(0, 60, 5)]
                log_minute_label = st.select_slider(
                    "분",
                    options=minute_options,
                    value=f"{default_minute:02d}" if f"{default_minute:02d}" in minute_options else "00",
                    key="log_minute_slider_widget",
                    label_visibility="collapsed",
                )
            with c4:
                log_category = st.selectbox("카테고리", options=categories, index=0, key="log_category_widget", label_visibility="collapsed")

            log_time = f"{int(log_hour_label):02d}:{int(log_minute_label):02d}"

            log_text = st.text_area(
                "내용",
                placeholder="예: 닭가슴살 샐러드 / 러닝 5km / 맥주 2잔 / SAT 복용 / 사우나 2세트 / 야근으로 운동 못함",
                height=120,
                key="log_text_widget",
                label_visibility="collapsed",
            )

            st.form_submit_button("🚀 저장", width="stretch", on_click=handle_log_form_submit)

        feedback = st.session_state.pop("_log_submit_feedback", None)
        if feedback:
            if bool(feedback.get("ok")):
                st.success(str(feedback.get("msg") or "✅ 저장 완료!"))
            else:
                st.error(str(feedback.get("msg") or "저장 실패"))

    st.divider()

    with st.expander("아카이브", expanded=False):

        @st.cache_data(ttl=300)
        def load_archive_data():
            return pd.DataFrame(fetch_sheet_data("Action_Log"))

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
    st.markdown("## The Pit Wall")

    pit_start = None
    try:
        pit_start_cfg = str(st.secrets.get("PITWALL_START_DATE", PITWALL_START_DATE_DEFAULT) or PITWALL_START_DATE_DEFAULT).strip()
        pit_start = _safe_parse_ymd(pit_start_cfg)
    except:
        pit_start = None
    pit_start = _align_date_to_saturday(pit_start)

    if pit_start is None:
        try:
            sprint_for_pit = get_active_sprint()
            if sprint_for_pit and sprint_for_pit.get("start_date"):
                pit_start = _align_date_to_saturday(sprint_for_pit["start_date"].date())
        except:
            pit_start = None
    if pit_start is None:
        pit_start = _align_date_to_saturday(get_current_kst().date())

    try:
        df_action_pit = pd.DataFrame(fetch_sheet_data("Action_Log"))
    except:
        df_action_pit = pd.DataFrame()

    try:
        df_health_pit = pd.DataFrame(fetch_sheet_data("Health_Log"))
    except:
        df_health_pit = pd.DataFrame()

    try:
        pit_rhr_start = _safe_float(st.secrets.get("PITWALL_RHR_START", PITWALL_RHR_START_DEFAULT), PITWALL_RHR_START_DEFAULT)
    except:
        pit_rhr_start = PITWALL_RHR_START_DEFAULT
    try:
        pit_rhr_target = _safe_float(st.secrets.get("PITWALL_RHR_TARGET", PITWALL_RHR_TARGET_DEFAULT), PITWALL_RHR_TARGET_DEFAULT)
    except:
        pit_rhr_target = PITWALL_RHR_TARGET_DEFAULT

    pit_board = build_pitwall_cardio_experiment(
        df_action=df_action_pit,
        df_health=df_health_pit,
        start_date=pit_start,
        weeks=PITWALL_CARDIO_WEEKS,
        rhr_start=pit_rhr_start,
        rhr_target=pit_rhr_target,
    )
    render_pitwall_cardio_experiment(pit_board)

    with st.expander("개발자 도구", expanded=False):
        st.write("server now:", datetime.now())
        st.write("kst now:", get_current_kst())
        st.write("experiment start:", pit_start)
        st.write("debug mode:", DEBUG_MODE)

        if DEBUG_MODE:
            try:
                date_key_dbg = get_mission_date_key()
                now_kst_dbg = get_current_kst()
                df_action_dbg = pd.DataFrame(fetch_sheet_data("Action_Log"))
                cal_dbg = get_today_calendar_events(date_key_dbg)
                slots_dbg = build_available_slots(date_key_dbg, cal_dbg)
                sprint_dbg = get_active_sprint()
                progress_dbg = None
                if sprint_dbg:
                    df_health_dbg = pd.DataFrame(fetch_sheet_data("Health_Log"))
                    current_w_dbg = (_latest_health_values(df_health_dbg)["Weight"] if not df_health_dbg.empty else 0.0)
                    progress_dbg = calculate_sprint_progress(sprint_dbg, current_w_dbg)

                ds_dbg = build_daily_state(
                    date_key=date_key_dbg,
                    now_kst=now_kst_dbg,
                    df_action=df_action_dbg,
                    cal_evts=cal_dbg,
                    available_slots=slots_dbg,
                    sprint_progress=progress_dbg,
                )
                st.write("daily_state preview:")
                st.json(ds_dbg)
            except Exception as e:
                st.warning(f"debug daily_state error: {e}")

        if st.button("🔄 전체 캐시 클리어"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("캐시 클리어 완료!")


# =========================================================
# [TAB 5] Player's Box
# =========================================================
with tab5:
    st.markdown("## Player's Box")
    pit_date_key = get_mission_date_key()
    pit_sprint = get_active_sprint()
    pit_sprint_id = str((pit_sprint or {}).get("sprint_id", "") or "")
    pit_cached = load_pit_chat_cache(pit_date_key)
    pit_cached_history = list(pit_cached.get("history", []) or [])
    pit_cached_pending = pit_cached.get("pending_patch")

    current_chat_date_key = str(st.session_state.get("pit_chat_date_key", "") or "")
    if current_chat_date_key != pit_date_key:
        st.session_state["pit_chat_date_key"] = pit_date_key
        st.session_state["pit_chat_history"] = pit_cached_history
        st.session_state["pit_pending_patch"] = pit_cached_pending if isinstance(pit_cached_pending, dict) else None
    else:
        if "pit_chat_history" not in st.session_state:
            st.session_state["pit_chat_history"] = pit_cached_history
        if "pit_pending_patch" not in st.session_state:
            st.session_state["pit_pending_patch"] = pit_cached_pending if isinstance(pit_cached_pending, dict) else None

    _, top_reset = st.columns([0.84, 0.16])
    with top_reset:
        if st.button("대화 초기화", width="stretch", key="pit_clear_chat_btn"):
            st.session_state["pit_chat_history"] = []
            st.session_state["pit_pending_patch"] = None
            clear_pit_chat_cache(pit_date_key)
            st.session_state["pit_patch_feedback"] = {"ok": True, "msg": "상담 기록을 초기화했습니다."}
            st.rerun()

    pit_feedback = st.session_state.pop("pit_patch_feedback", None)
    if pit_feedback:
        if pit_feedback.get("ok"):
            st.success(str(pit_feedback.get("msg", "반영 완료")))
        else:
            st.warning(str(pit_feedback.get("msg", "반영 실패")))

    with st.container(border=True):
        history = list(st.session_state.get("pit_chat_history", []) or [])
        chat_html = ['<div class="pit-chat-panel">']
        if history:
            for m in history[-16:]:
                role = str(m.get("role", "user"))
                text = str(m.get("text", "") or "").strip()
                if not text:
                    continue
                safe_text = _html_escape(text)
                if role == "assistant":
                    ts = str(m.get("ts", "") or "")
                    chat_html.append(
                        '<div class="pit-msg-row pit-msg-row-coach">'
                        + '<div class="pit-bubble pit-bubble-coach">'
                        + '<div class="pit-bubble-tag">COACH</div>'
                        + f'{safe_text}'
                        + (f'<div class="pit-bubble-tag" style="margin-top:6px; margin-bottom:0;">{_html_escape(ts)}</div>' if ts else "")
                        + '</div>'
                        + '</div>'
                    )
                else:
                    ts = str(m.get("ts", "") or "")
                    chat_html.append(
                        '<div class="pit-msg-row pit-msg-row-user">'
                        + '<div class="pit-bubble pit-bubble-user">'
                        + '<div class="pit-bubble-tag">YOU</div>'
                        + f'{safe_text}'
                        + (f'<div class="pit-bubble-tag" style="margin-top:6px; margin-bottom:0;">{_html_escape(ts)}</div>' if ts else "")
                        + '</div>'
                        + '</div>'
                    )
        else:
            chat_html.append('<div class="pit-empty">아직 상담 기록이 없습니다.</div>')
        chat_html.append('</div>')
        st.markdown("".join(chat_html), unsafe_allow_html=True)

    def _pit_submit_message(raw_msg):
        q = str(raw_msg or "").strip()
        if not q:
            st.warning("상담 내용을 입력해 주세요.")
            return
        consult_ctx = build_pitwall_consult_context(
            pit_date_key,
            str(st.session_state.get("_today_summary_nonce", "0")),
        )
        with st.spinner("코치가 상황을 분석 중입니다..."):
            ai_consult = ai_generate_pitwall_consultation(
                user_message=q,
                consult_context=consult_ctx,
                chat_history=st.session_state.get("pit_chat_history", []),
            )
        ts_now = get_current_kst().strftime("%H:%M")
        st.session_state["pit_chat_history"] = (
            list(st.session_state.get("pit_chat_history", []))
            + [{"role": "user", "text": q, "ts": ts_now}, {"role": "assistant", "text": str(ai_consult.get("coach_reply", "") or ""), "ts": ts_now}]
        )
        patch_obj = ai_consult.get("plan_patch", {}) or {}
        if bool(patch_obj.get("enabled")) and list(patch_obj.get("changes", []) or []):
            st.session_state["pit_pending_patch"] = patch_obj
        save_pit_chat_cache(
            pit_date_key,
            st.session_state.get("pit_chat_history", []),
            st.session_state.get("pit_pending_patch"),
        )
        st.rerun()

    st.caption("빠른 상담")
    q1, q2 = st.columns(2)
    with q1:
        if st.button("DF 우선 재정렬", width="stretch", key="pit_quick_df"):
            _pit_submit_message("남은 DF 항목 기준으로 오늘 우선순위를 다시 잡아 주세요.")
    with q2:
        if st.button("일정 기준 수정", width="stretch", key="pit_quick_schedule"):
            _pit_submit_message("오늘 캘린더/슬롯 기준으로 실행 가능한 계획으로 다시 맞춰 주세요.")
    q3, q4 = st.columns(2)
    with q3:
        if st.button("위기 모드", width="stretch", key="pit_quick_crisis"):
            _pit_submit_message("현재 페이스가 무너진 기준으로 강하게 경고하고 현 시점 우선 행동 1개를 제시해 주세요.")
    with q4:
        if st.button("계획 패치 제안", width="stretch", key="pit_quick_patch"):
            _pit_submit_message("오늘 Daily Five task_1~task_5 수정안을 JSON patch로 제시해 주세요.")

    with st.form("pit_coach_chat_form", clear_on_submit=True):
        in_col, send_col = st.columns([0.88, 0.12])
        with in_col:
            pit_user_msg = st.text_input(
                "상담 입력",
                placeholder="메시지를 입력하세요. 예) 오늘 남은 시간 기준으로 딱 1개 행동만 제시해줘",
                label_visibility="collapsed",
            )
        with send_col:
            pit_send = st.form_submit_button("➤", width="stretch", type="primary")

    if pit_send:
        _pit_submit_message(pit_user_msg)

    pending_patch = st.session_state.get("pit_pending_patch")
    if pending_patch and bool(pending_patch.get("enabled")):
        st.markdown("### Plan Patch Preview")
        with st.container(border=True):
            patch_date = str(pending_patch.get("date_key", pit_date_key) or pit_date_key)
            patch_reason = str(pending_patch.get("reason", "") or "").strip()
            st.caption(f"대상 일자: {patch_date}" + (f" | 사유: {patch_reason}" if patch_reason else ""))

            for i, ch in enumerate(list(pending_patch.get("changes", []) or []), start=1):
                task_id = str(ch.get("task_id", "") or "")
                updates = []
                for src, col in PITWALL_PATCH_FIELD_MAP.items():
                    if src in ch:
                        updates.append(f"{col}={ch.get(src)}")
                st.markdown(f"{i}. `{task_id}` -> " + (", ".join(updates) if updates else "(변경 없음)"))

            c_apply, c_drop = st.columns(2)
            with c_apply:
                if st.button("✅ 수정안 반영", width="stretch", key="pit_patch_apply_btn"):
                    if not pit_sprint_id:
                        st.session_state["pit_patch_feedback"] = {"ok": False, "msg": "활성 스프린트가 없어 반영할 수 없습니다."}
                    else:
                        patch_apply = dict(pending_patch)
                        patch_apply["date_key"] = patch_date
                        applied = apply_pitwall_plan_patch(pit_sprint_id, patch_apply)
                        st.session_state["pit_patch_feedback"] = {"ok": bool(applied.get("ok")), "msg": str(applied.get("message", ""))}
                    st.session_state["pit_pending_patch"] = None
                    save_pit_chat_cache(
                        pit_date_key,
                        st.session_state.get("pit_chat_history", []),
                        st.session_state.get("pit_pending_patch"),
                    )
                    st.rerun()
            with c_drop:
                if st.button("🗑️ 수정안 폐기", width="stretch", key="pit_patch_drop_btn"):
                    st.session_state["pit_pending_patch"] = None
                    st.session_state["pit_patch_feedback"] = {"ok": True, "msg": "수정안을 폐기했습니다."}
                    save_pit_chat_cache(
                        pit_date_key,
                        st.session_state.get("pit_chat_history", []),
                        st.session_state.get("pit_pending_patch"),
                    )
                    st.rerun()
