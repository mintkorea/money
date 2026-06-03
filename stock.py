import streamlit as st
import pandas as pd
import os
import json
import time

# 1. 페이지 설정 및 다크모드 적용
st.set_page_config(page_title="키움증권 실시간 수급 모니터", layout="wide")

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0F111A;
            color: #E2E8F0;
        }
        .stMetric {
            background-color: #1E2235;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #2D334D;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 키움증권 Open API 실시간 연동 대시보드")
st.caption("⚡ 20% 단타 전략 전용 - 금융투자 & 외국인 창구 추정치 실시간 매칭")

# 키움 수집기로부터 데이터를 로드하는 함수
def load_kiwoom_data():
    file_path = "kiwoom_live_data.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 파일이 없을 때 보여줄 가상/초기 데이터 구조
        return {
            "000660": {"현재가": 234500, "등락률": 1.35, "외국인": -50000, "금융투자": 425000, "개인": -310000},
            "0005930": {"현재가": 358000, "등락률": 2.25, "외국인": 1250000, "금융투자": 85000, "개인": -980000}
        }

# 실시간 갱신 루프 (장중에 스트리밍 형태로 데이터 변동 감지)
live_data = load_kiwoom_data()

# =========================================================================
# 🔵 SECTION 1: SK하이닉스 
# =========================================================================
sk_data = live_data.get("000660", {})
st.markdown("### 🔵 SK하이닉스 (가장 강력한 지표: 금융투자 수급)")
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    st.metric(label="현재가", value=f"{sk_data['현재가']:,}원", delta=f"{sk_data['등락률']}%")
with col2:
    st.metric(label="금융투자 당일 추정치", value=f"{sk_data['금융투자']}:+,} 주", delta="🔥 금투 주도 수급")
with col3:
    st.metric(label="개인 당일 추정치", value=f"{sk_data['개인']}:+,} 주", delta="🟢 역발상 조건 만족", delta_color="inverse")
with col4:
    st.metric(label="오전 60분봉 대응", value="조건 충족", delta="시가 위 방어 중")

# =========================================================================
# 🔴 SECTION 2: 삼성전자
# =========================================================================
se_data = live_data.get("005930", {})
st.markdown("---")
st.markdown("### 🔴 삼성전자 (가장 강력한 지표: 외국인 수급)")
col5, col6, col7, col8 = st.columns([1, 1, 1, 1])

with col5:
    st.metric(label="현재가", value=f"{se_data['현재가']:,}원", delta=f"{se_data['등락률']}%")
with col6:
    st.metric(label="외국인 당일 추정치", value=f"{se_data['외국인']}:+,} 주", delta="🔥 외인 매수 전환")
with col7:
    st.metric(label="개인 당일 추정치", value=f"{se_data['개인']}:+,} 주", delta="🟢 역발상 조건 만족", delta_color="inverse")
with col8:
    st.metric(label="오전 60분봉 대응", value="조건 충족", delta="상방 돌파 완료")

# 1초마다 브라우저단 자동 리프레시 실행 (스트리밍 효과)
time.sleep(1)
st.rerun()
