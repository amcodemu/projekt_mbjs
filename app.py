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

def clear_old_caches(keep_days=7):
    try:
        if not os.path.exists(CACHE_DIR): return
        now = datetime.now()
        for filename in os.listdir(CACHE_DIR):
            if filename.startswith("checkin_"):
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
# [백엔드 함수]
# ==========================================
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

# [수면 시간 파싱 헬퍼 함수 추가]
def parse_korean_datetime(dt_str):
    """구글 시트 형식(2026. 2. 3. 오전 12:39)을 datetime으로 변환"""
    try:
        dt_str = dt_str.replace('.', '').strip()
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
        sheet = get_db_connection("Missions")
        for row in sheet.get_all_records():
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
        sheet = get_db_connection("Mission_Rules")
        rules = {}
        for row in sheet.get_all_records():
            if row['Mission_ID'] == mission_id:
                try: rules[row['Rule_Type']] = json.loads(row['Rule_Value'])
                except: rules[row['Rule_Type']] = row['Rule_Value']
        return rules
    except: return {}

def calculate_mission_status(current_weight):
    mission = get_active_mission()
    if not mission: return {'active': False, 'message': '진행 중인 미션 없음'}
    
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

# ==========================================
# [수정된 prepare_full_context] 수면 정보 결합
# ==========================================
def prepare_full_context(df_health, df_action, current_weight, is_morning_fixed=False):
    now_kst = get_current_kst()
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
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            today_obj = datetime.strptime(today_date_key, '%Y-%m-%d')
            days_ago = (today_obj - date_obj).days
            
            if days_ago == 0: date_label = f"━━━ {date_str} (오늘) ━━━"
            elif days_ago == 1: date_label = f"━━━ {date_str} (어제) ━━━"
            else: date_label = f"━━━ {date_str} ({days_ago}일 전) ━━━"
            
            if date_logs.empty: logs_text = "(기록 없음)"
            else: logs_text = "\n".join([f"• [{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in date_logs.sort_values('Action_Time').iterrows()])
            logs_by_date.append(f"{date_label}\n{logs_text}")
        recent_logs_text = "\n\n".join(logs_by_date)
    else:
        recent_logs_text = "기록 없음"

    # [핵심 수정] 건강 지표 및 수면 시간 정밀 계산
    cutoff = (datetime.strptime(today_date_key, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    df_h_30 = df_health[df_health['Date'] >= cutoff].copy()
    
    for c in ['HRV', 'RHR']: 
        if c in df_h_30.columns: df_h_30[c] = pd.to_numeric(df_h_30[c], errors='coerce')

    hrv_avg = df_h_30.tail(7)['HRV'].mean() if not df_h_30.empty else 0
    rhr_avg = df_h_30.tail(7)['RHR'].mean() if not df_h_30.empty else 0
    
    # [수면 시간 로직 업데이트]
    sleep_info = "No sleep data."
    if not df_h_30.empty:
        last = df_h_30.iloc[-1]
        s_start = last.get('sleep_start', '')
        s_end = last.get('sleep_end', '')
        
        # 실제 수면 시간 계산
        dt_start = parse_korean_datetime(str(s_start))
        dt_end = parse_korean_datetime(str(s_end))
        
        actual_sleep_duration = 0
        if dt_start and dt_end:
            duration = dt_end - dt_start
            actual_sleep_duration = max(0, duration.total_seconds() / 3600)
            
            s_start_display = dt_start.strftime('%H:%M')
            s_end_display = dt_end.strftime('%H:%M')
            sleep_info = f"Last Night Sleep: {actual_sleep_duration:.1f}h (Bed: {s_start_display}, Wake: {s_end_display})"
        else:
            # 기존 컬럼(Sleep_duration) 백업용
            sd = last.get('Sleep_duration', 0)
            sleep_info = f"Last Sleep Duration (Legacy): {sd}h"

    patterns = analyze_patterns(df_h_30, df_action[df_action['Date'] >= cutoff])
    ptn_txt = "\n".join([p['message'] for p in patterns]) if patterns else "None"
    
    return f"""
[USER] Age:35, Male, Mission:{mission['name']}, Wt:{current_weight}kg

[LOGS (Last 5 Days - BY DATE)]
{recent_logs_text}

[TODAY: {today_date_key}]

[STATS] HRV:{hrv_avg:.1f}, RHR:{rhr_avg:.1f}
[SLEEP ANALYSIS] {sleep_info}
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
    [RECOVERY GUIDELINES]  # ← 여기 추가!
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
    
    # 활동 로그 텍스트
    activities_text = "\n".join([f"• {a}" for a in today_activities]) if today_activities else "아직 기록된 활동 없음"
    
    # 평일/주말 규칙
    if weekday < 5: 
        constraint_text = """
        [CRITICAL TIME CONSTRAINTS (Weekdays)]
        - 06:00 ~ 19:00 is WORK TIME. NO GYM suggestions.
        - Exception: Lunch (12:00~13:00) light walk or step walking OK.
        - Focus on 'Post-work' (after 19:00) for main exercise.
        """
    else:
        constraint_text = "[TIME CONSTRAINTS (Weekend)] User is free."
    
    # 시간대 계산 (상대 시간)
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
    
    # ★★★ full_context 다시 생성 (원본 시간 포함) ★★★
    try:
        sheet_health = get_db_connection("Health_Log")
        sheet_action = get_db_connection("Action_Log")
        df_health = pd.DataFrame(sheet_health.get_all_records())
        df_action = pd.DataFrame(sheet_action.get_all_records())
        full_context = prepare_full_context(df_health, df_action, weight, is_morning_fixed=False)
    except:
        full_context = "[Context loading failed]"
    
    # ★★★ 프롬프트 (상대 시간 사용) ★★★
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
        
        # ★★★ 생성 시점 시간 저장 ★★★
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
    
    # 1. 섭취
    if "섭취" in category:
        system_role = """
        You are a Korean Nutritionist.
        Estimate nutrition based on standard Korean serving sizes.
        Rules: Rice 1 bowl=300kcal. Alcohol: Soju 1 btl=7 glasses, Beer 1 btl=3 glasses.
        Output JSON: {"calories": int, "food_name": "str", "macros": "탄:xx 단:xx 지:xx", "summary": "str"}
        """
    
    # 2. 운동
    elif "운동" in category:
        system_role = """
        Sports Data Analyst. Extract workout metrics.
        Output JSON: {
            "time": int, "type": "str", "calories": int,
            "avg_bpm": int, "summary": "str"
        }
        """
    
    # 3. 음주
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
    
    # 4. 영양제
    elif "영양제" in category:
        system_role = """
        Supplement tracker.
        Output JSON: {
            "supplements": ["밀크씨슬", "오메가3" , "마그네슘"],
            "count": int,
            "summary": "영양제 3종 복용"
        }
        """
    
    # 5. 회복
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
    
    # 6. 노트
    elif "노트" in category:
        system_role = """
        Health condition analyzer.
        Output JSON: {
            "symptoms": ["증상1"],
            "stress_level": "high/medium/low",
            "summary": "요약"
        }
        """
    
    # 7. 기타
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
tab1, tab2, tab3 = st.tabs(["📊 대시보드", "📝 기록하기", "🏎️ Pit Wall"])

# [TAB 1] Dashboard
with tab1:
    st.markdown("### 📡 Real-time Bio-Dashboard")
    try:
        sh_h = get_db_connection("Health_Log")
        sh_a = get_db_connection("Action_Log")
        df_h = pd.DataFrame(sh_h.get_all_records())
        df_a = pd.DataFrame(sh_a.get_all_records())
        
        if not df_h.empty:
            now_kst = get_current_kst()
            date_key = get_mission_date_key()
            cal_evts = get_today_calendar_events()
            
            today_logs = df_a[df_a['Date'] == now_kst.strftime('%Y-%m-%d')]
            today_acts = [f"[{r['Action_Time']}] {r['Category']}: {r['User_Input']}" for _, r in today_logs.iterrows()]
            
            last_h = df_h.iloc[-1]
            hrv_c, rhr_c, w_c = float(last_h.get('HRV',0)), float(last_h.get('RHR',0)), float(last_h.get('Weight',0))
            mission = calculate_mission_status(w_c)
            
            st.caption(f"🕒 마지막 업데이트: {last_h.get('Date','Unknown')}")

            # ----------------------------------------------------
            # [수정 완료] HTML 들여쓰기 완전 제거 (Left-Align)
            # ----------------------------------------------------
            hrv_icon = "🟢" if hrv_c >= 45 else "🔴"
            rhr_icon = "🟢" if rhr_c <= 65 else "🔴"
            w_msg = f"{w_c - mission['target_weight']:.1f}kg 남음" if mission['active'] else "-"
            w_col = "#3B82F6" if mission['active'] else "#64748B"

            # 아래 문자열은 왼쪽 벽에 붙어있어야 함
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
<div style="font-size: 11px; color: {w_col}; font-weight: 600;">{w_msg}</div>
</div>
</div>
"""
            st.markdown(dashboard_html, unsafe_allow_html=True)
            
            st.divider()

            # Daily Check-in Header (Left-Align)
            checkin_lbl = f"{date_key} 05:00 기준"
            st.markdown(f"""<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px;"><h3 style="margin: 0;">☀️ Daily Check-in</h3><span style="font-size: 11px; color: #94a3b8;">({checkin_lbl})</span></div>""", unsafe_allow_html=True)

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
                        save_checkin_cache(date_key, ck_res); clear_old_caches()
                
                icon = {"Green":"🟢", "Red":"🔴"}.get(ck_res.get('condition_signal'), "🟡")
                st.subheader(f"{icon} {ck_res.get('condition_title', 'Analyzing...')}")
                with st.container(border=True): st.markdown(f"**🕵️ 분석:** {ck_res.get('analysis')}")
                
                st.write(""); st.markdown("**🎯 오늘의 전략**")
                
                # 전략 박스 (HTML Left-Align)
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"""<div class="strategy-box workout-box"><span class="strategy-title">💪 운동</span>{ck_res.get('mission_workout')}</div>""", unsafe_allow_html=True)
                with c2: st.markdown(f"""<div class="strategy-box diet-box"><span class="strategy-title">🥗 식단</span>{ck_res.get('mission_diet')}</div>""", unsafe_allow_html=True)
                with c3: st.markdown(f"""<div class="strategy-box recovery-box"><span class="strategy-title">🔋 회복</span>{ck_res.get('mission_recovery')}</div>""", unsafe_allow_html=True)
            else: st.info(f"💤 데이터 대기 중 ({date_key})")
            
            # Action Plan
            st.write("")
            rt_ctx = prepare_full_context(df_h, df_a, w_c, False)
            ap = ai_generate_action_plan(hrv_c, rhr_c, w_c, rt_ctx, today_acts + [f"[CALENDAR] {cal_evts}"])
            
            # Action Plan Header (Left-Align)
            st.markdown(f"""<h3 style="margin-bottom: 10px;">⚡ Action Plan <span class="time-badge">{ap.get('generated_at', now_kst.strftime('%H:%M'))} 기준</span></h3>""", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown(f"**📊 현재 상황:** {ap.get('current_analysis')}")
                st.markdown(f"**🚀 실질적 조언:**\n{ap.get('next_actions', '').replace(chr(10), chr(10)*2)}")
                if ap.get('warnings'): st.error(f"⚠️ {ap['warnings']}")
        else: st.warning("No Data")
    except Exception as e: st.error(f"Error: {e}")

# =========================================================
# [TAB 2] 기록하기
# =========================================================
with tab2:
    now_kst = get_current_kst()
    today_str = now_kst.strftime('%Y-%m-%d')
    
    # ★★★ [추가] 미션 진행도 섹션 ★★★
    st.markdown("### 🎯 미션 현황")
    
    # 현재 체중 가져오기
    current_weight = 0.0
    try:
        sh_h = get_db_connection("Health_Log")
        df_h = pd.DataFrame(sh_h.get_all_records())
        if not df_h.empty:
            current_weight = float(df_h.iloc[-1]['Weight'])
        else:
            current_weight = 90.4  # 기본값
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
    
    st.markdown("### 📊 오늘의 기록")

    # ★★★ 캐싱된 함수 ★★★
    @st.cache_data(ttl=300)  # 5분 캐시
    def get_today_summary(date_str):
        cal = 0
        mins = 0
        try:
            sh_a = get_db_connection("Action_Log")
            df_a = pd.DataFrame(sh_a.get_all_records())
            
            if not df_a.empty:
                df_a['Date_Clean'] = pd.to_datetime(df_a['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                today_df = df_a[df_a['Date_Clean'] == date_str]
                
                for _, r in today_df.iterrows():
                    try:
                        js = json.loads(r['AI_Analysis_JSON'])
                        if '섭취' in r['Category']: cal += js.get('calories', 0)
                        if '운동' in r['Category']: mins += js.get('time', 0)
                    except: pass
        except: pass
        
        return {'calories': cal, 'minutes': mins}

    # 캐시된 데이터 가져오기
    summary = get_today_summary(today_str)

    # ★★★ HTML 스타일링으로 표시 ★★★
    summary_html = f"""
    <div style="display: flex; gap: 8px; margin-bottom: 20px;">
    <div style="flex: 1; background: #FFFFFF; padding: 14px 8px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
    <div style="font-size: 12px; color: #64748B; font-weight: 600; margin-bottom: 6px;">섭취 칼로리</div>
    <div style="font-size: 22px; font-weight: 900; color: #1A2B4D;">{summary['calories']} kcal</div>
    </div>
    <div style="flex: 1; background: #FFFFFF; padding: 14px 8px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
    <div style="font-size: 12px; color: #64748B; font-weight: 600; margin-bottom: 6px;">운동 시간</div>
    <div style="font-size: 22px; font-weight: 900; color: #1A2B4D;">{summary['minutes']} 분</div>
    </div>
    <div style="flex: 1; background: #FFFFFF; padding: 14px 8px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
    <div style="font-size: 12px; color: #64748B; font-weight: 600; margin-bottom: 6px;">Dry Feb</div>
    <div style="font-size: 22px; font-weight: 900; color: #1A2B4D;">{now_kst.day}/28일</div>
    </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)
    
    # ★★★ 입력 폼 ★★★
    with st.container(border=True):
        with st.form("log", clear_on_submit=True):
            # ★★★ 한 줄에 4개 필드 ★★★
            c1, c2, c3, c4 = st.columns([2, 0.7, 0.7, 1.2])
            
            with c1: 
                d = st.date_input("", now_kst.date(), label_visibility="collapsed")
            with c2: 
                h = st.selectbox("", range(24), index=now_kst.hour, label_visibility="collapsed")
            with c3: 
                m = st.selectbox("", list(range(0,60,5)), index=(now_kst.minute//5), label_visibility="collapsed")
            with c4: 
                cat = st.selectbox("", ["섭취","운동","음주","영양제","회복","노트"], label_visibility="collapsed")
            
            # 내용 입력
            txt = st.text_input("", placeholder="예: 닭가슴살 샐러드", label_visibility="collapsed")
            
            # 저장 버튼
            if st.form_submit_button("🚀 저장", use_container_width=True) and txt:
                with st.spinner("Saving..."):
                    tm = f"{h:02d}:{m:02d}"
                    parsed = ai_parse_log(cat, txt, tm)
                    get_db_connection("Action_Log").append_row([
                        d.strftime("%Y-%m-%d"), 
                        tm, 
                        cat, 
                        txt, 
                        json.dumps(parsed, ensure_ascii=False), 
                        ""
                    ])
                    st.success("Saved!")
                    st.cache_data.clear()
    
    st.divider()
    
    # ★★★ [개선] 아카이브 캐싱 ★★★
    with st.expander("📂 아카이브"):
        @st.cache_data(ttl=300)
        def load_archive_data():
            sh_a = get_db_connection("Action_Log")
            df = pd.DataFrame(sh_a.get_all_records())
            return df
        
        try:
            df = load_archive_data()
            if not df.empty:
                st.dataframe(
                    df.iloc[::-1][['Date','Action_Time','Category','User_Input']].head(50),
                    use_container_width=True, 
                    hide_index=True
                )
        except: 
            st.error("로딩 실패")

# [TAB 3] Pit Wall
with tab3:
    st.markdown("## 🏎️ The Pit Wall")
    try:
        sh_a = get_db_connection("Action_Log")
        df = pd.DataFrame(sh_a.get_all_records())
        bd = []
        for _, r in df[df['Category'].str.contains("운동")].iterrows():
            try:
                js = json.loads(r['AI_Analysis_JSON'])
                if js.get('cadence') or "벤치마크" in str(r['User_Input']): bd.append({'Date':r['Date'], 'BPM':js.get('avg_bpm',0)})
            except: continue
        st.info(f"데이터 {len(bd)}개" if bd else "없음")
    except: st.error("Error")