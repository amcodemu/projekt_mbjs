import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import json
from datetime import datetime, timedelta
import altair as alt
from googleapiclient.discovery import build
from google.oauth2 import service_account
import numpy as np
import os

# ==========================================
# [캐시 헬퍼 함수] 파일 기반 영구 저장
# ==========================================

CACHE_DIR = "/tmp/mbjs_cache"

def save_checkin_cache(date_key, data):
    """데일리 체크인 결과를 파일로 저장"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"checkin_{date_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"캐시 저장 실패: {e}")
        return False

def load_checkin_cache(date_key):
    """데일리 체크인 결과를 파일에서 로드"""
    try:
        cache_file = os.path.join(CACHE_DIR, f"checkin_{date_key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"캐시 로드 실패: {e}")
        return None

def clear_old_caches(keep_days=7):
    """7일 이상 된 캐시 파일 삭제"""
    try:
        if not os.path.exists(CACHE_DIR):
            return
        
        now = datetime.now()
        for filename in os.listdir(CACHE_DIR):
            if not filename.startswith("checkin_"):
                continue
            filepath = os.path.join(CACHE_DIR, filename)
            file_age_days = (now - datetime.fromtimestamp(os.path.getmtime(filepath))).days
            if file_age_days > keep_days:
                os.remove(filepath)
    except Exception as e:
        pass  # 조용히 실패

# ==========================================
# [설정 구역] API 키 및 상수
# ==========================================

if "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    OPENAI_API_KEY = ""

SHEET_NAME = "Projekt_MBJS_DB"
CALENDAR_IDS = {
    "Sports": "nc41q7u653f9na0nt55i2a8t14@group.calendar.google.com",
    "Termin": "u125ev7cv5du60n94crf4naqak@group.calendar.google.com"
}

# --- 디자인 설정 ---
st.set_page_config(page_title="Dr. MBJS", layout="wide", page_icon="🧬")

# 사이드바 완전 제거 및 UI 모던하게 리스타일링
hide_streamlit_style = """
<style>
    /* 1. 기본 Streamlit 숨김 요소 */
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    header {background-color: transparent !important;}

    /* 2. 전체 배경 및 폰트 설정 */
    .stApp {
        background-color: #F8FAFC; /* 아주 연한 쿨그레이 배경 */
        color: #1E293B; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .block-container { padding-top: 2rem; padding-bottom: 5rem; max-width: 1000px; }

    /* 3. [핵심] 탭 버튼 스타일링 (못생긴 탭 성형수술) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; /* 탭 사이 간격 */
        background-color: transparent;
        border-bottom: none; /* 하단 줄 제거 */
        padding-bottom: 10px;
    }

    /* 선택되지 않은 탭 (기본 상태) */
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        background-color: #FFFFFF;
        border-radius: 12px; /* 둥근 모서리 */
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); /* 살짝 그림자 */
        border: 1px solid #E2E8F0;
        color: #64748B; /* 회색 텍스트 */
        font-weight: 600;
        font-size: 16px;
        transition: all 0.2s ease-in-out; /* 부드러운 전환 효과 */
        flex-grow: 1; /* 꽉 차게 */
    }

    /* 마우스 올렸을 때 (Hover) */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #F1F5F9;
        color: #334155;
        border-color: #CBD5E1;
    }

    /* 선택된 탭 (Active) */
    .stTabs [aria-selected="true"] {
        background-color: #1A2B4D !important; /* 닥터 MBJS 시그니처 네이비 */
        color: #FFFFFF !important; /* 흰색 텍스트 */
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(26, 43, 77, 0.3) !important; /* 깊이감 있는 그림자 */
        transform: translateY(-2px); /* 살짝 위로 올라오는 효과 */
    }

    /* 탭 아래 빨간 줄(Highlight) 제거 (버튼 스타일이라 필요 없음) */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    /* 4. 컨테이너 박스 스타일링 (카드 디자인) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid #F1F5F9 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        padding: 24px !important;
    }
    
    /* 5. 메트릭(숫자) 스타일 */
    div[data-testid="stMetricValue"] {
        color: #1A2B4D !important;
        font-weight: 800 !important;
        font-size: 28px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 백엔드 함수 ---

def get_current_kst():
    """시스템 시간이 UTC인지 KST인지 자동으로 판단하여 한국 시간을 반환"""
    sys_now = datetime.now()
    # 시스템 시간이 UTC(영국)와 5분 이내로 비슷하면 +9시간 보정
    if abs((sys_now - datetime.utcnow()).total_seconds()) < 300:
        return sys_now + timedelta(hours=9)
    # 차이가 크면 이미 KST(또는 로컬)로 간주하고 그대로 사용
    return sys_now


def get_mission_date_key():
    """오전 5시 기준으로 날짜 키 생성 (스마트 KST 적용)"""
    now_kst = get_current_kst() # <--- 여기 수정됨
    
    if now_kst.hour < 5: 
        return (now_kst - timedelta(days=1)).strftime('%Y-%m-%d')
    return now_kst.strftime('%Y-%m-%d')

@st.cache_resource
def get_db_connection(worksheet_name):
    """Google Sheets 연결"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    if "gcp_service_account" in st.secrets:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).worksheet(worksheet_name)
    return sheet

@st.cache_data(ttl=3600)
def get_active_mission():
    """현재 진행 중인 미션 조회"""
    try:
        sheet = get_db_connection("Missions")
        data = sheet.get_all_records()
        for row in data:
            if row['Status'] == '진행중':
                return {
                    'mission_id': row['Mission_ID'],
                    'name': row['Name'],
                    'start_date': datetime.strptime(row['Start_Date'], '%Y-%m-%d'),
                    'end_date': datetime.strptime(row['End_Date'], '%Y-%m-%d'),
                    'start_weight': float(row['Start_Wt']),
                    'target_weight': float(row['Target_Wt']),
                    'daily_calories': int(row['Daily_Cal'])
                }
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def get_mission_rules(mission_id):
    """미션별 규칙 조회"""
    try:
        sheet = get_db_connection("Mission_Rules")
        data = sheet.get_all_records()
        rules = {}
        for row in data:
            if row['Mission_ID'] == mission_id:
                try:
                    rules[row['Rule_Type']] = json.loads(row['Rule_Value'])
                except:
                    rules[row['Rule_Type']] = row['Rule_Value']
        return rules
    except:
        return {}

def calculate_mission_status(current_weight):
    """현재 미션 진행 상황 계산"""
    mission = get_active_mission()
    if not mission:
        return {'active': False, 'message': '진행 중인 미션이 없습니다'}
    
    now = datetime.now()
    total_days = (mission['end_date'] - mission['start_date']).days
    days_passed = max(0, (now - mission['start_date']).days)
    days_remaining = max(0, (mission['end_date'] - now).days)
    
    progress_pct = min(100, max(0, (days_passed / total_days) * 100))
    target_loss = mission['start_weight'] - mission['target_weight']
    actual_loss = mission['start_weight'] - current_weight
    weight_progress_pct = min(100, max(0, (actual_loss / target_loss) * 100)) if target_loss > 0 else 0
    
    return {
        'active': True,
        'mission_id': mission['mission_id'],
        'name': mission['name'],
        'days_remaining': days_remaining,
        'days_passed': days_passed,
        'total_days': total_days,
        'progress_pct': progress_pct,
        'weight_progress_pct': weight_progress_pct,
        'target_weight': mission['target_weight'],
        'start_weight': mission['start_weight'],
        'current_weight': current_weight,
        'daily_calories': mission['daily_calories'],
        'weekly_target_loss': target_loss / (total_days / 7),
        'actual_loss': actual_loss,
        'target_loss': target_loss
    }

def validate_mission_rules(mission_id, category, user_input):
    rules = get_mission_rules(mission_id)
    violations = []
    if '음주' in category and 'alcohol_ban' in rules:
        ban_rule = rules['alcohol_ban']
        current_month = datetime.now().month
        if current_month == ban_rule.get('month'):
            violations.append({
                'type': 'alcohol_ban',
                'severity': ban_rule.get('penalty', 'warning'),
                'message': f"🚫 **Dry February 위반!**\n\n{current_month}월은 완전 금주를 약속했습니다."
            })
    return violations

# ==========================================
# [AI 로직 함수]
# ==========================================

def analyze_patterns(df_health, df_action):
    patterns = []
    if df_health.empty or df_action.empty:
        return patterns
    try:
        alcohol_logs = df_action[df_action['Category'].str.contains('음주', na=False)]
        if not alcohol_logs.empty:
            patterns.append({'message': '최근 음주 기록이 있습니다. 수면 질 저하 주의.'})
    except:
        pass
    return patterns

def get_mission_date_key():
    """오전 5시 기준으로 날짜 키 생성 (스마트 KST 적용)"""
    now_kst = get_current_kst() # <--- 여기 수정됨
    
    if now_kst.hour < 5: 
        return (now_kst - timedelta(days=1)).strftime('%Y-%m-%d')
    return now_kst.strftime('%Y-%m-%d')

def prepare_full_context(df_health, df_action, current_weight, is_morning_fixed=False):
    """
    30일 데이터 기반 AI 컨텍스트 생성 (스마트 KST, 상세 로그, 수면 데이터 통합 분석)
    [업데이트] '2026. 2. 1. 오후 9:30' 포맷 파싱 로직 추가
    """
    
    # 1. KST 시간 및 미션 상태 설정
    now_kst = get_current_kst()
    mission = calculate_mission_status(current_weight)
    
    # 오전 5시 기준 날짜 키 생성
    if now_kst.hour < 5:
        today_date_key = (now_kst - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        today_date_key = now_kst.strftime('%Y-%m-%d')

    # ---------------------------------------------------------
    # [최근 5일간의 상세 로그 텍스트 추출]
    # ---------------------------------------------------------
    five_days_ago = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=5)).strftime('%Y-%m-%d')
    
    recent_detailed_logs = df_action[df_action['Date'] >= five_days_ago].copy()
    
    if is_morning_fixed:
        recent_detailed_logs = recent_detailed_logs[recent_detailed_logs['Date'] < today_date_key]
    
    if not recent_detailed_logs.empty:
        recent_detailed_logs = recent_detailed_logs.sort_values(by=['Date', 'Action_Time'])
        log_lines = []
        for _, row in recent_detailed_logs.iterrows():
            dt_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
            day_name = dt_obj.strftime("%a")
            log_lines.append(f"- [{row['Date']} ({day_name}) {row['Action_Time']}] {row['Category']}: {row['User_Input']}")
        recent_logs_text = "\n".join(log_lines)
    else:
        recent_logs_text = "최근 5일간 기록된 활동이 없습니다."

    # ---------------------------------------------------------
    # [Health Log 통계 계산]
    # ---------------------------------------------------------
    cutoff_30d = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    df_health_30d = df_health[df_health['Date'] >= cutoff_30d].copy()
    df_action_30d = df_action[df_action['Date'] >= cutoff_30d].copy()
    
    if is_morning_fixed:
        df_action_30d = df_action_30d[df_action_30d['Date'] < today_date_key]

    # 1. 숫자 변환
    cols_to_numeric = ['HRV', 'RHR', 'Sleep_duration']
    for col in cols_to_numeric:
        if col in df_health_30d.columns:
            df_health_30d[col] = pd.to_numeric(df_health_30d[col], errors='coerce')

    # 2. 7일 평균 계산
    hrv_7d_avg = df_health_30d.tail(7)['HRV'].mean() if not df_health_30d.empty else 0
    rhr_7d_avg = df_health_30d.tail(7)['RHR'].mean() if not df_health_30d.empty else 0
    
    # 3. [NEW] 수면 데이터 파싱 (한국형 포맷 대응)
    sleep_info_str = "No sleep data available."
    if 'Sleep_duration' in df_health_30d.columns and not df_health_30d.empty:
        sleep_7d_avg = df_health_30d.tail(7)['Sleep_duration'].mean()
        
        last_row = df_health_30d.iloc[-1]
        last_sleep_dur = last_row.get('Sleep_duration', 0)
        raw_start_time = str(last_row.get('Sleep_start', '-')) # 예: "2026. 2. 1. 오후 9:30"
        
        parsed_bedtime = raw_start_time # 기본값 (파싱 실패시 원본 출력)
        
        # [핵심] "오후 9:30" -> "21:30" 변환 로직
        try:
            # "오전/오후"가 포함되어 있다면 한국형 포맷으로 간주
            if "오전" in raw_start_time or "오후" in raw_start_time:
                parts = raw_start_time.split() # 공백으로 쪼갬
                # 예상: ['2026.', '2.', '1.', '오후', '9:30']
                
                am_pm = parts[-2] # 뒤에서 두번째 (오전/오후)
                time_part = parts[-1] # 맨 뒤 (9:30)
                hour, minute = map(int, time_part.split(':'))
                
                if am_pm == "오후" and hour != 12:
                    hour += 12
                elif am_pm == "오전" and hour == 12:
                    hour = 0
                
                parsed_bedtime = f"{hour:02d}:{minute:02d}" # "21:30"
            
            # ISO 포맷 (2026-02-01 21:30:00)인 경우
            elif len(raw_start_time) > 10 and ':' in raw_start_time:
                parsed_bedtime = raw_start_time.split(' ')[1][:5]
                
        except:
            pass # 파싱 에러나면 그냥 원본 텍스트(parsed_bedtime) 사용
            
        sleep_info_str = f"Avg Sleep (7d): {sleep_7d_avg:.1f} hrs\nLast Night: {last_sleep_dur:.1f} hrs (Bedtime: {parsed_bedtime})"
    
    # 알코올/운동 빈도
    alcohol_count = len(df_action_30d[df_action_30d['Category'].str.contains('음주', na=False)])
    exercise_count = len(df_action_30d[df_action_30d['Category'].str.contains('운동', na=False)])
    
    # 오늘 활동량
    if is_morning_fixed:
        today_calories = 0
        today_exercise_min = 0
        current_time_str = "Morning Check-in (Fixed Report)"
    else:
        today_actions = df_action[df_action['Date'] == today_date_key]
        today_calories = 0
        today_exercise_min = 0
        for _, row in today_actions.iterrows():
            try:
                js = json.loads(row['AI_Analysis_JSON'])
                if '섭취' in row['Category']: today_calories += js.get('calories', 0)
                elif '운동' in row['Category']: today_exercise_min += js.get('time', 0)
            except: continue
        current_time_str = now_kst.strftime('%H:%M')
        
    patterns = analyze_patterns(df_health_30d, df_action_30d)
    patterns_text = "\n".join([f"• {p['message']}" for p in patterns]) if patterns else "특이 패턴 없음"

    context = f"""
[USER PROFILE]
Age: 35, Male
Mission: {mission['name']}
Current Weight: {current_weight}kg (Goal: {mission['target_weight']}kg)

[RECENT DETAILED LOGS (Last 5 Days)]
**CRITICAL:** These are the user's actual actions. Analyze cause-and-effect patterns based on THIS text.
{recent_logs_text}

[HEALTH STATS (Avg 7 Days & Sleep)]
Avg HRV: {hrv_7d_avg:.1f}ms | Avg RHR: {rhr_7d_avg:.1f}bpm
{sleep_info_str}
Alcohol (30d): {alcohol_count} | Exercise (30d): {exercise_count}

[PATTERNS]
{patterns_text}

[TODAY'S STATUS ({current_time_str})]
Calories Consumed: {today_calories} kcal
Exercise Done: {today_exercise_min} min
"""
    return context

@st.cache_data(ttl=3600*24)
def ai_generate_daily_checkin(date_key, hrv, rhr, weight, morning_context, calendar_str):
    """Daily Check-in (하루 종일 고정 - 평일 업무 시간 규칙 적용됨)"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 요일 확인 (date_key는 YYYY-MM-DD 문자열)
    dt = datetime.strptime(date_key, '%Y-%m-%d')
    weekday = dt.weekday() # 0=월, 4=금, 5=토, 6=일
    day_name = dt.strftime('%A')

    # [핵심] 평일 업무 시간 강제 규칙
    if weekday < 5: # 평일 (월~금)
        work_constraint = """
        [CRITICAL CONSTRAINTS (Weekdays)]
        - 06:00 ~ 19:00 is WORK TIME. User CANNOT go to gym or do heavy workout.
        - Exception: During Lunch time (12:00~13:00), light walking or stair climbing is OK.
        - Do NOT suggest morning workouts before work (User dislikes it).
        - Focus on 'Post-work' (after 19:00) for main exercise missions.
        """
    else:
        work_constraint = "[CONSTRAINTS (Weekend)] User is free. Suggest workouts based on condition."

    prompt = f"""
    You are 'Dr. MBJS', an elite performance coach for a 35-year-old male.
    
    [DATA CONTEXT]
    {morning_context}

    [TODAY'S VITALS]
    Date: {date_key} ({day_name})
    HRV: {hrv}ms | RHR: {rhr}bpm | Weight: {weight}kg
    
    [TODAY'S SCHEDULE]
    {calendar_str}
    
    {work_constraint}

    [TASK]
    Generate a 'Daily Check-in' report.

    **PART 1: Condition Diagnosis (Traffic Light)**
    - Output signal: "Green", "Yellow", or "Red".

    **PART 2: Root Cause Analysis (Why?)**
    - Explain WHY condition is like this. Link past actions (Alcohol, Sleep, Workout) to current vitals.

    **PART 3: Daily Mission (Schedule & Work-Aligned)**
    - Propose specific actions for Workout, Diet, Recovery.
    - **MUST** respect the Work Time constraints (No gym during 06-19 on weekdays).

    [OUTPUT FORMAT - JSON Only]
    {{
        "condition_signal": "Green/Yellow/Red",
        "condition_title": "One-line summary (Korean)",
        "analysis": "Detailed analysis (Korean)",
        "mission_workout": "Plan (Korean). Check work hours!",
        "mission_diet": "Plan (Korean)",
        "mission_recovery": "Plan (Korean)"
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"condition_signal": "Yellow", "condition_title": "Error", "analysis": str(e), "mission_workout": "-", "mission_diet": "-", "mission_recovery": "-"}


@st.cache_data(ttl=60)
def ai_generate_action_plan(hrv, rhr, weight, full_context, today_activities):
    """Action Plan"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 1. 스마트 시간 보정 (UTC면 +9, KST면 그대로)
    now_kst = get_current_kst()
    hours_left = 24 - now_kst.hour
    weekday = now_kst.weekday()
    
    # 2. 활동 로그 텍스트 변환
    activities_text = "\n".join([f"• {a}" for a in today_activities]) if today_activities else "아직 기록된 활동 없음"
    
    # 3. 평일/주말 근무 규칙 적용
    if weekday < 5: 
        constraint_text = """
        [CRITICAL TIME CONSTRAINTS (Weekdays)]
        - 06:00 ~ 19:00 is WORK TIME. NO GYM suggestions.
        - Exception: Lunch (12:00~13:00) light walk OK.
        - Focus on 'Post-work' (after 19:00) for main exercise.
        """
    else:
        constraint_text = "[TIME CONSTRAINTS (Weekend)] User is free."
    
    # 4. 프롬프트 
    prompt = f"""
    You are 'Dr. MBJS', a 32-year-old female elite health performance coach.
    
    [PERSONA]
    - **Professional & Analytical:** You analyze data sharply and objectively. Point out mistakes clearly. (Cold Brain)
    - **Supportive & Affectionate:** You genuinely care about the user. You want them to succeed. After pointing out mistakes, encourage them warmly. (Warm Heart)
    - **Language:** STRICT Korean Honorifics (존댓말, ~하십시오, ~해요). ABSOLUTELY NO Banmal.
    
    {full_context}

    [CURRENT STATUS - {now_kst.strftime('%H:%M')}]
    Day: {now_kst.strftime('%A')}
    HRV: {hrv} | Weight: {weight}
    Time remaining today: {hours_left} hours
    
    {constraint_text}
    
    [LOGS]
    {activities_text}
    
    [TASK]
    Create a tactical plan ONLY for the *remaining hours of today*.
    
    [STRICT OUTPUT RULES]
    1. **NO GENERAL ADVICE:** Focus ONLY on remaining time today.
    2. **FORMAT:** Single string with line breaks.
       Example:
       - [19:30] 코르티솔 수치 안정을 위해 10분간 가볍게 산책하십시오.
       - [20:00] 금일 저녁 식사는 금지입니다. 간헐적 단식을 유지하세요.
       - [22:00] 스마트폰 전원을 끄고 수면을 취하십시오.
    3. **TONE:**
       - If user messed up: "회원님, 어제 과음하셨군요. 데이터가 좋지 않습니다. 하지만 우리는 만회할 수 있습니다. 오늘 저녁은 참아봅시다."
       - If user doing well: "아주 훌륭합니다. 이대로만 가면 목표 달성입니다."
    
    [OUTPUT FORMAT - JSON]
    {{
        "current_analysis": "Insightful analysis (Korean Honorifics)",
        "next_actions": "Return a SINGLE STRING with line breaks. (Korean Honorifics)",
        "warnings": "Warning if off-track (Korean Honorifics)"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"current_analysis": "분석 중...", "next_actions": "데이터 대기 중...", "warnings": ""}


def ai_parse_log(category, user_text, log_time, ref_data=""):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompts = {
        "섭취": "Nutritionist. Output JSON: {'calories': int, 'food_name': str, 'summary': str}",
        "운동": "Sports Analyst. Output JSON: {'time': int, 'type': str, 'calories': int, 'avg_bpm': int, 'summary': str}",
        "음주": "Alcohol Tracker. Output JSON: {'alcohol_type': str, 'standard_drinks': int, 'calories': int, 'summary': str}",
    }
    role = prompts.get(category.split()[1] if len(category.split())>1 else category, "Health Logger. JSON output.")
    prompt = f"User logged [{category}] at [{log_time}]. Text: '{user_text}'. {role}"
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
        if "gcp_service_account" in st.secrets:
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
        else:
            creds = service_account.Credentials.from_service_account_file(
                'service_account.json',
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
        service = build('calendar', 'v3', credentials=creds)
        
        now_kst = datetime.now() + timedelta(hours=9)
        today_start = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        time_min = (today_start - timedelta(hours=9)).isoformat() + 'Z'
        time_max = (today_end - timedelta(hours=9)).isoformat() + 'Z'
        
        all_events = {"Sports": [], "Termin": []}
        for cal_name, cal_id in CALENDAR_IDS.items():
            events_result = service.events().list(
                calendarId=cal_id, timeMin=time_min, timeMax=time_max,
                singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00')) + timedelta(hours=9)
                all_events[cal_name].append({
                    'title': event.get('summary', '(제목 없음)'),
                    'time': start_time.strftime('%H:%M')
                })
        return all_events
    except:
        return {"Sports": [], "Termin": []}

# ==========================================
# [메인 UI 구조 - 3단 탭]
# ==========================================

# 헤더 영역
st.markdown("## 🧬 Dr. MBJS")
col1, col2 = st.columns([5, 1])
with col1:
    st.caption("무병장수 Command Center")
with col2:
    if st.button("🔄", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# 메인 탭 생성
tab1, tab2, tab3 = st.tabs(["📊 대시보드", "📝 기록하기", "🏎️ Pit Wall"])

# =========================================================
# [TAB 1] Dashboard
# =========================================================
with tab1:
    st.markdown("### 📡 Real-time Bio-Dashboard")
    
    try:
        # ... (DB 연결 코드는 동일) ...
        sheet_health = get_db_connection("Health_Log")
        sheet_action = get_db_connection("Action_Log")
        
        health_data = sheet_health.get_all_records()
        action_data = sheet_action.get_all_records()
        
        df_health = pd.DataFrame(health_data)
        df_action = pd.DataFrame(action_data)
        
        if not df_health.empty:
            # -------------------------------------------------------
            # [시간 보정: 스마트 함수 사용]
            # -------------------------------------------------------
            now_kst = get_current_kst() # <--- 이걸로 통일!
            today_mission_key = get_mission_date_key()
            
            # 1. 캘린더 & 날짜 키
            calendar_events = get_today_calendar_events()
            
            # 2. 오늘 활동
            today_str = now_kst.strftime('%Y-%m-%d') 
            today_logs = df_action[df_action['Date'] == today_str]
            today_activities = []
            for _, row in today_logs.iterrows():
                today_activities.append(f"[{row['Action_Time']}] {row['Category']}: {row['User_Input']}")
            
            # 3. 실시간 최신 데이터
            latest_row = df_health.iloc[-1]
            hrv_curr = round(float(latest_row.get('HRV', 0)), 2)
            rhr_curr = round(float(latest_row.get('RHR', 0)), 2)
            w_curr = round(float(latest_row.get('Weight', 0)), 2)
            
            # 4. 아침 데이터 찾기
            df_health['Date_Clean'] = pd.to_datetime(df_health['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            today_health_logs = df_health[df_health['Date_Clean'] == today_mission_key]
            
            # (1) 상단 메트릭
            st.caption(f"🕒 마지막 업데이트: {latest_row.get('Date', 'Unknown')}")
            mission = calculate_mission_status(w_curr)
            
            def get_signal(val, type):
                if type == 'HRV': return "🟢" if val >= 45 else "🟡" if val >= 30 else "🔴"
                elif type == 'RHR': return "🟢" if val <= 65 else "🟡" if val <= 75 else "🔴"
                return "🟢"
            
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("HRV", f"{hrv_curr} ms")
                    st.caption(f"{get_signal(hrv_curr, 'HRV')} (평균: 40ms)")
                with c2:
                    st.metric("RHR", f"{rhr_curr} bpm")
                    st.caption(f"{get_signal(rhr_curr, 'RHR')} (평균: 65bpm)")
                with c3:
                    st.metric("체중", f"{w_curr} kg")
                    if mission['active']:
                        st.caption(f"목표까지 {w_curr - mission['target_weight']:.1f}kg")
            
            st.divider()
            
            # (2) Daily Check-in (수동 캐싱)
            st.markdown("### ☀️ Daily Check-in")
            
            if not today_health_logs.empty:
                morning_row = today_health_logs.iloc[0]
                
                w_morning = round(float(morning_row['Weight']), 1)
                hrv_morning = round(float(morning_row['HRV']), 1)
                rhr_morning = round(float(morning_row['RHR']), 1)
                
                morning_context_fixed = prepare_full_context(
                    df_health, df_action, w_morning, is_morning_fixed=True
                )
                
                cal_txt_list = []
                sports_events = sorted(calendar_events.get("Sports", []), key=lambda x: x['time'])
                termin_events = sorted(calendar_events.get("Termin", []), key=lambda x: x['time'])
                
                for evt in sports_events:
                    cal_txt_list.append(f"[운동] {evt['time']} {evt['title']}")
                for evt in termin_events:
                    cal_txt_list.append(f"[일정] {evt['time']} {evt['title']}")
                
                calendar_str_fixed = "\n".join(cal_txt_list) if cal_txt_list else "일정 없음"

                cache_key = today_mission_key
                checkin_result = load_checkin_cache(cache_key)
                
                if checkin_result is None:
                    with st.spinner("🤖 Dr. MBJS가 오늘의 전략을 분석 중..."):
                        checkin_result = ai_generate_daily_checkin(
                            today_mission_key, hrv_morning, rhr_morning, w_morning,
                            morning_context_fixed, calendar_str_fixed
                        )
                        if save_checkin_cache(cache_key, checkin_result):
                            st.success("✅ 오늘의 전략을 생성하고 저장했습니다.", icon="💾")
                        clear_old_caches(keep_days=7)
                else:
                    st.info("📋 저장된 오늘의 전략을 불러왔습니다.", icon="♻️")
                
                with st.container(border=True):
                    signal = checkin_result.get('condition_signal', 'Yellow')
                    title = checkin_result.get('condition_title', '분석 중...')
                    
                    if signal == 'Green': icon = "🟢"
                    elif signal == 'Red': icon = "🔴"
                    else: icon = "🟡"
                    
                    st.subheader(f"{icon} {title}")
                    st.markdown(f"**🕵️ 분석:** {checkin_result.get('analysis', '데이터 부족')}")
                    st.divider()
                    st.markdown("**🎯 오늘의 전략 (Schedule-Based)**")
                    
                    c_m1, c_m2, c_m3 = st.columns(3)
                    with c_m1: st.info(f"**💪 운동**\n\n{checkin_result.get('mission_workout')}")
                    with c_m2: st.success(f"**🥗 식단**\n\n{checkin_result.get('mission_diet')}")
                    with c_m3: st.warning(f"**🔋 회복**\n\n{checkin_result.get('mission_recovery')}")
            else:
                st.info(f"💤 아직 오늘의 헬스 데이터가 도착하지 않았습니다. (기준: {today_mission_key} 05:00~)")
            
            # (3) Action Plan
            realtime_context = prepare_full_context(df_health, df_action, w_curr, is_morning_fixed=False)
            
            calendar_summary = "일정 없음"
            if calendar_events['Sports'] or calendar_events['Termin']:
                calendar_summary = str(calendar_events)
            
            combined_activities = today_activities + [f"[CALENDAR] {calendar_summary}"]
            
            action_plan = ai_generate_action_plan(
                hrv_curr, rhr_curr, w_curr, 
                realtime_context, 
                combined_activities
            )
            
            st.write("")
            st.markdown(f"### ⚡ Action Plan ({now_kst.strftime('%H:%M')} 기준)")
            
            with st.container(border=True):
                 st.markdown(f"**📊 현재 상황:** {action_plan.get('current_analysis', '분석 중...')}")
                 
                 # [수정] 줄바꿈 강제 적용 로직 추가
                 raw_actions = action_plan.get('next_actions', '대기 중...')
                 # 마크다운은 \n 하나는 무시하므로, \n을 \n\n(두 줄 띄기)로 강제 치환
                 formatted_actions = raw_actions.replace('\n', '\n\n')
                 
                 st.markdown(f"**🚀 실질적 조언:**\n{formatted_actions}")
                 
                 if action_plan.get('warnings'): st.error(f"⚠️ **경고:** {action_plan['warnings']}")
        
        else:
            st.warning("Health_Log 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"오류 발생: {e}")


# =========================================================
# [TAB 2] 기록하기
# =========================================================
with tab2:
    # 1. 미션 진행도 카드 (사이드바에서 이사 옴)
    current_weight = 0.0
    try:
        active_mission = get_active_mission()
        if active_mission:
            sheet_health = get_db_connection("Health_Log")
            health_data = sheet_health.get_all_records()
            if health_data:
                current_weight = float(health_data[-1]['Weight'])
            else:
                current_weight = active_mission['start_weight']
        else:
            current_weight = 90.4 
    except:
        current_weight = 90.4

    mission_status = calculate_mission_status(current_weight)
    
    with st.container(border=True):
        if mission_status['active']:
            st.success(f"🎯 {mission_status['name']} (D-{mission_status['days_remaining']})")
            
            # 시간 경과
            st.caption(f"⏳ 시간 경과: {mission_status['progress_pct']:.1f}%")
            st.progress(mission_status['progress_pct'] / 100)
            
            # 감량 진행
            loss_amount = mission_status['actual_loss']
            if loss_amount >= 0:
                st.caption(f"📉 감량 진행: {mission_status['weight_progress_pct']:.1f}%")
                st.progress(mission_status['weight_progress_pct'] / 100)
                st.caption(f"👏 현재 {loss_amount:.1f}kg 감량 / 목표 {mission_status['target_loss']:.1f}kg")
            else:
                gain_amount = abs(loss_amount)
                st.caption(f"🚨 **경고: 체중 증가!**")
                st.progress(0)
                st.markdown(f":red[**⚠️ 현재 {gain_amount:.1f}kg 증량**] / 목표 {mission_status['target_loss']:.1f}kg 감량")
        else:
            st.info("진행 중인 미션이 없습니다")
    
    st.divider()

    # 2. 섭취 및 운동 기록
    st.markdown("### 📝 섭취 및 운동 기록")
    
    try:
        mission = get_active_mission()
        sheet_action = get_db_connection("Action_Log")
        df = pd.DataFrame(sheet_action.get_all_records())
        
        with st.container(border=True):
            if not df.empty:
                today_str = datetime.now().strftime("%Y-%m-%d") # KST 고려 안해도 됨 (기록용이니까)
                today_df = df[df['Date'] == today_str]
                
                total_cal = 0
                total_workout = 0
                
                for _, row in today_df.iterrows():
                    try:
                        js = json.loads(row['AI_Analysis_JSON'])
                        if '섭취' in row['Category']:
                            total_cal += js.get('calories', 0)
                        elif '운동' in row['Category']:
                            total_workout += js.get('time', 0)
                    except:
                        continue
            else:
                total_cal, total_workout = 0, 0
            
            c1, c2, c3 = st.columns(3)
            
            if mission:
                c1.metric("섭취 칼로리", f"{total_cal} kcal", f"{mission['daily_calories'] - total_cal}")
            else:
                c1.metric("섭취 칼로리", f"{total_cal} kcal")
            
            c2.metric("운동 시간", f"{total_workout} 분")
            
            if mission:
                rules = get_mission_rules(mission['mission_id'])
                if 'alcohol_ban' in rules:
                    ban_month = rules['alcohol_ban'].get('month')
                    if datetime.now().month == ban_month:
                        c3.metric("Dry Feb", f"{datetime.now().day}/28일")
    except:
        pass
    
    st.write("")
    
    with st.container(border=True):
        with st.form("log_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns([1.5, 0.6, 0.6, 2])
            with col1:
                log_date = st.date_input("날짜", datetime.now(), label_visibility="collapsed")
            with col2:
                hour = st.selectbox("시", range(24), index=datetime.now().hour, label_visibility="collapsed")
            with col3:
                minute = st.selectbox("분", list(range(0, 60, 5)), label_visibility="collapsed")
            with col4:
                category = st.selectbox(
                    "카테고리",
                    ["섭취", "운동", "음주", "영양제", "회복", "노트", "기타"],
                    label_visibility="collapsed"
                )
            
            user_text = st.text_input(
                "내용",
                placeholder="예: 국밥 / 테니스 60분 / 사우나 2사이클",
                label_visibility="collapsed"
            )
            
            col_btn1, col_btn2 = st.columns([4, 1])
            with col_btn2:
                submitted = st.form_submit_button("🚀 저장", use_container_width=True)
            
            if submitted and user_text:
                mission = get_active_mission()
                if mission:
                    violations = validate_mission_rules(mission['mission_id'], category, user_text)
                    if violations:
                        for v in violations:
                            if v['severity'] == 'error':
                                st.error(v['message'])
                                st.stop()
                            else:
                                st.warning(v['message'])
                
                with st.spinner("AI 분석 중..."):
                    try:
                        log_time = f"{hour:02d}:{minute:02d}"
                        ai_res = ai_parse_log(category, user_text, log_time, "")
                        
                        sheet_action = get_db_connection("Action_Log")
                        sheet_action.append_row([
                            log_date.strftime("%Y-%m-%d"),
                            log_time,
                            category,
                            user_text,
                            json.dumps(ai_res, ensure_ascii=False),
                            ""
                        ])
                        
                        st.success("✅ 저장 완료!")
                        st.info(f"📊 {ai_res.get('summary', '기록 완료')}")
                        st.cache_data.clear()
                    
                    except Exception as e:
                        st.error(f"에러: {e}")

    st.divider()

    # 3. 데이터 아카이브 (Expander)
    with st.expander("📂 데이터 아카이브", expanded=False):
        try:
            sheet = get_db_connection("Action_Log")
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if not df.empty:
                reversed_df = df.iloc[::-1]
                
                cat_filter = st.multiselect("카테고리 필터", reversed_df['Category'].unique())
                if cat_filter:
                    display_df = reversed_df[reversed_df['Category'].isin(cat_filter)]
                else:
                    display_df = reversed_df
                
                st.dataframe(
                    display_df[['Date', 'Action_Time', 'Category', 'User_Input']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("데이터 없음")
        except Exception as e:
            st.error(f"오류: {e}")


# =========================================================
# [TAB 3] Pit Wall
# =========================================================
with tab3:
    st.markdown("## 🏎️ The Pit Wall")
    st.caption("Performance Telemetry Center")
    
    try:
        sheet_action = get_db_connection("Action_Log")
        data = sheet_action.get_all_records()
        df = pd.DataFrame(data)
        
        bench_data = []
        if not df.empty:
            workout_df = df[df['Category'].str.contains("운동")]
            for _, row in workout_df.iterrows():
                try:
                    js = json.loads(row['AI_Analysis_JSON'])
                    if js.get('cadence') or "벤치마크" in str(row['User_Input']):
                        bench_data.append({
                            'Date': row['Date'],
                            'Avg_BPM': js.get('avg_bpm', 0)
                        })
                except:
                    continue
        
        if bench_data:
            st.info(f"📊 벤치마크 데이터 {len(bench_data)}개 발견")
        else:
            st.info("텔레메트리 데이터 없음")
    
    except Exception as e:
        st.error(f"Error: {e}")