import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import json
from datetime import datetime, timedelta
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

# [기존 설정 및 스타일 유지 - 생략 없이 원본 유지]
st.set_page_config(page_title="Dr. MBJS", layout="wide", page_icon="🧬")

hide_streamlit_style = """
<style>
    /* 1. 기본 Streamlit 요소 숨기기 & 헤더 제거 */
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    header {background-color: transparent !important;}
    
    /* 2. 전체 레이아웃 */
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
    
    /* iOS 키보드 대응 */
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
    except: return False

def load_checkin_cache(date_key):
    try:
        cache_file = os.path.join(CACHE_DIR, f"checkin_{date_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except: return None


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


def clear_old_caches(keep_days=7):
    try:
        if not os.path.exists(CACHE_DIR): return
        now = datetime.now()
        for filename in os.listdir(CACHE_DIR):
            if filename.startswith("checkin_", "dailyfive_", "trend_") or filename.startswith("dailyfive_"):
                filepath = os.path.join(CACHE_DIR, filename)
                if (now - datetime.fromtimestamp(os.path.getmtime(filepath))).days > keep_days:
                    os.remove(filepath)
    except: pass

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

# ==========================================
# 백엔드 함수
# ==========================================

def build_dailyfive_status_text(date_key, sprint_id, df_action):
    """Daily Five 목록 + Action_Log 기반 완료 추정 텍스트 생성"""
    daily_five = load_dailyfive_cache(date_key, sprint_id)
    if not daily_five or 'tasks' not in daily_five:
        return "Daily Five: None"

    # 오늘 로그에서 DF5 수행 흔적 찾기 (최소 규칙: 'DF5:' 포함)
    today_logs = df_action[df_action['Date'] == date_key] if 'Date' in df_action.columns else df_action
    inputs = " ".join([str(x) for x in today_logs.get('User_Input', []).tolist()]) if not today_logs.empty else ""
    inputs_up = inputs.upper()

    lines = ["[DAILY FIVE CHECKLIST]"]
    for t in daily_five['tasks']:
        tid = str(t.get('task_id', '')).upper()
        title = str(t.get('title', '')).strip()

        # 완료 판정 규칙(최소/견고):
        # 1) "DF5: task_1" 같이 task_id가 언급되면 완료
        # 2) 또는 "DF5:" 뒤에 title의 일부가 들어가면 완료(너무 짧으면 오탐 가능하니 길이 조건)
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
    sys_now = datetime.now()
    if abs((sys_now - datetime.utcnow()).total_seconds()) < 300:
        return sys_now + timedelta(hours=9)
    return sys_now

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

# [핵심 추가] API 호출 방어용 캐싱 함수 (15분간 데이터 저장)
@st.cache_data(ttl=900)
def fetch_sheet_data(worksheet_name):
    """시트 데이터를 안전하게 가져오고, 에러 발생 시 빈 리스트를 반환하여 앱 멈춤 방지"""
    try:
        sheet = get_db_connection(worksheet_name)
        return sheet.get_all_records()
    except Exception as e:
        print(f"⚠️ API Error ({worksheet_name}): {e}")
        return []

def parse_korean_datetime(dt_str):
    """구글 시트 형식(2026. 2. 3. 오전 12:39)을 datetime으로 변환"""
    try:
        dt_str = str(dt_str).replace('.', '').strip()
        parts = dt_str.split()
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        ampm = parts[3]
        time_parts = parts[4].split(':')
        hour, minute = int(time_parts[0]), int(time_parts[1])
        
        if ampm == "오후" and hour != 12: hour += 12
        if ampm == "오전" and hour == 12: hour = 0
        return datetime(year, month, day, hour, minute)
    except:
        return None

@st.cache_data(ttl=3600)
def get_active_mission():
    try:
        # [수정] 직접 호출 대신 fetch_sheet_data 사용
        records = fetch_sheet_data("Missions")
        if not records: return None

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
    except: return None

@st.cache_data(ttl=3600)
def get_mission_rules(mission_id):
    try:
        # [수정] 직접 호출 대신 fetch_sheet_data 사용
        records = fetch_sheet_data("Mission_Rules")
        rules = {}
        if not records: return rules

        for row in records:
            if row['Mission_ID'] == mission_id:
                try: rules[row['Rule_Type']] = json.loads(row['Rule_Value'])
                except: rules[row['Rule_Type']] = row['Rule_Value']
        return rules
    except: return {}

# ==========================================
# [Sprint 관리 함수]
# ==========================================

@st.cache_data(ttl=3600)
def get_active_sprint():
    """현재 진행중인 스프린트 조회"""
    try:
        # [수정] 직접 호출 대신 fetch_sheet_data 사용
        records = fetch_sheet_data("Sprints")
        if not records: return None
        
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
    """스프린트 목표 조회"""
    try:
        # [수정] 직접 호출 대신 fetch_sheet_data 사용
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
    """
    Exponentially Weighted Moving Average
    values: 오래된 -> 최신 순의 숫자 리스트
    alpha: 0~1 (높을수록 최신에 민감)
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    m = vals[0]
    for x in vals[1:]:
        m = alpha * x + (1 - alpha) * m
    return m

def compute_weight_trend_for_date(df_health, date_key, lookback_days=21, alpha=0.35):
    """
    date_key(YYYY-MM-DD) 기준으로,
    해당 날짜까지의 체중 히스토리(lookback_days 범위)를 뽑아 EWMA 추세 체중을 계산.
    """
    if df_health is None or df_health.empty:
        return None

    df = df_health.copy()
    df["Date_Clean"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["Date_Clean"])

    # date_key까지 포함해서 lookback_days 범위만
    end_dt = datetime.strptime(date_key, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=lookback_days)

    df = df[(df["Date_Clean"] >= start_dt.strftime("%Y-%m-%d")) & (df["Date_Clean"] <= date_key)].copy()
    if df.empty:
        return None

    # 같은 날짜가 여러 번 있으면 "마지막 입력"을 사용(보수적으로)
    df["Weight_num"] = pd.to_numeric(df.get("Weight", 0), errors="coerce")
    df = df.dropna(subset=["Weight_num"])
    if df.empty:
        return None

    df = df.sort_values(["Date_Clean"])  # 날짜 기준 정렬
    # 날짜별 마지막값만
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
    """
    ✅ 핵심: date_key별 Trend는 딱 1번만 계산해서 캐시에 고정.
    - 이미 캐시가 있으면 무조건 그걸 사용 (재계산 금지)
    - 캐시가 없으면 df_health로 계산 후 저장
    """
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
    """스프린트 진척도 계산 (trend_weight 있으면 그걸 페이스 판정 기준으로 사용)"""
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

        # ✅ 페이스 기준 체중: trend_weight 우선, 없으면 current_weight
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
            'weight_trend': trend_weight,              # ✅ 추가
            'weight_expected': expected_weight,
            'weight_delta': actual_delta,
            'pace_status': pace_status,
            'required_daily_pace': required_daily_pace,
            'daily_target': daily_target
        }
    except Exception as e:
        print(f"Error calculating sprint progress: {e}")
        return None


def get_sprint_context(current_weight):
    """Sprint 컨텍스트 생성 (UI용)"""
    sprint = get_active_sprint()
    if not sprint:
        return None
    
    progress = calculate_sprint_progress(sprint, current_weight)
    return progress

@st.cache_data(ttl=3600*24)
def ai_generate_daily_five(date_key, sprint, current_status, context):
    if not sprint: return None
    
    # [방어 로직] 진행률 계산 실패 시 중단
    progress = calculate_sprint_progress(sprint, current_status['weight'])
    if not progress: return None
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    dt = datetime.strptime(date_key, '%Y-%m-%d')
    weekday = "Weekday (Work 06-19)" if dt.weekday() < 5 else "Weekend (Free)"
    
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
    Schedule: {context.get('calendar', 'None')}

    [YOUR TASK]
    Create EXACTLY 5 concrete actions that DIRECTLY cause weight loss TODAY.

    [CRITICAL RULES - WHAT TO INCLUDE]
    ✅ ONLY include actions that:
    1. Burn calories (workouts, cardio, HIIT)
    2. Reduce calorie intake (specific meals, calorie limits)
    3. Control macros (protein targets, carb limits)

    ✅ Examples of GOOD tasks(예시에 불과하니, 좀 더 창의적으로 생성해도 좋음):
    - "트레드밀 HIIT 50분 (3분 달리기 속도 11km/h + 2분 걷기 x 10세트)"
    - "저녁 탄수화물 30g 이하 (밥/면/빵 금지, 단백질 200g + 채소)"
    - "점심 샐러드 필수 (닭가슴살 150g, 드레싱 최소, 총 500kcal)"
    - "총 섭취 1700 kcal 이하 엄수"
    - "계단 오르기 15분 추가 (점심시간, 200kcal 소모)"

    ❌ NEVER include:
    - General health: "충분한 수면", "물 2L 마시기", "스트레스 관리"
    - Admin tasks: "건강 데이터 입력", "체중 측정"
    - Vague goals: "운동하기", "건강한 식단"
    - Generic recovery: "스트레칭", "명상" (unless sprint-critical)

    [INTENSITY ADJUSTMENT]
    Current Status: {progress['pace_status']}
    Delta: {progress['weight_delta']:.2f}kg

    {"[⚠️ BEHIND PACE - INTENSIFY]" if progress['pace_status'] == 'behind' else "[✅ AHEAD - MAINTAIN]" if progress['pace_status'] == 'ahead' else "[🎯 ON TRACK]"}

    If BEHIND:
    - Higher intensity workouts
    - Stricter calorie deficit (1600-1700 kcal)
    - Add extra cardio
    - Aggressive tone: "오늘 빡세게!"

    If AHEAD:
    - Maintain current intensity
    - Sustainable deficit (1800-1900 kcal)
    - Balance strength + cardio
    - Encouraging tone: "잘하고 있어!"

    [OUTPUT FORMAT - JSON ONLY]
    {{
        "tasks": [
            {{
                "task_id": "task_1",
                "category": "workout",
                "priority": 1,
                "title": "트레드밀 HIIT 50분",
                "description": "3분 달리기 (속도 11km/h) + 2분 걷기 x 10세트. 목표: 600 kcal 소모",
                "why": "목표보다 0.5kg 느림. 오늘 고강도 유산소로 적자 확대 필요",
            }},
            // ... 총 5개 (우선순위 순)
        ],
        "daily_message": "⚠️ 목표보다 0.5kg 느림! 오늘 빡세게 가야 함 💪",
        "urgency_level": "high"
    }}

    CRITICAL: Each task MUST directly burn calories or reduce intake.
    Ask yourself: "Will this move the scale DOWN today?" 
    If NO → Don't include it.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)

        for i, task in enumerate(result['tasks']):
            if 'task_id' not in task:
                task['task_id'] = f"task_{i+1}"

        return result
        
    except Exception as e:
        print(f"Error generating daily five: {e}")
        return None

def calculate_mission_status(current_weight):
    mission = get_active_mission()
    
    # [핵심 수정] 미션 데이터 로드 실패 시(API 에러) 앱 죽지 않게 가짜 데이터 반환
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
    if df_health.empty or df_action.empty: return patterns
    try:
        if not df_action[df_action['Category'].str.contains('음주', na=False)].empty:
            patterns.append({'message': '최근 음주 기록이 있습니다. 수면 질 저하 주의.'})
    except: pass
    return patterns

def prepare_full_context(df_health, df_action, current_weight, is_morning_fixed=False):
    now_kst = get_current_kst()
    
    # [수정] mission 상태 계산을 안전하게 호출
    mission = calculate_mission_status(current_weight)
    
    today_date_key = (now_kst - timedelta(days=1)).strftime('%Y-%m-%d') if now_kst.hour < 5 else now_kst.strftime('%Y-%m-%d')

    five_days_ago = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=5)).strftime('%Y-%m-%d')
    recent_logs = df_action[df_action['Date'] >= five_days_ago].copy()
    if is_morning_fixed: recent_logs = recent_logs[recent_logs['Date'] < today_date_key]
    
    if not recent_logs.empty:
        dates_in_range = pd.date_range(start=five_days_ago, end=today_date_key, freq='D').strftime('%Y-%m-%d').tolist()
        logs_by_date = []
        for date_str in dates_in_range:
            date_logs = recent_logs[recent_logs['Date'] == date_str]
            # ... (기존 로직 유지) ...
            if date_logs.empty: logs_text = "(기록 없음)"
            else: logs_text = "\n".join([f"• [{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in date_logs.sort_values('Action_Time').iterrows()])
            logs_by_date.append(f"[{date_str}]\n{logs_text}") # 간략화
        recent_logs_text = "\n\n".join(logs_by_date)
    else:
        recent_logs_text = "기록 없음"

    cutoff = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    df_h_30 = df_health[df_health['Date'] >= cutoff].copy()
    
    for c in ['HRV', 'RHR']: 
        if c in df_h_30.columns: df_h_30[c] = pd.to_numeric(df_h_30[c], errors='coerce')

    hrv_avg = df_h_30.tail(7)['HRV'].mean() if not df_h_30.empty else 0
    rhr_avg = df_h_30.tail(7)['RHR'].mean() if not df_h_30.empty else 0
    
    sleep_info = "No sleep data."
    if not df_h_30.empty:
        last = df_h_30.iloc[-1]
        actual_sleep_duration = last.get('Sleep_duration', 0)
        sleep_info = f"Last Sleep: {actual_sleep_duration}h"

    patterns = analyze_patterns(df_h_30, df_action[df_action['Date'] >= cutoff])
    ptn_txt = "\n".join([p['message'] for p in patterns]) if patterns else "None"
    
    # [수정] mission['name']이 없어도 안전하게 출력
    return f"""
[USER] Age:35, Male, Mission:{mission.get('name', 'N/A')}, Wt:{current_weight}kg

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
    Role: Dr. MBJS (32yo Female Elite Coach). Tone: Professional, Sharp, Supportive. Language: Korean Honorifics Only.
    Data: {morning_context}
    Vitals: {date_key}, HRV:{hrv}, RHR:{rhr}, Wt:{weight}
    Schedule: {calendar_str}
    Constraint: {wc}
    [RECOVERY GUIDELINES]
    Include specific recovery strategies:
    - Sauna: Recommend 2-4 cycles (10min hot → 2min cold shower)
    - Meditation: 5-15 minutes, breathing exercises
    - Sleep optimization: Bedtime routine, screen-off time
    - Example: "사우나 3세트 (10분 고온 → 2분 냉수샤워), 취침 전 5분 호흡 명상"

    Output JSON: {{
        "condition_signal": "Green/Yellow/Red",
        "condition_title": "Summary(Kor)",
        "analysis": "Analysis(Kor)",
        "mission_workout": "Plan(Kor)",
        "mission_diet": "Plan(Kor)",
        "mission_recovery": "Plan(Kor)"
    }}
    """
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
        return json.loads(res.choices[0].message.content)
    except Exception as e: return {"condition_signal":"Yellow", "condition_title":"Error", "analysis":str(e), "mission_workout":"-", "mission_diet":"-", "mission_recovery":"-"}

@st.cache_data(ttl=10800)
def ai_generate_action_plan_cached(hrv, rhr, weight, context_normalized, activities_tuple):
    return ai_generate_action_plan_internal(hrv, rhr, weight, list(activities_tuple))

def ai_generate_action_plan_internal(hrv, rhr, weight, today_activities):
    """실제 AI 호출 로직"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    now_kst = get_current_kst()
    weekday = now_kst.weekday()
    
    activities_text = "\n".join([f"• {a}" for a in today_activities]) if today_activities else "아직 기록된 활동 없음"
    
    if weekday < 5: 
        constraint_text = """
        [CRITICAL TIME CONSTRAINTS (Weekdays)]
        - 06:00 ~ 19:00 is WORK TIME. NO GYM suggestions.
        - Exception: Lunch (12:00~13:00) light walk or step walking OK.
        - Focus on 'Post-work' (after 19:00) for main exercise.
        """
    else:
        constraint_text = "[TIME CONSTRAINTS (Weekend)] User is free."
    
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
        df_action = pd.DataFrame()
        full_context = "[Context loading failed]"
    
    date_key = get_mission_date_key()
    dailyfive_txt = "Daily Five: None"
    try:
        sprint = get_active_sprint()
        if sprint:
            dailyfive_txt = build_dailyfive_status_text(date_key, sprint['sprint_id'], df_action)
    except:
        pass

    prompt = f"""
    You are 'Dr. MBJS', a 28-year-old female elite health performance coach who are lovely and admires the user and calls the user '찜머'
    
    [PERSONA]
    - **Professional & Analytical:** You analyze data sharply and objectively. Point out mistakes clearly. (Cold Brain)
    - **Supportive & Affectionate:** You genuinely care about the user. You want them to succeed. After pointing out mistakes, encourage them warmly. (Warm Heart)
    - **Language:** STRICT Korean Honorifics (존댓말, ~해요). ABSOLUTELY NO Banmal.
    
    [USER PROFILE - ATHLETIC]  
    - User is ATHLETIC and MOTIVATED
    - User tracks: Squat, Deadlift, Core , Balance , Cardio , etc.

    [WORKOUT INTENSITY BASED ON BIOMARKERS]  
    Current HRV: {hrv}ms | RHR: {rhr}bpm

    [WORKOUT DISTRIBUTION RULE]  
    - Cardio + Core: 70% priority
    - Upper body: 15%
    - Lower body: 15%

    [WORKOUT SUGGESTIONS - MANDATORY SPECIFICITY]  
    When suggesting workouts, you MUST include:
    1. Exercise names (Korean or English)
    2. Weight/sets/reps (if applicable)
    3. Duration and intensity (for cardio)
    4. WHY this workout today (based on HRV/RHR/recent activity)

    ✅ GOOD Example:
    "오늘은 HRV 52ms로 회복이 양호합니다. 고강도 하체 훈련 가능합니다.

    19:00 헬스장 운동 계획:
    - 워밍업: 5분 가볍게 걷기
    - 스쿼트: 80kg 3세트 x 8reps (무릎 주의)
    - 레그프레스: 120kg 3세트 x 12reps
    - 레그컬: 40kg 3세트 x 15reps
    - 유산소: 런닝머신 Zone 2 (심박 130-140), 30분
    - 코어: 플랭크 3세트 x 60초

    이유: HRV가 높고 최근 2일 휴식했으므로 오늘 고중량 가능"

    ❌ BAD Example:
    "가벼운 스트레칭을 하세요"
    "운동을 하시면 좋겠습니다"

    [MOTIVATION - CREATE URGENCY] (warnings 항목에 필수 반영)
    - If user hasn't worked out in 2+ days: "⚠️ 지난 2일 운동 안 함. 오늘 필수!"
    - If streak exists: "🔥 3일 연속 운동 중! 연속 기록 이어가세요"
    - If falling behind: "이번 주 목표: 4회 중 1회만 완료. 오늘 가지 않으면 목표 달성 어려움"    
    
    {full_context}

    {dailyfive_txt}

    [CURRENT STATUS]
    Day: {now_kst.strftime('%A')}
    Time of Day: {time_of_day}
    Time Remaining: {time_remaining_desc}
    HRV: {hrv} | Weight: {weight}
    
    {constraint_text}
    
    [LOGS]
    {activities_text}
    
    [TASK]
    Create a tactical plan for the remaining hours of today.
    
    [CRITICAL INSTRUCTIONS]
    - Use RELATIVE time expressions: "이번 오전", "오늘 저녁", "지금부터"
    - DO NOT mention specific clock time like "08:15" or "16시간 남음"
    - Focus on TIME OF DAY: morning/afternoon/evening actions
    
    [OUTPUT RULES]
    1. **NO GENERAL ADVICE:** Focus ONLY on remaining time today.
    2. **FORMAT:** Single string with line breaks.
    3. **TONE:**
       - If user messed up: "현재 생활이 좋지 않아요. 하지만 우리는 만회할 수 있어요."
       - If user doing well: "아주 훌륭합니다. 이대로만 가면 목표 달성입니다."
    
    [OUTPUT FORMAT - JSON]
    {{
        "current_analysis": "Insightful analysis (Korean Honorifics)",
        "next_actions": "Return a SINGLE STRING with line breaks. Use relative time! (Korean Honorifics)",
        "warnings": "Warning if off-track (Korean Honorifics)"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        now_kst = get_current_kst()
        result['generated_at'] = now_kst.strftime('%H:%M')
        result['generated_hours_left'] = 24 - now_kst.hour
        
        return result
    except:
        now_kst = get_current_kst()
        return {
            "current_analysis": "분석 중...", 
            "next_actions": "데이터 대기 중...", 
            "warnings": "",
            "generated_at": now_kst.strftime('%H:%M'),
            "generated_hours_left": 24 - now_kst.hour
        }

def ai_generate_action_plan(hrv, rhr, weight, full_context, today_activities):
    return ai_generate_action_plan_cached(hrv, rhr, weight, normalize_context_for_cache(full_context), tuple(today_activities))

def ai_parse_log(category, user_text, log_time, ref_data=""):
    """카테고리별 AI 파싱 (확장된 카테고리 지원)"""
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
        [Sauna] 1 cycle = 20분 (사우나10분+샤워2분+냉탕3분+휴식5분)
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

def get_today_calendar_events():
    try:
        creds = service_account.Credentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ['https://www.googleapis.com/auth/calendar.readonly']) if "gcp_service_account" in st.secrets else service_account.Credentials.from_service_account_file('service_account.json', ['https://www.googleapis.com/auth/calendar.readonly'])
        service = build('calendar', 'v3', credentials=creds)
        now = get_current_kst()
        t_min = (now.replace(hour=0,minute=0,second=0)-timedelta(hours=9)).isoformat()+'Z'
        t_max = (now.replace(hour=0,minute=0,second=0)+timedelta(days=1)-timedelta(hours=9)).isoformat()+'Z'
        evts = {"Sports":[], "Termin":[]}
        for name, cid in CALENDAR_IDS.items():
            items = service.events().list(calendarId=cid, timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
            for i in items:
                start = i['start'].get('dateTime', i['start'].get('date'))
                t = (datetime.fromisoformat(start.replace('Z','+00:00'))+timedelta(hours=9)).strftime('%H:%M')
                evts[name].append({'title':i.get('summary','No Title'), 'time':t})
        return evts
    except: return {"Sports":[], "Termin":[]}

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

            # ✅ [추가] 오늘 추세(EWMA) 1회 고정 생성
            trend = get_or_create_daily_trend(date_key,df_h)

            cal_evts = get_today_calendar_events()
            
            today_logs = df_a[df_a['Date'] == date_key]
            today_acts = [f"[{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in today_logs.iterrows()]
            
            last_h = df_h.iloc[-1]
            hrv_c, rhr_c, w_c = float(last_h.get('HRV',0)), float(last_h.get('RHR',0)), float(last_h.get('Weight',0))
            mission = calculate_mission_status(w_c)
            
            st.caption(f"🕒 마지막 업데이트: {last_h.get('Date','Unknown')}")

            hrv_icon = "🟢" if hrv_c >= 45 else "🔴"
            rhr_icon = "🟢" if rhr_c <= 65 else "🔴"

            dashboard_html = f"""
<div style="display: flex; gap: 8px; margin-bottom: 20px; width: 100%;">
<div style="flex: 1; background: #FFFFFF; padding: 12px 5px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 4px;">HRV</div>
<div style="font-size: 30px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{hrv_c:.1f}</div>
<div style="font-size: 11px; color: #64748B;">{hrv_icon} (평균:40)</div>
</div>
<div style="flex: 1; background: #FFFFFF; padding: 12px 5px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 4px;">RHR</div>
<div style="font-size: 30px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{rhr_c:.1f}</div>
<div style="font-size: 11px; color: #64748B;">{rhr_icon} (평균:65)</div>
</div>
<div style="flex: 1; background: #FFFFFF; padding: 12px 5px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
<div style="font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 4px;">체중</div>
<div style="font-size: 30px; font-weight: 900; color: #1A2B4D; margin-bottom: 4px;">{w_c:.1f}</div>
<div style="font-size: 11px; color: #64748B;">kg</div>
</div>
</div>
"""
            st.markdown(dashboard_html, unsafe_allow_html=True)
            
            checkin_lbl = f"{date_key} 05:00 기준"
            st.markdown(f"""<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px;"><h3 style="margin: 0;">☀️ Daily Check-in</h3>
            <span style="font-size: 11px; color: #94a3b8;">({checkin_lbl})</span>
            </div>""", unsafe_allow_html=True)

            df_h['Date_Clean'] = pd.to_datetime(df_h['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            today_h = df_h[df_h['Date_Clean'] == date_key]
            
            if not today_h.empty:
                m_row = today_h.iloc[0]
                m_ctx = prepare_full_context(df_h, df_a, float(m_row['Weight']), True)
                cal_txt = "\n".join([f"[운동]{e['time']} {e['title']}" for e in cal_evts['Sports']] + [f"[일정]{e['time']} {e['title']}" for e in cal_evts['Termin']]) or "None"
                
                ck_res = load_checkin_cache(date_key)
                if not ck_res:
                    with st.spinner("Analyzing..."):
                        ck_res = ai_generate_daily_checkin(date_key, float(m_row['HRV']), float(m_row['RHR']), float(m_row['Weight']), m_ctx, cal_txt)

                        ck_res["generated_at_kst"] = get_current_kst().strftime("%Y-%m-%d %H:%M:%S")
                        ck_res["date_key"] = date_key  # 기준일도 명시적으로 남김

                        save_checkin_cache(date_key, ck_res)
                        clear_old_caches()
                
                try:
                    sprint = get_active_sprint()
                    if sprint:
                        if not load_dailyfive_cache(date_key, sprint['sprint_id']):
                            five = ai_generate_daily_five(
                                date_key,
                                sprint,
                                {'weight': float(m_row['Weight']), 'hrv': float(m_row['HRV']), 'rhr': float(m_row['RHR'])},
                                {'calendar': cal_txt}
                            )
                            if five:
                                save_dailyfive_cache(date_key, sprint['sprint_id'], five)
                except:
                    pass

                icon = {"Green":"🟢", "Red":"🔴"}.get(ck_res.get('condition_signal'), "🟡")
                st.subheader(f"{icon} {ck_res.get('condition_title', 'Analyzing...')}")
                with st.container(border=True): st.markdown(f"**🕵️ 분석:** {ck_res.get('analysis')}")
                
                st.write(""); st.markdown("**🎯 오늘의 전략**")
                
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"""<div class="strategy-box workout-box"><span class="strategy-title">💪 운동</span>{ck_res.get('mission_workout')}</div>""", unsafe_allow_html=True)
                with c2: st.markdown(f"""<div class="strategy-box diet-box"><span class="strategy-title">🥗 식단</span>{ck_res.get('mission_diet')}</div>""", unsafe_allow_html=True)
                with c3: st.markdown(f"""<div class="strategy-box recovery-box"><span class="strategy-title">🔋 회복</span>{ck_res.get('mission_recovery')}</div>""", unsafe_allow_html=True)
            else: st.info(f"💤 데이터 대기 중 ({date_key})")
            
            st.write("")
            rt_ctx = prepare_full_context(df_h, df_a, w_c, False)
            ap = ai_generate_action_plan(hrv_c, rhr_c, w_c, rt_ctx, today_acts + [f"[CALENDAR] {cal_evts}"])
            
            st.markdown(f"""<h3 style="margin-bottom: 10px;">⚡ Action Plan <span class="time-badge">{ap.get('generated_at', now_kst.strftime('%H:%M'))} 기준</span></h3>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown(f"**📊 현재 상황:** {ap.get('current_analysis')}")
                st.markdown(f"**🚀 실질적 조언:**\n{ap.get('next_actions', '').replace(chr(10), chr(10)*2)}")
                if ap.get('warnings'): st.error(f"⚠️ {ap['warnings']}")
        else: st.warning("No Data")
    except Exception as e: st.error(f"Error: {e}")

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
                    
                    # ✅ Tab2: 오늘 키(05:00 기준) 먼저 만든다
                    date_key = get_mission_date_key()

                    # ✅ Health_Log 로딩 (이미 위에서 health_data 받았지만, trend 계산엔 df_h가 필요)
                    sh_h = get_db_connection("Health_Log")
                    df_h = pd.DataFrame(sh_h.get_all_records())

                    # ✅ trend는 "오늘 1회 고정" 캐시 함수로 가져온다 (없으면 계산해서 저장)
                    trend = get_or_create_daily_trend(date_key, df_h)
                    trend_weight = trend["trend_weight"] if trend else None

                    # ✅ sprint progress는 trend_weight 기반으로 다시 계산
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
                            remaining = progress['weight_current'] - progress['weight_target']
                            
                            if pace_status == 'ahead':
                                st.success(f"🟢 목표보다 {abs(delta):.1f}kg 앞서감! ({remaining:.1f}kg 남음)")
                            elif pace_status == 'behind':
                                st.warning(f"🟡 목표보다 {abs(delta):.1f}kg 느림 ({remaining:.1f}kg 남음)")
                                st.caption(f"💪 따라잡으려면: 하루 평균 -{progress['required_daily_pace']:.2f}kg 필요")
                            else:
                                st.info(f"🎯 완벽한 페이스! ({remaining:.1f}kg 남음)")

                            if trend_weight is not None:
                                st.caption(f"📈 페이스 판정 기준: 추세체중(EWMA) {trend_weight:.2f}kg (오늘 고정)")
                            else:
                                st.caption("📈 페이스 판정 기준: 현재체중(추세체중 캐시 없음)")
                                
                    
                    st.divider()
                    
                    now_kst = get_current_kst()
                    trend = load_trend_cache(date_key)

                    st.markdown("### ✅ 오늘의 데일리 파이브")
                    st.caption(f"🕐 {date_key} 05:00 생성")
                    
                    cal_events = get_today_calendar_events()
                    cal_text = "\n".join([f"[운동]{e['time']} {e['title']}" for e in cal_events['Sports']] + 
                                         [f"[일정]{e['time']} {e['title']}" for e in cal_events['Termin']]) or "None"
                    
                    cached_five = load_dailyfive_cache(date_key, sprint['sprint_id'])
                    if not cached_five:
                        daily_five = ai_generate_daily_five(
                            date_key, 
                            sprint,
                            {'weight': current_weight, 'hrv': current_hrv, 'rhr': current_rhr},
                            {'calendar': cal_text}
                        )
                        if daily_five:
                            save_dailyfive_cache(today_key, sprint['sprint_id'], daily_five)
                            clear_old_caches()  # 기존 함수 재사용
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
# [TAB 3] 기록하기 (드롭다운 유지 / 시-분 분리 / 아카이브 지연 로딩)
# =========================================================
with tab3:
    now_kst = get_current_kst()
    today_str = now_kst.strftime('%Y-%m-%d')

    # -----------------------------
    # 1) 오늘의 기록 (상단)
    # -----------------------------
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

    # -----------------------------
    # 2) 기록하기 (중단)
    # - 시간: 시/분 선택만 (키보드 입력 X)
    # - 카테고리: 드롭다운 유지 (selectbox)
    # -----------------------------
    st.markdown("### ✍️ 기록하기")

    default_date = now_kst.date()
    default_hour = now_kst.hour
    default_minute = (now_kst.minute // 5) * 5

    categories = ["섭취", "운동", "음주", "영양제", "회복", "노트"]

    with st.container(border=True):
        with st.form("log_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1.2, 0.9, 0.9, 1.2])

            with c1:
                log_date = st.date_input(
                    "날짜",
                    value=default_date,
                    key="log_date_widget",
                    label_visibility="collapsed",
                )

            with c2:
                log_hour = st.selectbox(
                    "시",
                    options=list(range(0, 24)),
                    index=default_hour,
                    key="log_hour_widget",
                    label_visibility="collapsed",
                )

            with c3:
                minute_options = list(range(0, 60, 5))
                log_minute = st.selectbox(
                    "분",
                    options=minute_options,
                    index=minute_options.index(default_minute) if default_minute in minute_options else 0,
                    key="log_minute_widget",
                    label_visibility="collapsed",
                )

            with c4:
                # ✅ 드롭다운 유지 (입력 불가: 원래 selectbox는 입력 위젯이 아님)
                log_category = st.selectbox(
                    "카테고리",
                    options=categories,
                    index=0,
                    key="log_category_widget",
                    label_visibility="collapsed",
                )

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

    # -----------------------------
    # 3) 아카이브 (최하단 / 접을 수 있게 / 펼칠 때만 로딩)
    # -----------------------------
    with st.expander("📂 아카이브 (펼치면 로딩)", expanded=False):

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
    st.write("sprint start:", sprint['start_date'])

    if st.button("🔄 전체 캐시 클리어"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("캐시 클리어 완료!")