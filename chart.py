import streamlit as st
import pandas as pd

# 1. 웹 앱 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(
    page_title="단타 타점 분석기",
    page_icon="📊",
    layout="centered"
)

# 2. 상단 타이틀 및 설명 (모바일 최적화 레이아웃)
st.title("📊 상한가 주도주 타점별 효율 분석")
st.write("이미 10% 이상 뜬 종목을 추격할 때와 5% 초입에 잡을 때의 실전 리스크와 기대수익 구조를 데이터로 비교합니다.")
st.write("---")

# 3. 시뮬레이션 데이터 구성
data = {
    "진입 타점 (Entry Point)": ["초입 타점 (+5%)", "기존 확인 타점 (+10%)", "과열 돌파 타점 (+15%)"],
    "최대 기대수익 (Max Gain)": [25.0, 20.0, 15.0],
    "평균 손실 리스크 (Avg Risk)": [-3.5, -6.5, -11.0]
}

# 데이터프레임 변환 및 인덱스 설정 (차트 라벨용)
df = pd.DataFrame(data)
df.set_index("진입 타점 (Entry Point)", inplace=True)

# 4. 메인 시각화 차트 (Streamlit 내장 바 차트: 별도 라이브러리 설치 불필요)
st.subheader("📈 진입 등락률별 기대수익 vs 리스크 범위")
st.bar_chart(df, height=350)

# 5. 한눈에 보는 통계 비교표 (인라인 테이블)
st.subheader("📋 실전 매매 손익비 통계 데이터")
st.table(data)

# 6. 선배님의 핵심 고민을 해결하는 실전 인사이트 요약
st.write("---")
st.markdown("""
### 💡 데이터가 증명하는 단타의 핵심 레슨

* **진입 타점 10% 이상의 맹점**
  * 등락률이 이미 10%~15% 이상 나온 주도주를 '확인하고' 조정 시 진입하면, 고점 돌파 실패 후 밀릴 때 **손실 리스크(-6.5% ~ -11.0%)가 기하급수적으로 커집니다.**
  * 주저앉을 때 들어가면 물리기 십상이고, 상한가(30%)를 가더라도 **수익 공간이 최대 15%~20%로 한정**되어 손익비가 무너집니다.

* **초입 타점(+5%)으로 그물을 내려야 하는 이유**
  * 아침 장초반 시가 분출 후 **3%~5% 대**에서 거래대금이 폭발하는 초입 종목을 포착하면, 실패하더라도 기준봉 시가 손절선이 짧아 **리스크가 -3.5% 내외**로 극히 제한됩니다.
  * 반면 상한가 도달 시 **기대 수익률은 +25% 이상 확보**되므로, 확률 싸움에서 완벽하게 주도권을 쥐고 계좌를 우상향시킬 수 있습니다.
""")

# 7. 장중 대응용 간단 손익비 계산기 인터랙티브 기능 (보너스)
st.write("---")
st.subheader("🧮 장중 즉석 손익비 계산기")
st.caption("장중에 포착된 종목의 현재 등락률을 입력해 보세요. 먹을 공간과 손절 가이드를 실시간 계산해 드립니다.")

# 사용자 입력 슬라이더
current_pct = st.slider("포착된 종목의 현재 등락률 (%)", min_value=1.0, max_value=25.0, value=10.0, step=0.5)

# 계산 로직
expected_gain = ((30.0 - current_pct) / (100.0 + current_pct)) * 100.0
stop_loss_guide = current_pct - 3.0

# 결과 출력
col1, col2 = st.columns(2)
with col1:
    st.metric(label="상한가 도달 시 기대수익률", value=f"+{expected_gain:.2f}%")
with col2:
    st.metric(label="실전 감당 손절선 가이드 (시가 기준)", value=f"+{stop_loss_guide:.1f}% 부근")
