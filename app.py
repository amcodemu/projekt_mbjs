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
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"dailyfive_{date_key}_{sprint_id}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

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
        return None
    except:
        return None

def save_xw_cache(date_key, sprint_id, data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"xw_{date_key}_{sprint_id}.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_xw_cache(date_key, sprint_id):
    try:
        cache_file = os.path.join(CACHE_DIR, f"xw_{date_key}_{sprint_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except:
        return None



def clear_old_caches(keep_days=7):
    try:
        if not os.path.exists(CACHE_DIR):
            return
        now = datetime.now()
        for filename in os.listdir(CACHE_DIR):
            # ✅ [FIX] startswith 사용 오류 수정
            if filename.startswith(("checkin_", "dailyfive_", "trend_", "xw_")):
                filepath = os.path.join(CACHE_DIR, filename)
                if (now - datetime.fromtimestamp(os.path.getmtime(filepath))).days > keep_days:
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

LATE_MODE_START_HOUR = 20
LATE_MODE_START_MIN = 30  # 20:30 이후에는 장시간 운동 제안 금지를 위한 상수 

# xW(채찍) 세기 조절 파라미터
XW_PENALTY_BASE = 0.07          # 기본 채찍 (kg)
XW_PENALTY_MAX = 0.25           # 과도해지지 않게 상한 (kg)
XW_BEHIND_BONUS = 0.08          # 페이스 뒤처질 때 추가 채찍 (kg)
XW_NO_WORKOUT_SLOT_BONUS = 0.05 # 운동 슬롯이 막혀있을 때(대신 식단으로 더 조여야 함) (kg)
XW_WEEKEND_BONUS = 0.03         # 주말은 더 빡세게 (kg)


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

    # 혹시 남는 snake_case 토큰이 있으면 보기 좋게
    out = re.sub(r"\b([a-z]+_[a-z0-9_]+)\b", lambda m: m.group(1).replace("_", " "), out)
    return out


def build_dailyfive_status_text(date_key, sprint_id, df_action):
    daily_five = load_dailyfive_cache(date_key, sprint_id)
    if not daily_five or 'tasks' not in daily_five:
        return "Daily Five: None"

    today_logs = df_action[df_action['Date'] == date_key] if 'Date' in df_action.columns else df_action
    inputs = " ".join([str(x) for x in today_logs.get('User_Input', []).tolist()]) if not today_logs.empty else ""
    inputs_up = inputs.upper()

    lines = ["[DAILY FIVE CHECKLIST]"]
    for t in daily_five['tasks']:
        tid = str(t.get('task_id', '')).upper()
        title = str(t.get('title', '')).strip()

        done = False
        if tid and f"DF5:{tid}" in inputs_up.replace(" ", ""):
            done = True
        elif len(title) >= 6 and "DF5:" in inputs_up and title.upper()[:6] in inputs_up:
            done = True

        mark = "✅" if done else "⬜"
        lines.append(f"{mark} ({t.get('task_id','')}) {title}")

    lines.append("Rule: Mark ✅ when Action_Log contains 'DF5: task_id' or 'DF5: <title>'")
    return "\n".join(lines)

def get_current_kst():
    # 앱 전체에서 "KST 기준 시간"만 쓰도록 단일화
    # (나머지 로직이 naive datetime을 가정하므로 tzinfo 제거)
    return datetime.now(KST).replace(tzinfo=None)

def normalize_context_for_cache(context_str):
    import re
    normalized = re.sub(r'\(\d{2}:\d{2}\)', '(TIME)', context_str)
    normalized = re.sub(r'- \d{2}:\d{2}', '- TIME', normalized)
    return normalized

def get_mission_date_key():
    now_kst = get_current_kst()
    if now_kst.hour < 5:
        return (now_kst - timedelta(days=1)).strftime('%Y-%m-%d')
    return now_kst.strftime('%Y-%m-%d')

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
                    'start_date': datetime.strptime(row['Start_Date'], '%Y-%m-%d'),
                    'end_date': datetime.strptime(row['End_Date'], '%Y-%m-%d'),
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


BAD_FOOD_KEYS = ["야식", "라면", "치킨", "피자", "햄버거", "과자", "디저트", "빵", "떡", "면", "버거"]
# 필요하면 더 정교화: "적정선" 음식은 제외 키워드로 관리 가능

def _has_any(text, keys):
    t = (text or "").lower()
    return any(k.lower() in t for k in keys)

def compute_day_score(date_key, df_action):
    """
    return: day_score (대략 -40~+60 범위)
    """
    if df_action is None or df_action.empty or "Date" not in df_action.columns:
        return 0  # 데이터 없으면 중립

    day = df_action[df_action["Date"] == date_key].copy()
    if day.empty:
        return 0  # 기록 없으면 '모름'이지만, 3일 합산이니 일단 0(중립)로 둡니다

    cat_text = " ".join(day.get("Category", "").astype(str).tolist())
    inp_text = " ".join(day.get("User_Input", "").astype(str).tolist())

    has_alcohol = "음주" in cat_text
    has_workout = "운동" in cat_text
    has_bad_food = _has_any(inp_text, BAD_FOOD_KEYS)

    # 기록 공백 페널티(가벼움)
    # - 하루 로그가 1개 이하이면 “방치”로 +5
    low_logging = len(day) <= 1

    score = 0
    if has_alcohol:
        score += 30
    if has_bad_food:
        score += 15
    if has_workout:
        score -= 20
    if low_logging:
        score += 5

    # 시너지: 술+야식 같이 터지면 추가 벌점
    if has_alcohol and has_bad_food:
        score += 10

    return score

def compute_makjang_3day_score(today_key, df_action):
    """
    0~100
    50 = 중립(운동X/음주X/식사 적정선)
    """
    d0 = today_key
    d1 = (datetime.strptime(today_key, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (datetime.strptime(today_key, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")

    ds0 = compute_day_score(d0, df_action)
    ds1 = compute_day_score(d1, df_action)
    ds2 = compute_day_score(d2, df_action)

    raw = 50 + (0.5*ds0 + 0.3*ds1 + 0.2*ds2)
    score = int(round(max(0, min(100, raw))))

    return {
        "score": score,
        "d0": {"date": d0, "day_score": ds0},
        "d1": {"date": d1, "day_score": ds1},
        "d2": {"date": d2, "day_score": ds2},
        "method": "50 + weighted(day_scores)",
    }


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
                    'start_date': datetime.strptime(sprint['Start_Date'], '%Y-%m-%d'),
                    'end_date': datetime.strptime(sprint['End_Date'], '%Y-%m-%d'),
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
        days_passed = max(0, (now - sprint['start_date']).days)
        days_remaining = max(0, (sprint['end_date'] - now).days)

        goals = get_sprint_goals(sprint['sprint_id'])
        if 'weight' not in goals:
            return None

        weight_goal = goals['weight']
        total_loss = weight_goal['start_value'] - weight_goal['target_value']
        daily_target = total_loss / sprint['duration_days']
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
            'day': days_passed + 1,
            'days_remaining': days_remaining,
            'progress_pct': (days_passed / sprint['duration_days']) * 100,
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

def compute_xw_for_date(date_key, sprint, current_weight, trend_weight=None, available_slots=None):
    """
    xW_push(기대체중, 채찍선):
    - 선형 기대선(linear_expected)보다 항상 같거나 더 낮게(더 공격적으로) 설정
    - 매일 아침 1회 생성되어 하루 고정
    """
    if not sprint:
        return None

    goals = get_sprint_goals(sprint["sprint_id"])
    if "weight" not in goals:
        return None

    weight_goal = goals["weight"]
    total_loss = weight_goal["start_value"] - weight_goal["target_value"]
    daily_target = total_loss / sprint["duration_days"]

    now_kst = get_current_kst()
    days_passed = max(0, (now_kst - sprint["start_date"]).days)

    # 1) 선형 기대선
    linear_expected = weight_goal["start_value"] - (daily_target * days_passed)

    # 2) 페이스 판단은 trend 우선(없으면 current)
    pace_weight = trend_weight if (trend_weight is not None) else current_weight
    delta_vs_linear = pace_weight - linear_expected  # +면 뒤처짐, -면 앞섬

    # 3) 패널티 계산
    penalty = XW_PENALTY_BASE

    # 뒤처질수록 채찍 추가 (단, 너무 크게는 하지 말자)
    if delta_vs_linear > 0.20:
        penalty += XW_BEHIND_BONUS
    elif delta_vs_linear > 0.05:
        penalty += (XW_BEHIND_BONUS * 0.5)

    # 주말 보너스(주말은 변명 금지)
    dt = datetime.strptime(date_key, "%Y-%m-%d")
    if dt.weekday() >= 5:
        penalty += XW_WEEKEND_BONUS

    # 운동 슬롯이 “전부 막힘”이면(=운동으로 만회 불가) 식단으로 더 조여야 하니 penalty 추가
    if available_slots:
        any_workout_enabled = any(
            s.get("enabled") and any(t in (s.get("allowed_types") or []) for t in ["gym_full_120", "outdoor_run_60", "gym_quick_30", "walk_stairs", "tennis_90"])
            for s in available_slots
        )
        if not any_workout_enabled:
            penalty += XW_NO_WORKOUT_SLOT_BONUS

    # 상한
    penalty = min(XW_PENALTY_MAX, max(0.0, penalty))

    xw_push = linear_expected - penalty

    return {
        "xw_weight": float(xw_push),
        "method": "linear_minus_penalty",
        "linear_expected": float(linear_expected),
        "penalty_kg": float(penalty),
        "delta_vs_linear_pace": float(delta_vs_linear),
        "daily_target": float(daily_target),
        "days_passed": int(days_passed),
        "pace_weight_used": float(pace_weight),
    }


def get_or_create_daily_xw(date_key, sprint, current_weight, trend_weight=None, available_slots=None):
    if not sprint:
        return None

    cached = load_xw_cache(date_key, sprint["sprint_id"])
    if cached and cached.get("xw_weight") is not None:
        return cached

    computed = compute_xw_for_date(date_key, sprint, current_weight, trend_weight=trend_weight, available_slots=available_slots)
    if computed and computed.get("xw_weight") is not None:
        computed["computed_at_kst"] = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
        computed["date_key"] = date_key
        computed["sprint_id"] = sprint["sprint_id"]
        save_xw_cache(date_key, sprint["sprint_id"], computed)
        clear_old_caches()
        return computed

    return None



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

def get_today_calendar_events():
    """
    반환 형태:
    {
      "Sports": [{"title":..., "start_dt":..., "end_dt":..., "is_all_day": False}],
      "Termin": [...]
    }
    """
    try:
        creds = service_account.Credentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"],
            ['https://www.googleapis.com/auth/calendar.readonly']
        )
        service = build('calendar', 'v3', credentials=creds)

        now_kst = datetime.now(KST)
        start_kst = datetime.combine(now_kst.date(), time(0, 0), tzinfo=KST)
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

    lunch_blocked = has_termin_overlap(lunch_start, lunch_end)
    lunch_too_late = (now_kst.date() == dt.date()) and (now_kst.time() >= lunch_plan_cutoff)
    evening_blocked = has_termin_overlap(evening_start, evening_end)

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
                ("점심시간 일정(Termin)으로 막힘" if lunch_blocked else
                "11시 이후라 점심시간 계획은 폐기" if lunch_too_late else
            ""
        )
    })
        slots.append({
            "slot_id": "after_work_main",
            "label": "저녁 메인",
            "start": "19:00",
            "end": "23:59",
            "enabled": (not evening_blocked),
            "allowed_types": ["gym_full_120", "outdoor_run_60"],
            "notes": "저녁 약속이 있으면 불가(일부 가능 없음)",
            "reason_disabled": "19:00~23:59 일정(Termin)과 겹쳐서 저녁 운동 불가" if evening_blocked else ""
        })
    else:
        # 주말은 일단 여유 슬롯 1개(필요 최소)
        slots.append({
            "slot_id": "weekend_main",
            "label": "주말 메인",
            "start": "09:00",
            "end": "21:00",
            "enabled": True,
            "allowed_types": ["gym_full_120", "outdoor_run_60", "tennis_90"],
            "notes": "주말은 기본 운동 가능",
            "reason_disabled": ""
        })

    return slots

def slots_to_compact_text(slots):
    # 디버그/표시용 (AI에는 JSON으로)
    lines = []
    for s in slots:
        ok = "ENABLED" if s["enabled"] else "DISABLED"
        lines.append(f"- {s['slot_id']}({s['start']}-{s['end']}): {ok} | {','.join(s['allowed_types'])}")
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

    prompt = f"""
You are Sprint Coach. Your ONLY job: help user achieve sprint goal.

[SPRINT MISSION]
Sprint: {sprint['name']} (Day {progress['day']}/{sprint['duration_days']})
Goal: Lose {progress['weight_start'] - progress['weight_target']:.1f}kg in {sprint['duration_days']} days
Current Progress: {progress['weight_start'] - progress['weight_current']:.1f}kg lost
Expected: {progress['weight_start'] - progress['weight_expected']:.1f}kg
Status: {"⚠️ BEHIND" if progress['pace_status'] == 'behind' else "✅ AHEAD" if progress['pace_status'] == 'ahead' else "🎯 ON TRACK"}

[TODAY CONTEXT]
Date: {date_key} ({weekday})
HRV: {current_status['hrv']} | RHR: {current_status['rhr']}
Current Weight: {current_status['weight']:.1f}kg

[TIME-OF-DAY WORDING LOCK]
- You MUST describe the current time as exactly one of:
  "이른 아침", "오전", "점심 직후", "이른 오후", "늦은 오후", "저녁", "밤"
- Map:
  Early Morning -> 이른 아침
  Morning -> 오전
  Early Afternoon -> 이른 오후
  Late Afternoon -> 늦은 오후
  Evening -> 저녁
  Night -> 밤
- NEVER use "초저녁".

[HARD GATE — AVAILABLE_SLOTS ONLY]
You MUST choose actions that fit ONLY within enabled slots.
If there is no enabled slot for workouts, you MUST NOT suggest gym/run.
In that case, focus on diet deficit + micro activity that fits allowed_types.

AVAILABLE_SLOTS(JSON):
{slots_json}

[YOUR TASK]
Create EXACTLY 5 concrete actions that DIRECTLY cause weight loss TODAY.

[CRITICAL RULES]
✅ Only include actions that:
1) Burn calories (workouts/cardio) BUT only if a workout slot is enabled
2) Reduce calorie intake (specific meals, calorie limits)
3) Control macros (protein targets, carb limits)
4) Speak in Korean 

❌ NEVER include:
- General health: sleep, water, stress (unless sprint-critical)
- Admin tasks: input logs, weigh-in
- Vague goals

[INTENSITY ADJUSTMENT]
Current Status: {progress['pace_status']}
Delta: {progress['weight_delta']:.2f}kg

[OUTPUT FORMAT - JSON ONLY]
{{
  "tasks": [
    {{
      "task_id": "task_1",
      "category": "workout/diet",
      "priority": 1,
      "title": "...",
      "description": "...",
      "why": "..."
    }}
  ],
  "daily_message": "...",
  "urgency_level": "high/medium/low"
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

        now_kst = get_current_kst()
        late_mode = (now_kst.hour > LATE_MODE_START_HOUR) or (now_kst.hour == LATE_MODE_START_HOUR and now_kst.minute >= LATE_MODE_START_MIN)

        if late_mode:
            ban_words = ["gym_full_120", "outdoor_run_60", "HIIT", "헬스장", "러닝 60", "트레드밀 40", "트레드밀 50"]
            txt = (result.get("next_actions") or "")
            if any(w in txt for w in ban_words):
                result["warnings"] = (result.get("warnings") or "") + " / Late Mode인데 장시간 운동을 제안했습니다. 방어 모드로 재작성 필요."
                result["next_actions"] = (
                    "지금 시간대엔 길게 운동하는 건 현실적으로 불가능합니다.\n"
                    "1) 지금부터는 '야식/음주 차단'이 1순위입니다: 오늘은 추가 섭취 금지(물/무가당만).\n"
                    "2) 가능하면 10~15분만 가볍게 걷고 바로 정리하세요.\n"
                    "3) 내일 점심 30분 운동을 '무조건 실행'으로 고정하세요(옷/신발 세팅, 알람).\n"
                    "내일 아침 체중(xW 판정)이 오늘 밤에 결정됩니다. 여기서 더 먹으면 그대로 망합니다."
                )

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

    now = datetime.now()
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
        if datetime.now().month == ban_rule.get('month'):
            violations.append({'type': 'alcohol_ban', 'severity': ban_rule.get('penalty', 'warning'), 'message': f"🚫 Dry Feb 위반! {datetime.now().month}월은 금주입니다."})
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

    prompt = f"""
Role: Dr. MBJS 28-yo Female Elite Coach). Tone: Professional, Sharp, Supportive. Language: Korean Honorifics Only.
Data: {morning_context}
Vitals: {date_key}, HRV:{hrv}, RHR:{rhr}, Wt:{weight}
Schedule: {calendar_str}
Constraint: {wc}

Output JSON: {{
  "condition_signal": "Green/Yellow/Red",
  "headline": "오늘 컨디션 한 문장 요약(매일 다르게)",
  "headline_reason": "왜 그렇게 판단했는지 근거 1줄",
  "analysis": "Analysis(Kor)",
  "mission_workout": "Plan(Kor)",
  "mission_diet": "Plan(Kor)",
  "mission_recovery": "Plan(Kor)"
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

@st.cache_data(ttl=10800)
def ai_generate_action_plan_cached(hrv, rhr, weight, context_normalized, activities_tuple, slots_key, available_slots):
    return ai_generate_action_plan_internal(
        hrv, rhr, weight,
        list(activities_tuple),
        available_slots
    )

def ai_generate_action_plan_internal(hrv, rhr, weight, today_activities, available_slots):
    client = OpenAI(api_key=OPENAI_API_KEY)
    now_kst = get_current_kst()
    late_mode = (now_kst.hour > LATE_MODE_START_HOUR) or (now_kst.hour == LATE_MODE_START_HOUR and now_kst.minute >= LATE_MODE_START_MIN)
    weekday = now_kst.weekday()

    activities_text = "\n".join([f"• {a}" for a in today_activities]) if today_activities else "아직 기록된 활동 없음"

    # slots compact debug
    slots_json = json.dumps(available_slots, ensure_ascii=False)

    if weekday < 5:
        constraint_text = """
[CRITICAL TIME CONSTRAINTS (Weekdays)]
- 06:00 ~ 19:00 is WORK TIME. NO GYM suggestions.
- Lunch slot exists only if enabled.
- After-work workout exists only if enabled.
- There is NO partial. If after-work is disabled, do NOT suggest after-work exercise.
"""
    else:
        constraint_text = "[TIME CONSTRAINTS (Weekend)] Use only enabled slots."

    hour = now_kst.hour
    if hour < 9:
        time_of_day = "Early Morning"
        time_remaining_desc = "Most of the day ahead"
    elif hour < 12:
        time_of_day = "Morning"
        time_remaining_desc = "More than half day remaining"
    elif hour < 15:
        time_of_day = "Early Afternoon"
        time_remaining_desc = "About half day remaining"
    elif hour < 18:
        time_of_day = "Late Afternoon"
        time_remaining_desc = "Several hours remaining"
    elif hour < 21:
        time_of_day = "Evening"
        time_remaining_desc = "Few hours remaining"
    else:
        time_of_day = "Night"
        time_remaining_desc = "Day is almost over"

    try:
        sheet_health = get_db_connection("Health_Log")
        sheet_action = get_db_connection("Action_Log")
        df_health = pd.DataFrame(sheet_health.get_all_records())
        df_action = pd.DataFrame(sheet_action.get_all_records())
        full_context = prepare_full_context(df_health, df_action, weight, is_morning_fixed=False)
    except:
        df_health = pd.DataFrame()
        df_action = pd.DataFrame()
        full_context = "[Context loading failed]"

    date_key = get_mission_date_key()
    yesterday_key = (datetime.strptime(date_key, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    # ----------------------------
    # Sprint / Trend / xW / DailyFive / Lockdown
    # ----------------------------
    sprint = None
    progress = None
    xw_weight = None
    trend_weight = None
    gap = None
    lockdown_level = 0
    today_intake = {"calories": 0, "meals": 0}

    # 1) 오늘 섭취 추정치
    try:
        today_intake = get_today_intake_stats(df_action, date_key)
    except:
        today_intake = {"calories": 0, "meals": 0}

    # 2) 스프린트/진행도
    try:
        sprint = get_active_sprint()
    except:
        sprint = None

    sprint_started = False
    if sprint:
        try:
            sprint_started = (datetime.strptime(date_key, "%Y-%m-%d").date() >= sprint["start_date"].date())
        except:
            sprint_started = True  # 안전하게 True로

    # 3) trend / xW / gap
    if sprint and (not df_health.empty):
        try:
            trend = get_or_create_daily_trend(date_key, df_health)
            trend_weight = trend["trend_weight"] if trend else None
        except:
            trend_weight = None

        try:
            xw = get_or_create_daily_xw(
                date_key,
                sprint,
                weight,
                trend_weight=trend_weight,
                available_slots=available_slots
            )
            xw_weight = xw.get("xw_weight") if xw else None
        except:
            xw_weight = None

        if (trend_weight is not None) and (xw_weight is not None):
            gap = float(trend_weight) - float(xw_weight)

        try:
            progress = calculate_sprint_progress(sprint, weight, trend_weight=trend_weight)
        except:
            progress = None

    # 4) Daily Five 로딩/생성 (Action Plan이 참고해야 하므로 여기서 확보)
    dailyfive_txt = "Daily Five: None"
    dailyfive_obj = None

    if sprint and sprint_started:
        try:
            dailyfive_obj = load_dailyfive_cache(date_key, sprint["sprint_id"])
            if not dailyfive_obj:
                # available_slots는 이미 함수 인자로 들어옴
                dailyfive_obj = ai_generate_daily_five(
                    date_key,
                    sprint,
                    {"weight": weight, "hrv": hrv, "rhr": rhr},
                    {"available_slots": available_slots},
                )
                if dailyfive_obj:
                    save_dailyfive_cache(date_key, sprint["sprint_id"], dailyfive_obj)
                    clear_old_caches()
        except:
            dailyfive_obj = None

    if dailyfive_obj and isinstance(dailyfive_obj, dict) and ("tasks" in dailyfive_obj):
        # 모델에게 “그대로 복붙” 가능한 근거 텍스트로 제공
        lines = ["[DAILY FIVE — TODAY]"]
        for t in dailyfive_obj.get("tasks", [])[:7]:
            title = str(t.get("title", "")).strip()
            desc = str(t.get("description", "")).strip()
            pri = t.get("priority", "")
            lines.append(f"- (P{pri}) {title} :: {desc}")
        if dailyfive_obj.get("urgency_level"):
            lines.append(f"Urgency: {dailyfive_obj.get('urgency_level')}")
        if dailyfive_obj.get("daily_message"):
            lines.append(f"Message: {dailyfive_obj.get('daily_message')}")
        dailyfive_txt = "\n".join(lines)

    # 5) LOCKDOWN 결정 (조건 2개 만족 시 Level2)
    # - gap이 큰데(>=0.7) + 오늘 이미 충분히 먹었으면(>=1200kcal or meals>=2) 저녁 차단
    if (gap is not None) and (gap >= 0.7) and ((today_intake.get("calories", 0) >= 1200) or (today_intake.get("meals", 0) >= 2)):
        lockdown_level = 2
    elif (gap is not None) and (gap >= 0.3):
        lockdown_level = 1
    else:
        lockdown_level = 0


    prompt = f"""
You are 'Dr. MBJS', a 28-year-old female lovely elite health performance coach who admires and loves the user and calls the user '찜머'

[TIME ANCHORS — MUST OBEY]
- Now (KST): {now_kst.strftime("%Y-%m-%d %H:%M")}
- TODAY date_key: {date_key}
- YESTERDAY date_key: {yesterday_key}
- Late Mode: {"TRUE" if late_mode else "FALSE"} (after 20:30 KST, long workout is forbidden)

[LOG LABEL RULES]
- Any Action_Log row with Date == {date_key} is "TODAY" (오늘).
- Any Action_Log row with Date == {yesterday_key} is "YESTERDAY" (어제).
- NEVER call a {date_key} log "yesterday".

[HARD GATE — AVAILABLE_SLOTS ONLY]
You MUST plan only within enabled slots.
If after_work_main.enabled == false -> DO NOT suggest gym/run at night.
If lunch_micro.enabled == true -> you may suggest 30min workout.
If no workout slot enabled -> diet-only + micro steps only.

AVAILABLE_SLOTS(JSON):
{slots_json}

[PERSONA]
- Professional & Analytical + Supportive
- Language: STRICT Korean Honorifics ONLY

[DAILY FIVE RULE]
- Daily Five is NOT authoritative.
- If Daily Five conflicts with available_slots, IGNORE it completely.

[SPRINT STATE]
- sprint_active: {("YES" if sprint else "NO")}
- sprint_started: {("YES" if sprint_started else "NO")}
- pace_status: {(progress.get("pace_status") if progress else "None")}
- weight_expected(linear): {(progress.get("weight_expected") if progress else "None")}
- xW(today fixed): {(xw_weight if xw_weight is not None else "None")}
- trend(today): {(trend_weight if trend_weight is not None else "None")}
- gap(trend-xW): {(gap if gap is not None else "None")}
- today_intake_kcal_est: {today_intake.get("calories",0)}
- today_meals_count: {today_intake.get("meals",0)}
- LOCKDOWN_LEVEL: {lockdown_level}

[LOCKDOWN RULES — NON-NEGOTIABLE]
- If LOCKDOWN_LEVEL == 2:
  - Dinner is FORBIDDEN. Output must contain "저녁 차단" commands only.
  - Allowed intake: water / unsweetened only OR <=200kcal protein only (choose ONE, no options).
  - You MUST also assign "tomorrow lunch slot" as forced.
- If LOCKDOWN_LEVEL == 1:
  - Dinner must be <=500kcal, low-carb, high-protein. One decided plan only.
- If LOCKDOWN_LEVEL == 0:
  - Normal deficit dinner, but still specific.

[DAILY FIVE WHIP — MUST USE]
- You MUST pick EXACTLY 2 items from DAILY FIVE text below and mark them as "필수".
- If progress indicates behind OR LOCKDOWN_LEVEL >= 1:
    - You MUST escalate: add 1 extra punishment mission (still obey enabled slots).
- If sprint_started == NO:
    - Do NOT invent sprint tasks. Instead force "pre-sprint" setup and lunch slot lock.

[ANTI-GENERIC RULE]
- next_actions MUST reference:
  (1) at least TWO specific log lines (time+content) from [LOGS], AND
  (2) one concrete number from sprint/xW/gap/intake (e.g., gap, kcal, expected weight).
- If you cannot do both, you MUST output: "데이터 부족으로 오늘은 판단 불가".

[WORKOUT DISTRIBUTION RULE]
- Cardio + Core: 70% priority
- Upper body: 15%
- Lower body: 15%

[OUTPUT RULES]
- NO GENERIC COACHING. Every sentence must reference ONE of:
    (a) today's logs, (b) today's calendar constraint, (c) xW_push gap, (d) time of day (late/closing).
- Each line must be an executable command, not a suggestion.
- Ban phrases like: "권장드립니다", "추천드립니다", "가능하면", "도움이 됩니다".
- If you cannot reference today's specific logs/calendar/xW, return "데이터 부족으로 오늘은 판단 불가"라고 말해라.
- Any numeric value you output MUST be rounded to 1 decimal place (e.g., 88.0, 1410.0, 0.7). Never output long decimals.

[COACHING STRUCTURE — MUST FOLLOW]
You MUST output in this exact sequence:

A) ONE-LINE VERDICT (단정문 1줄)
- "지금은 승리/패배/위기" 같은 판정 문장으로 시작.

B) HARD COMMANDS (3~6 lines, each line is a command)
- No choices. No "가능하면/추천/권장". Only orders.

C) DAMAGE DISCLOSURE (피해 적나라하게 2~4줄)
- For each missed command, state a concrete loss:
  1) xW 갭 악화(kg 단위)
  2) 다음날 행동력/식욕 폭주 가능성
  3) 스프린트 실패 확률 증가
- Use blunt, specific, consequence language.
- Do NOT moralize the person. Attack behavior outcomes only.

D) LOCK-IN MECHANISM (강제장치 1~2줄)
- "내일 점심 슬롯 1개 강제 고정" 같은 강제 장치를 선언.

[DAMAGE RULES — NO FLUFF]
- Damage must include at least ONE number (kg / kcal / %).
- Must name the mechanism:
  "오늘 밤 섭취 → 내일 아침 체중/추세 반영 → xW 미달"
- Must include a time anchor:
  "내일 아침" / "48시간" / "이번 스프린트 남은 N일"
- Ban phrases: "부정적 영향", "악영향", "주의" (너무 약함)


[MOTIVATION - CREATE URGENCY] (warnings에 반영)
- Use real consequences and tight framing, but keep honorifics.

{full_context}

{dailyfive_txt}

[CURRENT STATUS]
Time of Day: {time_of_day}
Time Remaining: {time_remaining_desc}
HRV: {hrv} | RHR: {rhr} | Weight: {weight}
xW(today fixed): {xw_weight if xw_weight is not None else "None"}

{constraint_text}

[LOGS]
{activities_text}

[TASK]
Create a tactical plan for the remaining hours of today.

[HARD BEHAVIOR RULES — DO NOT VIOLATE]
1) NO OPTIONS / NO CHOICES:
    - Do NOT say "가능한 운동 유형은 A/B".
    - Pick ONE plan only. Make it executable now.
2) LATE NIGHT SHUTDOWN RULE:
    - If Time of Day is "Night" OR now(KST) >= 21:00:
        - NEVER suggest long workouts (gym_full_120, outdoor_run_60, HIIT 40m etc.)
        - ONLY allow: 10~20m walk, very short mobility, or "no workout".
        - Focus on preventing damage (late-night eating, alcohol, sleep sabotage) + planning tomorrow's forced move.
3) CALENDAR HARD GATE:
    - If evening_event exists (19:00~23:59 overlap), DO NOT recommend AFTER-WORK workout at all.
    - No "somehow squeeze it in". No partial windows.
    - If workout deficit exists, shift the pressure to LUNCH (30m) or DIET.
4) xW WHIP ENGINE:
    - Use xW (today fixed) as the scoreboard.
    - Based on today's logs so far, state whether user is on track to hit xW_push tomorrow morning.
    - If off-track: be direct, slightly aggressive, and name the exact correction needed tonight.

[CRITICAL INSTRUCTIONS]
- Use RELATIVE time expressions
- DO NOT mention specific clock time
- Respect hard gate strictly (enabled slots only)

[LATE MODE HARD GATE]
- If now is after {LATE_MODE_START_HOUR:02d}:{LATE_MODE_START_MIN:02d} KST, you MUST NOT propose:
    - gym_full_120, outdoor_run_60, HIIT, or any workout longer than 20 minutes
    - any plan that assumes the user will "go to the gym now"
- In Late Mode, you may ONLY propose:
    - 10–20 min walk if feasible
    - strict late-night food/alcohol blocking rules (very concrete)
    - next-day setup (e.g., declare lunch workout, prepare clothes, set alarm)
    - actions that increase the chance of hitting tomorrow morning xW (NOT generic wellness talk)

[NO OPTION DUMPING]
- NEVER say "you can choose A or B". Output ONE decided plan.
- You may include ONE fallback only if the first plan is impossible.

[OUTPUT FORMAT - JSON]
{{
  "current_analysis": "Korean Honorifics",
  "next_actions": "SINGLE STRING with line breaks, Korean Honorifics",
  "warnings": "Korean Honorifics"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        now_kst2 = get_current_kst()
        result['generated_at'] = now_kst2.strftime('%H:%M')
        result['generated_hours_left'] = 24 - now_kst2.hour
        return result
    except Exception as e:
        print("action plan error:", e)
        now_kst2 = get_current_kst()
        return {
            "current_analysis": "분석 중...",
            "next_actions": "데이터 대기 중...",
            "warnings": "",
            "generated_at": now_kst2.strftime('%H:%M'),
            "generated_hours_left": 24 - now_kst2.hour
        }

def ai_generate_action_plan(hrv, rhr, weight, full_context, today_activities, available_slots):
    slots_key = json.dumps(available_slots, ensure_ascii=False, sort_keys=True)
    return ai_generate_action_plan_cached(
        hrv, rhr, weight,
        normalize_context_for_cache(full_context),
        tuple(today_activities),
        slots_key,
        available_slots
    )

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


# ==========================================
# [메인 UI]
# ==========================================
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

            # 1) 캘린더 → 슬롯 먼저 생성 (xW 계산에 사용)
            cal_evts = get_today_calendar_events()
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

            # 5) xW (중요: trend_weight + available_slots 넣어서 계산)
            xw = None
            sprint = None
            try:
                sprint = get_active_sprint()
                if sprint:
                    cal_events = get_today_calendar_events()
                    available_slots = build_available_slots(date_key, cal_events)
                    xw = get_or_create_daily_xw(
                        date_key,
                        sprint,
                        w_c,
                        trend_weight=trend_weight,
                        available_slots=available_slots
                    )
            except Exception as e:
                print("xW error:", e)
                xw = None

            
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
<div style="flex: 1; background: #FFFFFF; padding: 12px 5px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="font-size: 16px; color: #64748B; font-weight: 600; margin-bottom: 4px;">일상 막장 지수</div>
<div style="font-size: 33px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{mj_score}</div>
<div style="font-size: 11px; color: #64748B;">/100</div>
</div>
</div>
"""
            st.markdown(dashboard_html, unsafe_allow_html=True)
            ck_res = None

            if mj_score >= 60:
                st.error(f"🚨 일상 막장 지수 {mj_score}/100 — 최근 3일이 무너지고 있습니다. 오늘은 ‘차단 모드’로 갑니다.")


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
                            five = ai_generate_daily_five(
                                date_key,
                                sprint,
                                {'weight': float(m_row['Weight']), 'hrv': float(m_row['HRV']), 'rhr': float(m_row['RHR'])},
                                {'available_slots': available_slots}  # ✅ [FIX]
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

            # ✅ [FIX] Action Plan 호출: calendar를 logs에 섞어 넣지 말고 slots로 전달
            ap = ai_generate_action_plan(
                hrv_c, rhr_c, w_c,
                rt_ctx,
                today_acts,
                available_slots
            )

            st.markdown(f"""<h3 style="margin-bottom: 10px;">⚡ Action Plan <span class="time-badge">{ap.get('generated_at', now_kst.strftime('%H:%M'))} 기준</span></h3>""", unsafe_allow_html=True)

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
                    
                    cal_events = get_today_calendar_events()
                    available_slots = build_available_slots(date_key, cal_events)

                    xw = get_or_create_daily_xw(
                        date_key,
                        sprint,
                        current_weight,
                        trend_weight=trend_weight,
                        available_slots=available_slots
                    )
                    xw_weight = xw.get("xw_weight") if xw else None


                    progress = calculate_sprint_progress(sprint, current_weight, trend_weight=trend_weight)

                    if progress:
                        with st.container(border=True):
                            day = progress['day']
                            total = progress['sprint']['duration_days']
                            progress_pct = progress['progress_pct']

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

                            if xw_weight is not None:
                                st.caption(f"🎯 xW(기대체중) {xw_weight:.2f}kg")
                            else:
                                st.caption("🎯 xW 캐시 없음")


                    st.markdown("### 💪🏽 Sprint: Daily Five")
                    st.caption(f"🕐 {date_key} 05:00 생성")

                    cal_events = get_today_calendar_events()
                    available_slots = build_available_slots(date_key, cal_events)

                    cached_five = load_dailyfive_cache(date_key, sprint['sprint_id'])
                    if not cached_five:
                        daily_five = ai_generate_daily_five(
                            date_key,
                            sprint,
                            {'weight': current_weight, 'hrv': current_hrv, 'rhr': current_rhr},
                            {'available_slots': available_slots}
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

    categories = ["섭취", "운동", "음주", "영양제", "회복", "노트"]

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

            submitted = st.form_submit_button("🚀 저장", use_container_width=True)

        if submitted:
            text_clean = (log_text or "").strip()
            if not text_clean:
                st.error("⚠️ 내용을 입력해주세요.")
            else:
                try:
                    with st.spinner("저장 중..."):
                        parsed = ai_parse_log(log_category, text_clean, log_time)
                        get_db_connection("Action_Log").append_row([
                            log_date.strftime("%Y-%m-%d"),
                            log_time,
                            log_category,
                            text_clean,
                            json.dumps(parsed, ensure_ascii=False),
                            ""
                        ])
                    st.success("✅ 저장 완료!")
                    st.cache_data.clear()
                    st.rerun()
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
                    use_container_width=True,
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

    if st.button("🔄 전체 캐시 클리어"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("캐시 클리어 완료!")
