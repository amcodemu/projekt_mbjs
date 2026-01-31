import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import json
from datetime import datetime
import altair as alt
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import timedelta

# ==========================================
# [설정 구역] API 키 및 상수
# ==========================================


# 로컬 vs 배포 환경 구분
if "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    OPENAI_API_KEY = "sk-proj-tbiqL6AIgpabIVUKosWY..."  # 로컬용

SHEET_NAME = "Projekt_MBJS_DB"
CALENDAR_IDS = {
    "Sports": "nc41q7u653f9na0nt55i2a8t14@group.calendar.google.com",
    "Termin": "u125ev7cv5du60n94crf4naqak@group.calendar.google.com"
}

# --- 1. 디자인 설정 ---
st.set_page_config(page_title="Projekt MBJS", layout="wide", page_icon="🧬")

st.markdown("""
<style>
    .stApp { background-color: #F5F7FA; color: #1A2B4D; font-family: 'Inter', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #FFFFFF;
        border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        font-weight: 600; color: #7F8C9D; border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD !important; color: #007AFF !important; border: 1px solid #007AFF !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important; border-radius: 20px !important;
        border: 1px solid #E1E5EB !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
        padding: 20px !important;
    }
    div[data-testid="stMetricValue"] { color: #007AFF !important; font-weight: 800 !important; }
    input[type="text"], input[type="number"], .stDateInput input, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; color: #1A2B4D !important;
        border: 1px solid #E6E8EB !important; border-radius: 10px !important;
    }
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #007AFF 0%, #0055FF 100%) !important;
        border: none !important; box-shadow: 0 4px 10px rgba(0, 122, 255, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 백엔드 함수 (모든 기능 통합) ---

@st.cache_resource #같은 시트를 반복 로드할 때 캐시 사용
def get_db_connection(worksheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # 로컬 vs 배포 환경 구분
    if "gcp_service_account" in st.secrets:
        # 배포 환경: Streamlit Cloud
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
    else:
        # 로컬 환경
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).worksheet(worksheet_name)
    return sheet

def ai_parse_log(category, user_text, log_time, ref_data=""):
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 1. 식단
    if "섭취" in category:
        system_role = f"""
        You are a highly experienced Korean Nutritionist.
        Estimate nutrition based on standard Korean serving sizes.
        Rules: Rice(밥) 1 bowl=300kcal. Alcohol: Soju 1 btl=7 glasses , Beer 1 btl = 3 glasses , wine 1 btl = 14 glasses
        Output JSON: {{"calories": int, "food_name": "str", "macros": "탄:xx 단:xx 지:xx", "alcohol_glasses": float}}
        """
        
    # 2. 운동 (텔레메트리 데이터 추출)
    elif "운동" in category:
        system_role = """
        You are a Sports Data Analyst. Extract exact workout metrics.
        [Analysis Rules]
        1. General: time(min), type, calories, avg_bpm, max_bpm.
        2. **Benchmark Running (Telemetry):**
           - Extract 'Cadence', 'Vertical Oscillation', 'GCT' if available.
        Output JSON: 
        {
            "time": int, "intensity": int, "type": "str", 
            "calories": int, "avg_bpm": int, "max_bpm": int,
            "cadence": int, "vertical_osc": float, "gct": int, 
            "summary": "str", "analysis": "str"
        }
        """
    
    # 3. 기타
    else: 
        system_role = "Health Logger."

    prompt = f"Context: User logged [{category}] at [{log_time}]. Text: '{user_text}'. Role: {system_role}. Return ONLY JSON."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def summarize_recent_actions(df_act, days=3):
    """
    최근 N일간 Action_Log를 요약
    목적: AI 원인 분석에 필요한 핵심 정보 추출
    """
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    
    # 최근 N일 데이터만 필터링
    recent = df_act[df_act['Date'] >= cutoff_str]
    
    # 요약 딕셔너리 초기화
    summary = {
        "alcohol_glasses": 0,
        "sodium_foods": 0,
        "workout_minutes": 0,
        "daily_logs": []  # 날짜별 주요 활동 텍스트
    }
    
    # 각 로그 순회하며 데이터 집계
    for _, row in recent.iterrows():
        try:
            js = json.loads(row['AI_Analysis_JSON'])
            date = row['Date']
            category = row['Category']
            
            # 1. 알코올 집계
            if "섭취" in category:
                alcohol = js.get('alcohol_glasses', 0)
                if alcohol > 0:
                    summary['alcohol_glasses'] += alcohol
                    summary['daily_logs'].append(
                        f"{date}: 알코올 {int(alcohol)}잔"
                    )
                
                # 2. 고염분 음식 체크
                food = js.get('food_name', '')
                if any(word in food for word in ['국밥', '찌개', '탕', '라면', '국물']):
                    summary['sodium_foods'] += 1
                    summary['daily_logs'].append(
                        f"{date}: {food} (고염분)"
                    )
            
            # 3. 운동 집계
            elif "운동" in category:
                workout_time = js.get('time', 0)
                if workout_time > 0:
                    summary['workout_minutes'] += workout_time
                    workout_type = js.get('type', '운동')
                    summary['daily_logs'].append(
                        f"{date}: {workout_type} {workout_time}분"
                    )
        
        except Exception as e:
            # JSON 파싱 실패 시 무시
            continue
    
    return summary


@st.cache_data(ttl=300)  # 5분 동안 캐시
def ai_analyze_cause(hrv, rhr, weight, action_summary):
    """
    바이오 지표 + 최근 활동 → AI가 원인 분석
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 활동 로그를 텍스트로 변환
    if action_summary['daily_logs']:
        logs_text = "\n".join(action_summary['daily_logs'])
    else:
        logs_text = "기록 없음"
    
    # AI 프롬프트
    prompt = f"""
당신은 데이터 기반 건강 컨설턴트입니다.

[오늘 측정값]
- HRV: {hrv}ms (정상: 30-100ms, 3040 남성 평균: 40ms)
- RHR: {rhr}bpm (정상: 60-70bpm)
- 체중: {weight}kg

[최근 3일 활동 기록]
{logs_text}

[분석 규칙]
1. HRV/RHR 수치의 **직접적 원인**을 활동 기록에서 찾으세요.
2. 추측 금지. 기록된 데이터만 근거로 사용하세요.
3. 우선순위: 알코올 > 고염분 식단 > 과도한 운동 > 기타
4. 활동 기록이 없으면 "데이터 부족으로 추정 불가"라고 명시하세요.
5. 2-3문장으로 간결하게 작성하세요.

[출력 형식 - 반드시 JSON]
{{
  "primary": "핵심 원인을 1문장으로",
  "details": ["세부 근거 1", "세부 근거 2"],
  "confidence": "high 또는 medium 또는 low"
}}

예시:
{{
  "primary": "1/28 알코올 14잔 섭취가 HRV 급락의 직접 원인입니다",
  "details": ["간 해독 과정에서 자율신경계 억제", "1/29 고염분 식단으로 회복 지연"],
  "confidence": "high"
}}
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        # API 오류 시 기본 응답
        return {
            "primary": "분석 중 오류 발생",
            "details": [str(e)],
            "confidence": "low"
        }

@st.cache_data(ttl=300)
def ai_generate_action_plan(condition_status, hrv, rhr, weight, action_summary, calendar_events):
    """
    컨디션 + 최근 활동 + 오늘 캘린더 일정 → AI가 맞춤형 액션 플랜 생성
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # 활동 로그 텍스트 변환
    if action_summary['daily_logs']:
        logs_text = "\n".join(action_summary['daily_logs'])
    else:
        logs_text = "기록 없음"
    
    # 캘린더 일정 텍스트 변환
    calendar_text = []
    for event in calendar_events.get("Sports", []):
        calendar_text.append(f"[Sports] {event['time']} {event['title']}")
    for event in calendar_events.get("Termin", []):
        calendar_text.append(f"[Termin] {event['time']} {event['title']}")
    
    if calendar_text:
        calendar_str = "\n".join(calendar_text)
    else:
        calendar_str = "일정 없음"
    
    # AI 프롬프트
    prompt = f"""
당신은 냉정하고 전문적인 건강 컨설턴트입니다.

[현재 컨디션]
- 상태: {condition_status} (RED=위험/YELLOW=주의/GREEN=최상)
- HRV: {hrv}ms
- RHR: {rhr}bpm
- 체중: {weight}kg

[최근 3일 활동]
{logs_text}

[오늘 일정]
{calendar_str}

[임무]
오늘의 액션 플랜 3가지를 생성하세요:
1. 💪 운동 가이드
2. 🥗 식단 가이드
3. 🔋 회복 가이드

[사용자 상황 정보 - 반드시 고려할 것]
1. **근무 시간 제약**
   - 월~금 06:00-19:00은 업무 시간 → 이 시간에는 별도 활동 불가능
   - 11:30-13:00 점심시간 → 필요시 30분 산책 또는 계단 오르기 조언 가능
   - 주말은 시간 자유로움

2. **가능한 회복 루틴**
   - **사우나:** 1사이클 = 사우나 10분 → 냉탕 3분 → 휴식 5분
   - 평소 2사이클 진행함
   - 오늘 컨디션 고려해서 몇 사이클 권장할지, 또는 사우나 자체가 과부하인지 판단
   - **명상:** 시간대와 길이 구체적으로
   - **수면:** 취침 시각, 수면 시간, 수면 환경 조성 방법

[중요 규칙]
1. **오늘 캘린더 일정을 반드시 고려**하세요
   - 운동 일정 있으면: 현재 컨디션으로 가능한지 판단
   - 회식/약속 있으면: 알코올/식단 주의사항 명시
   - 일정 과밀하면: 스트레스 관리 조언

2. **컨디션 기반 우선순위**
   - RED: 완전 휴식 우선, 일정 조정 권장
   - YELLOW: 강도 낮춤, 조심스럽게 진행
   - GREEN: 적극적 활동 권장

3. **구체적이고 실행 가능하게**
   - "적당히" 금지 → "Zone 2, 30분 이하" 같이 명확히
   - "주의" 금지 → "소주 2잔 이하" 같이 수치로

4. **간결하게**
   - 각 항목당 1-2문장
   
[출력 형식 - JSON]
{{
  "workout": "운동 가이드 (캘린더 일정 반영)",
  "diet": "식단 가이드 (캘린더 일정 반영)",
  "recovery": "회복 가이드"
}}

예시:
예시 1 (평일 RED 상태):
{{
  "workout": "19:00 퇴근 후 완전 휴식. 점심시간에 15분 가벼운 산책만 권장.",
  "diet": "점심 회식 예정 확인. 알코올 금지, 국물 요리 피하고 단백질 위주 섭취.",
  "recovery": "사우나 1사이클만 (현재 HRV로는 2사이클 과부하). 22:00 이전 취침, 명상 10분 후 수면."
}}

예시 2 (주말 GREEN 상태):
{{
  "workout": "오전 테니스 레슨 OK. 강도 높여도 무방, 레슨 후 쿨다운 필수.",
  "diet": "운동 전 탄수화물 충분히, 운동 후 단백질 30g 이상 섭취.",
  "recovery": "사우나 2사이클 진행 가능. 저녁 명상 15분, 23시 이전 취침으로 회복 최적화."
}}

예시 3 (평일 YELLOW, 사우나 과부하 판단):
{{
  "workout": "점심시간 계단 10층 오르기 2회. 퇴근 후 추가 운동 금지.",
  "diet": "저염식 유지. 저녁 7시 이전 식사 완료.",
  "recovery": "현재 RHR 72bpm으로 사우나는 심혈관 부담. 오늘은 명상 20분 + 미온욕으로 대체. 22:00 취침."
}}
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        # 에러 시 기본 플랜
        return {
            "workout": "완전 휴식 권장",
            "diet": "저염식 + 충분한 수분 섭취",
            "recovery": "10시 30분 이전 취침",
            "error": str(e)
        }




def get_today_calendar_events():
    try:
        # 로컬 vs 배포 환경 구분
        if "gcp_service_account" in st.secrets:
            # 배포 환경: Streamlit Cloud
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
        else:
            # 로컬 환경
            creds = service_account.Credentials.from_service_account_file(
                'service_account.json',
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
        service = build('calendar', 'v3', credentials=creds)
        
        # 오늘 날짜 범위 설정 (00:00 ~ 23:59)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # ISO 8601 형식으로 변환
        time_min = today_start.isoformat() + 'Z'
        time_max = today_end.isoformat() + 'Z'
        
        # 결과 저장
        all_events = {
            "Sports": [],
            "Termin": []
        }
        
        # 각 캘린더에서 이벤트 가져오기
        for cal_name, cal_id in CALENDAR_IDS.items():
            events_result = service.events().list(
                calendarId=cal_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            for event in events:
                # 시간 추출
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                
                # 이벤트 정보 저장
                all_events[cal_name].append({
                    'title': event.get('summary', '(제목 없음)'),
                    'time': start_time.strftime('%H:%M'),
                    'description': event.get('description', '')
                })
        
        return all_events
    
    except Exception as e:
        # 에러 시 빈 결과 반환
        return {"Sports": [], "Termin": [], "error": str(e)}




# --- 3. 메인 UI 구성 (사이드바 메뉴로 페이지 전환) ---

with st.sidebar:
    st.header("🧬 Projekt MBJS")
    st.caption("AI Health Command Center")
    
    # 메뉴 선택 (3개로 확장)
    page = st.radio("메뉴 이동", [
        "🏠 Daily Dashboard", 
        "🏎️ The Pit Wall", 
        "📂 Log Archive"
    ])
    
    st.divider()
    st.markdown("### ℹ️ User Profile")
    st.caption("Target Weight: **83.0kg**")
    st.caption("Focus: **Tennis / Zone 2**")

# =========================================================
# [PAGE 1] 🏠 Daily Dashboard
# =========================================================
if page == "🏠 Daily Dashboard":
    st.markdown("## 🏠 Daily Dashboard")

    tab1, tab2 = st.tabs(["🌞 Morning Check-in (진단)", "📝 Daily Action Log (실행)"])

    # --- [Tab 1] 진단 대시보드 ---
    with tab1:
        st.markdown("### 📡 Real-time Bio-Dashboard")
        try:
            sheet_health = get_db_connection("Health_Log")
            sheet_action = get_db_connection("Action_Log")
            
            health_data = sheet_health.get_all_records()
            action_data = sheet_action.get_all_records()
            
            df = pd.DataFrame(health_data)
            df_act = pd.DataFrame(action_data)
            
            if not df.empty:
                df['Date_Obj'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Day_Str'] = df['Date_Obj'].dt.strftime("%m-%d")
                for c in ['HRV', 'RHR', 'Weight']: df[c] = pd.to_numeric(df[c], errors='coerce')

                # Worst Case Logic
                df_daily = df.groupby('Day_Str').agg({
                    'HRV': 'min', 'RHR': 'max', 'Weight': 'max', 'Date_Obj': 'max'
                }).reset_index().sort_values('Date_Obj')
                
                df_recent = df_daily.tail(7) 
                last_row = df.iloc[-1] 
                prev_row = df_daily.iloc[-2] if len(df_daily) > 1 else last_row

                st.caption(f"🕒 마지막 업데이트: {last_row.get('Date', 'Unknown')}")

                # Action Log 요약
                recent_actions = []
                if not df_act.empty:
                    target_dates = [datetime.now().strftime("%Y-%m-%d"), (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")]
                    recent_acts = df_act[df_act['Date'].isin(target_dates)]
                    for _, row in recent_acts.iterrows():
                        recent_actions.append(f"[{row['Date']} {row['Category']}] {row['User_Input']}")
                action_summary = "\n".join(recent_actions) if recent_actions else "최근 기록된 활동 없음."

                # 기능 함수들
                def make_sparkline(data, y_col, color_hex):
                    return alt.Chart(data).mark_line(point=True, strokeWidth=3).encode(
                        x=alt.X('Day_Str', title=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y(y_col, title=None, scale=alt.Scale(zero=False)),
                        color=alt.value(color_hex), tooltip=['Day_Str', y_col]
                    ).properties(height=100)

                def get_traffic_signal(val, type):
                    if type == 'HRV': return "🔴 Achtung!" if val < 30 else "🟡 Caution" if val < 45 else "🟢 Keep it up!"
                    elif type == 'RHR': return "🔴 Achtung!" if val > 75 else "🟡 Caution" if val > 65 else "🟢 Keep it up!"
                    elif type == 'Score': 
                        if val < 60: return "🔴 F (낙제)"
                        elif val < 70: return "🔴 D (위험)"
                        else: return "🟢 Keep it up!"
                    return ""
                
                def get_status_color(signal_text):
                    if "🔴" in signal_text: return "#FF4B4B"
                    elif "🟡" in signal_text: return "#FFA726"
                    return "#2ECC71"

                # -----------------------------------------------------------
                # [점수 및 변수 계산] (변수명 복구 완료)
                # -----------------------------------------------------------
                try: hrv_curr = int(last_row.get('HRV', 0))
                except: hrv_curr = 0
                hrv_signal = get_traffic_signal(hrv_curr, 'HRV')
                hrv_color = get_status_color(hrv_signal)

                try: rhr_curr = int(last_row.get('RHR', 0))
                except: rhr_curr = 0
                rhr_signal = get_traffic_signal(rhr_curr, 'RHR')
                rhr_color = get_status_color(rhr_signal)

                TARGET_WEIGHT = 83.0
                try:
                    w_curr = float(last_row.get('Weight', 0))
                    w_prev = float(prev_row['Weight']) if prev_row['Weight'] > 0 else w_curr
                    if w_curr > 0:
                        gap = abs(w_curr - TARGET_WEIGHT)
                        base_score = 100 - (gap * 6)
                        trend_score = 3 if w_curr < w_prev else -3 if w_curr > w_prev else -1
                        final_score = int(min(100, max(0, base_score + trend_score)))
                    else: final_score, w_curr = 0, 0.0
                except: final_score, w_curr = 0, 0.0
                score_signal = get_traffic_signal(final_score, 'Score')
                score_color = get_status_color(score_signal)

                # -----------------------------------------------------------
                # [UI 출력] 3단 대시보드
                # -----------------------------------------------------------
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("HRV (회복탄력성)", f"{hrv_curr} ms")
                        st.caption(f"**{hrv_signal}** (3040평균: 40ms)")
                        if not df_recent.empty: st.altair_chart(make_sparkline(df_recent, 'HRV', hrv_color), use_container_width=True)
                    with c2:
                        st.metric("RHR (안정시심박)", f"{rhr_curr} bpm")
                        st.caption(f"**{rhr_signal}** (3040평균: 65bpm)")
                        if not df_recent.empty: st.altair_chart(make_sparkline(df_recent, 'RHR', rhr_color), use_container_width=True)
                    with c3:
                        st.metric("체중 관리 지수", f"{final_score} 점")
                        st.caption(f"**{score_signal}** (Target: {TARGET_WEIGHT}kg)")
                        if not df_recent.empty: st.altair_chart(make_sparkline(df_recent, 'Weight', score_color), use_container_width=True)
                
                st.info(f"⚖️ **현재 체중: {w_curr}kg** (목표까지 {round(w_curr - TARGET_WEIGHT, 1)}kg 남음)")

                # ===========================================================
                # 🩺 닥터 MBJS의 즉시 분석 (상세 로직 복구 완료)
                # ===========================================================
                st.divider()
                st.markdown("### 🩺 닥터 MBJS의 종합 진단")

                # [1] 상태 진단 로직
                if "Achtung" in hrv_signal or "Achtung" in rhr_signal:
                    condition_status = "RED"
                    summary_title = "🚨 [경고] 신체 기능 저하 감지"
                elif "Caution" in hrv_signal or "Caution" in rhr_signal:
                    condition_status = "YELLOW"
                    summary_title = "🟡 [주의] 컨디션 조절 필요"
                else:
                    condition_status = "GREEN"
                    summary_title = "🟢 [최상] 훈련 준비 완료"

                # [2] 텍스트 생성 로직
                # 1) 지표 해석
                interpret_texts = []
                if hrv_curr < 40:
                    interpret_texts.append(f"• **HRV({hrv_curr}ms):** 3040 남성 평균(40ms)보다 낮습니다. 자율신경계가 억눌려 있습니다.")
                else:
                    interpret_texts.append(f"• **HRV({hrv_curr}ms):** 평균 이상으로 회복 탄력성이 아주 좋습니다.")
                
                if rhr_curr > 65:
                    interpret_texts.append(f"• **RHR({rhr_curr}bpm):** 심장이 평소보다 빠르게 뛰고 있습니다(평균 65bpm 초과). 엔진이 과열된 상태입니다.")
                else:
                    interpret_texts.append(f"• **RHR({rhr_curr}bpm):** 심박수가 아주 안정적입니다.")
                    
                if w_curr > w_prev:
                    interpret_texts.append(f"• **체중:** 어제보다 **{round(w_curr - w_prev, 1)}kg 증가**하여 점수가 깎였습니다.")
                elif w_curr < w_prev:
                    interpret_texts.append(f"• **체중:** 어제보다 **{round(w_prev - w_curr, 1)}kg 감소**하는 긍정적 추세입니다.")

                # [🆕 추가] AI 기반 원인 분석 실행
                recent_summary = summarize_recent_actions(df_act, days=3)
                ai_cause = ai_analyze_cause(hrv_curr, rhr_curr, w_curr, recent_summary)

                # 2) 원인 분석
                cause_texts = []

                # [🆕] AI 분석 결과 우선 표시
                cause_texts.append(f"• **핵심 원인:** {ai_cause['primary']}")

                # [🆕] 세부 근거 추가
                if ai_cause['details']:
                    for detail in ai_cause['details']:
                        cause_texts.append(f"• {detail}")
                
                if w_curr > w_prev:
                    cause_texts.append("• **체중 증가 원인:** 어제 섭취한 국물(염분)이나 야식으로 인한 수분 저류(붓기) 가능성이 높습니다.")

                # 3) 오늘의 액션 플랜
                # [🆕] 캘린더 일정 가져오기
                calendar_events = get_today_calendar_events()

                # [🆕] AI가 캘린더 고려해서 액션 플랜 생성
                ai_plan = ai_generate_action_plan(
                    condition_status, 
                    hrv_curr, 
                    rhr_curr, 
                    w_curr, 
                    recent_summary,
                    calendar_events
                )

                # [🆕] AI 생성 플랜을 리스트로 변환
                action_plans = [
                    f"💪 **운동:** {ai_plan.get('workout', '데이터 부족')}",
                    f"🥗 **식단:** {ai_plan.get('diet', '데이터 부족')}",
                    f"🔋 **회복:** {ai_plan.get('recovery', '데이터 부족')}"
                ]

                # [3] 화면 출력
                st.markdown(f"#### {summary_title}")
                with st.container(border=True):
                    st.markdown(f"##### 1️⃣ 지표 해석")
                    for t in interpret_texts: st.markdown(t)
                    st.markdown("---")
                    st.markdown(f"##### 2️⃣ 원인 분석 (최근 3일 데이터 기반)")
                    for t in cause_texts: 
                        st.markdown(t)

                    # [🆕] 확신도 표시
                    conf = ai_cause.get('confidence', 'low')
                    if conf == 'high':
                        st.info("📊 확신도: ⬛⬛⬛⬛⬜ (80%+) - 명확한 원인 확인")
                    elif conf == 'medium':
                        st.info("📊 확신도: ⬛⬛⬛⬜⬜ (50-80%) - 추정 가능")
                    else:
                        st.warning("📊 확신도: ⬛⬛⬜⬜⬜ (<50%) - 추가 데이터 필요")
                    st.markdown("---")
                    st.markdown(f"##### 3️⃣ 오늘의 액션 플랜")
                    for t in action_plans: st.markdown(t)

                # [수정됨] 상세 가이드 전체 복구
                st.write("")
                st.write("")
                with st.expander("ℹ️ [일러두기] 지표 해석 가이드 & 결정 변수"):
                    st.markdown("""
                    **1. HRV (심박 변이도 / Heart Rate Variability)**
                    * **정의:** 심장 박동 사이의 시간 간격이 얼마나 불규칙한가를 나타냅니다. (규칙적일수록 나쁨, 불규칙할수록 좋음)
                    * **의미:** 자율신경계(교감/부교감)의 균형 상태. 수치가 **높을수록(High)** 회복이 잘 된 상태입니다.
                    * **결정 변수 (Variables):** 
                        * 📉 **감소 요인:** 수면 부족, 음주(가장 큼), 늦은 식사, 정신적 스트레스, 오버트레이닝.
                        * 📈 **증가 요인:** 양질의 수면, 명상, 냉수욕, 규칙적인 유산소 운동.

                    **2. RHR (안정시 심박수 / Resting Heart Rate)**
                    * **정의:** 완전히 휴식하고 있을 때(보통 기상 직후) 1분당 심장 박동 수입니다.
                    * **의미:** 심폐 기능의 효율성. 엔진의 공회전 속도와 같습니다. 수치가 **낮을수록(Low)** 심장이 튼튼하다는 뜻입니다.
                    * **결정 변수 (Variables):**
                        * 📈 **증가 요인(나쁨):** 탈수, 염증/감기, 체온 상승, 전날 과식, 알코올, 카페인.
                        * 📉 **감소 요인(좋음):** 꾸준한 지구력 훈련(Zone 2), 체중 감량.

                    **3. 체중 관리 지수 (Weight Score)**
                    * **정의:** 목표 체중(83kg) 도달률과 최근 체중 변화 추세를 종합한 자체 점수입니다. (100점 만점)
                    * **결정 변수 (Variables):** 
                        * **목표 거리:** 83kg에서 멀어질수록 감점.
                        * **추세 보너스:** 어제보다 감량했으면 가산점(+), 증량했으면 벌점(-).
                    """)

            else: st.warning("데이터가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

    # --- [Tab 2] Action Log ---
    with tab2:
        st.markdown("### 📝 섭취 및 운동 기록")
        try:
            sheet_action = get_db_connection("Action_Log")
            df = pd.DataFrame(sheet_action.get_all_records())
            
            with st.container(border=True):
                if not df.empty:
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    today_df = df[df['Date'] == today_str]
                    total_cal = sum([json.loads(x).get('calories',0) for x in today_df[today_df['Category'].str.contains("섭취")]['AI_Analysis_JSON']])
                    total_workout = sum([json.loads(x).get('time',0) for x in today_df[today_df['Category'].str.contains("운동")]['AI_Analysis_JSON']])
                    last_act = df.iloc[-1]['Category']
                else: total_cal, total_workout, last_act = 0, 0, "-"
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Calories", f"{total_cal} kcal", f"{2000-total_cal} left")
                c2.metric("Workout", f"{total_workout} min", "Target: 60m")
                c3.metric("Last Action", last_act)
        except: pass

        st.write("")
        with st.container(border=True):
            with st.form("log_form", clear_on_submit=True):
                c1, c2, c3, c4, c5 = st.columns([1.2, 0.1, 0.8, 0.8, 1.5]) 
                with c1: log_date = st.date_input("d", datetime.now(), label_visibility="collapsed")
                with c3: hour = st.selectbox("h", range(24), index=datetime.now().hour, label_visibility="collapsed")
                with c4: minute = st.selectbox("m", list(range(0, 60, 5)), label_visibility="collapsed")
                with c5: category = st.selectbox("c", ["🍽️ 섭취", "💪 운동", "🎸 기타"], label_visibility="collapsed")
                
                c_in, c_btn = st.columns([4, 1])
                with c_in: user_text = st.text_input("input", placeholder="예: 국밥 1그릇 / 벤치마크 러닝", label_visibility="collapsed")
                with c_btn: submitted = st.form_submit_button("🚀 전송", use_container_width=True)

                if submitted and user_text:
                    with st.spinner("AI 분석 중... (Pure AI Mode)"):
                        try:
                            log_time = f"{hour:02d}:{minute:02d}"
                            ai_res = ai_parse_log(category, user_text, log_time, "")
                            
                            sheet_action.append_row([log_date.strftime("%Y-%m-%d"), log_time, category, user_text, json.dumps(ai_res, ensure_ascii=False), ""])
                            st.toast("✅ 저장 완료!")
                            
                            if "운동" in category and ai_res.get('cadence'):
                                st.success(f"🏎️ 텔레메트리 데이터 감지! (RPM: {ai_res.get('cadence')})")
                            else:
                                st.info(f"📊 {ai_res.get('summary', '기록 완료')}")
                        except Exception as e: st.error(f"에러: {e}")

# =========================================================
# [PAGE 2] 🏎️ The Pit Wall
# =========================================================
elif page == "🏎️ The Pit Wall": 
    st.markdown("## 🏎️ The Pit Wall")
    st.caption("Telemetry Analysis Center: 고정 부하(Dyno Test) 환경에서의 신체 엔진 효율성 정밀 분석")

    try:
        sheet_action = get_db_connection("Action_Log")
        data = sheet_action.get_all_records()
        df = pd.DataFrame(data)

        # 벤치마크 데이터(Telemetry) 추출
        bench_data = []
        if not df.empty:
            workout_df = df[df['Category'].str.contains("운동")]
            for _, row in workout_df.iterrows():
                try:
                    js = json.loads(row['AI_Analysis_JSON'])
                    if js.get('cadence') or "벤치마크" in str(row['User_Input']):
                        bench_data.append({
                            'Date': row['Date'],
                            'Cadence': js.get('cadence', 0),
                            'Oscillation': js.get('vertical_osc', 0),
                            'GCT': js.get('gct', 0),
                            'Avg_BPM': js.get('avg_bpm', 0)
                        })
                except: continue
        
        if bench_data:
            df_bench = pd.DataFrame(bench_data)
            df_bench['Date'] = pd.to_datetime(df_bench['Date'])
            df_bench = df_bench.sort_values('Date')

            last_run = df_bench.iloc[-1]
            efficiency_score = int((last_run['Cadence'] / last_run['Avg_BPM']) * 100) if last_run['Avg_BPM'] > 0 else 0
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1: st.metric("⚙️ Body Efficiency", f"{efficiency_score} Pts", "MBJS Index")
                with c2: st.info(f"🏁 **Last Lap Data:** {last_run['Date'].strftime('%Y-%m-%d')} | 엔진부하 {last_run['Avg_BPM']}bpm | 구동 RPM {last_run['Cadence']}")

            st.write("")
            st.markdown("#### 📟 Telemetry Data Monitor")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**📉 Engine Load (Heart Rate)**") 
                st.altair_chart(alt.Chart(df_bench).mark_line(point=True, color='red').encode(x='Date', y=alt.Y('Avg_BPM', scale=alt.Scale(zero=False))).properties(height=200), use_container_width=True)
                st.markdown("**📈 Engine RPM (Cadence)**") 
                st.altair_chart(alt.Chart(df_bench).mark_line(point=True, color='purple').encode(x='Date', y=alt.Y('Cadence', scale=alt.Scale(zero=False))).properties(height=200), use_container_width=True)
            with c2:
                st.markdown("**📉 Suspension Loss (Vertical Osc.)**") 
                st.altair_chart(alt.Chart(df_bench).mark_line(point=True, color='orange').encode(x='Date', y=alt.Y('Oscillation', scale=alt.Scale(zero=False))).properties(height=200), use_container_width=True)
                st.markdown("**📉 Traction Time (GCT)**") 
                st.altair_chart(alt.Chart(df_bench).mark_line(point=True, color='green').encode(x='Date', y=alt.Y('GCT', scale=alt.Scale(zero=False))).properties(height=200), use_container_width=True)
        else:
            st.info("📡 No Telemetry Data found. (Please initiate a Benchmark Run)")

    except Exception as e: st.error(f"System Error: {e}")

# =========================================================
# [PAGE 3] 📂 Log Archive
# =========================================================
elif page == "📂 Log Archive":
    st.markdown("# 🗂️ Log Archive")
    try:
        sheet = get_db_connection("Action_Log") 
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty:
            reversed_df = df.iloc[::-1]
            with st.container(border=True):
                cat_filter = st.multiselect("🔍 카테고리 필터", reversed_df['Category'].unique())
                if cat_filter: display_df = reversed_df[reversed_df['Category'].isin(cat_filter)]
                else: display_df = reversed_df
                st.dataframe(display_df[['Date', 'Action_Time', 'Category', 'User_Input']], use_container_width=True, hide_index=True)
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 CSV 다운로드", csv, "mbjs_full_log.csv", "text/csv")
        else:
            st.info("데이터가 없습니다.")
    except Exception as e: st.error(f"오류: {e}")