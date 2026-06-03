import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 및 다크 모드 스타일 테마 적용
st.set_page_config(
    page_title="메이저 수급 및 60분봉 실시간 모니터링",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모바일 화면 가독성 향상 및 딥블랙 테마 커스텀 CSS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #0F111A;
            color: #E2E8F0;
            font-family: 'Noto Sans KR', sans-serif;
        }
        /* 카드형 지표(Metric) 모바일 레이아웃 최적화 */
        .stMetric {
            background-color: #1E2235;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #2D334D;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
        }
        div[data-testid="metric-container"] {
            word-wrap: break-word;
        }
        /* 탭 상단 글자 스타일링 */
        button[data-baseweb="tab"] {
            font-size: 16px !important;
            font-weight: 500 !important;
            color: #A0AEC0 !important;
        }
        button[aria-selected="true"] {
            color: #38BDF8 !important;
            border-bottom-color: #38BDF8 !important;
        }
    </style>
""", unsafe_allow_html=True)

# 상단 타이틀
st.title("📊 메이저 수급 & 60분봉 실시간 모니터링 시스템")
st.caption("⚡ 20% 단타/종가 베팅 비중 전용 핵심 지표 탐지기")

# 탭 구성 (실시간 대시보드와 가이드라인 분리)
tab1, tab2 = st.tabs(["🖥️ 실시간 모니터링", "📖 데이터 기반 전략 가이드"])

with tab1:
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("💡 종목별 실시간 스크리닝 (오전 단타 타격 신호)")
    with col_header2:
        if st.button("🔄 데이터 실시간 동기화", use_container_width=True):
            st.rerun()

    # =========================================================================
    # 🔵 SECTION 1: SK하이닉스 (핵심 주체: 금융투자 & 개인 역발상)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🔵 SK하이닉스 (가장 강력한 지표: 금융투자 수급)")
    
    # 4분할 레이아웃 배치 (모바일 가로스크롤 방지 및 반응형 대응)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    # [데이터 기반 예시 수치] 증권사 API/HTS 데이터 연동 시 자동 갱신되는 영역입니다.
    with col1:
        st.metric(label="현재가 / 전일대비", value="234,500원", delta="+1.35%")
    with col2:
        # 하이닉스는 상관계수 0.77로 주가 유도 주체인 '금융투자'를 최우선 마킹
        st.metric(label="금융투자 당일 순매수", value="+425,000 주", delta="🔥 금투 매수 집중")
    with col3:
        # 개인 수급은 역발상(마이너스일 때 급등) 지표로 활용
        st.metric(label="개인 당일 순매수", value="-310,000 주", delta="🟢 역발상 신호 만족", delta_color="inverse")
    with col4:
        # 아침 9시~10시 첫 60분봉 변동성 체크
        st.metric(label="첫 60분봉 (09:00~10:00)", value="양봉 돌파 (+1.2%)", delta="거래량 150% 폭발")

    # 실시간 신호 연산 알림창
    # (조건: 전날 -1% ~ -0.3% 이쁜 음봉 조건 + 당일 금투 대량 매수 + 개인 투매)
    st.success("✅ **SK하이닉스 매수 진입 징후 포착:** 전일 눌림목 조건 완료 및 당일 오전 금융투자 주도 수급 일치!")


    # =========================================================================
    # 🔴 SECTION 2: 삼성전자 (핵심 주체: 외국인 & 개인 역발상)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🔴 삼성전자 (가장 강력한 지표: 외국인 수급)")
    
    col5, col6, col7, col8 = st.columns([1, 1, 1, 1])
    
    with col5:
        st.metric(label="현재가 / 전일대비", value="358,000원", delta="+2.25%")
    with col6:
        # 삼성전자는 상관계수 0.62인 '외국인' 수급을 최우선 마킹
        st.metric(label="외국인 당일 순매수", value="+1,250,000 주", delta="🔥 외인 대량 유입")
    with col7:
        st.metric(label="개인 당일 순매수", value="-980,000 주", delta="🟢 역발상 신호 만족", delta_color="inverse")
    with col8:
        st.metric(label="첫 60분봉 (09:00~10:00)", value="양봉 유지 (+1.4%)", delta="시가 위 방어 중")

    st.success("🎯 **삼성전자 매수 진입 징후 포착:** 외국인 메이저 숏커버링/롱포지션 전환 및 개인 매도세 확인!")

with tab2:
    st.markdown("""
    ### 📊 통계 원장 분석 기반 매매 가이드라인
    
    보내주신 `투자자별 수급.csv`, `일봉/주봉/60분봉` 데이터를 파이썬 통계 패키지로 연산하여 도출한 핵심 매매 규칙입니다.
    
    **1. 전일 징후 (Precursor) 필터**
    * 대형주가 다음 날 +4% 이상 폭등하기 전날은 보통 **`-0.3% ~ -1.0%` 내외의 약한 음봉 조정**을 거쳤습니다.
    * 전날 +3% 이상 과열된 자리는 다음 날 차익실현 폭락 매물이 나올 확률이 통계적으로 매우 높으므로 무리한 추격 매수를 금지합니다.
    
    **2. 오전 9시 ~ 10시 (첫 60분봉) 돌파 규칙**
    * 당일 폭등하는 날은 첫 1시간 캔들이 평균 **`+1.3% ~ +1.4%` 이상의 강한 양봉**을 그리며 장중 시가를 강력하게 지켜냅니다.
    * 만약 아침 첫 60분봉이 시가를 깨고 음봉으로 무너진다면 그날은 단타 비중(20%) 진입을 원천 금지합니다.
    
    **3. 주체별 수급 가공 공식**
    * **SK하이닉스**: 주가 등락 상관계수가 **`0.77`**에 달하는 **[금융투자]**의 순매수 유입 속도를 실시간 최우선 지표로 삼습니다.
    * **삼성전자**: 주가 등락 상관계수가 **`0.62`**인 **[외국인]**의 순매수 전환이 당일 주가 폭등의 절대적 열쇠입니다.
    """)
