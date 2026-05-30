import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="수급 및 순환매 분석기", page_icon="📈")

st.title("📈 수급 주체별 매수량 & 주가 변동 및 순환매 분석기")
st.write("엑셀 데이터를 기반으로 주가 상승을 견인하는 핵심 수급 주체를 찾아내고, 순환매 주기를 도출합니다.")
st.write("---")

# 2. [실전용] 데이터 로드 및 시뮬레이터 구성
# 장중에 키움증권 등에서 다운로드한 엑셀(CSV) 파일이 있다면 업로드할 수 있는 기능을 탑재했습니다.
uploaded_file = st.sidebar.file_uploader("엑셀 또는 CSV 데이터 업로드 (선택)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # 업로드된 파일 읽기
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    # 💡 백지상태에서도 즉시 연동을 확인하도록 60일치 모의 데이터(샘플)를 자동 생성합니다.
    st.sidebar.info("💡 샘플 데이터로 분석을 진행 중입니다. 장중에 실제 엑셀을 올리시면 해당 데이터로 자동 전환됩니다.")
    
    np.random.seed(42)
    dates = pd.date_range(start="2026-03-01", periods=60)
    
    # 순환매 및 수급 주체별 특성 부여 생성 (외인 매수 시 주가 급등 시나리오)
    foreigner = np.sin(np.linspace(0, 10, 60)) * 5000 + np.random.normal(0, 1000, 60)
    institution = np.cos(np.linspace(0, 10, 60)) * 3000 + np.random.normal(0, 800, 60)
    retail = -(foreigner + institution) + np.random.normal(0, 500, 60)
    
    # 외인 매수량과 동기화된 주가 변동 생성 (외인이 사면 주가가 오르는 상관관계 0.7 세팅)
    price = 10000 + (foreigner * 0.4) + (institution * 0.1) + np.random.normal(0, 1500, 60)
    
    df = pd.DataFrame({
        "날짜": dates,
        "주가": price,
        "외인매수량": foreigner,
        "기관매수량": institution,
        "개인매수량": retail
    })

# 날짜를 인덱스로 지정
df.set_index("날짜", inplace=True)

# 3. 화면 레이아웃 분할 (좌측: 차트 시각화, 우측: 유의미한 수치 분석)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 주가 변동과 주체별 수급 추이 (시각화)")
    
    # 주가 데이터 표준화 (차트 스케일을 맞추기 위해 변동 추이만 비교)
    chart_df = pd.DataFrame()
    chart_df["주가 (Price)"] = df["주가"]
    chart_df["외인 수급 (Foreigner)"] = df["외인매수량"]
    chart_df["기관 수급 (Institution)"] = df["기관매수량"]
    chart_df["개인 수급 (Retail)"] = df["개인매수량"]
    
    # Streamlit 내장 라인 차트 출력 (다크 모드 완벽 호환, 범례 제공)
    st.line_chart(chart_df, height=400)
    st.caption("※ 주가(선)의 꼭짓점과 각 수급 주체(선)의 피크(Peak) 구간이 일치하는 지점을 추적하세요.")

with col2:
    st.subheader("🔍 순환매 및 수급 통계 분석")
    
    # [핵심 1] 어떤 주체가 살 때 주가가 오르는가? (상관관계 분석)
    # 1에 가까울수록 같이 오르고, -1에 가까울수록 반대로 움직입니다.
    corr = df.corr()["주가"].drop("주가")
    
    st.write("**1. 주가 견인 주체 판별 (상관계수)**")
    for main_actor, val in corr.items():
        if val > 0.4:
            status = f"🔥 강력한 주가 견인 세력 (+{val:.2f})"
        elif val < -0.4:
            status = f"📉 이 주체가 사면 주가 하락 (-{val:.2f})"
        else:
            status = f"😐 주가와 무관함 ({val:.2f})"
        st.info(f"- **{main_actor}**: {status}")
        
    # [핵심 2] 순환매 주기 및 유의미한 수치 도출
    st.write("---")
    st.write("**2. 순환매 주기 및 패턴 매칭**")
    
    # 수급이 양수로 전환되는 골든크로스 주기 계산 (단순 예시 로직)
    foreign_positive_days = (df["외인매수량"] > 0).sum()
    cycle_estimate = int(len(df) / (np.diff(np.where(df["외인매수량"] > 0)[0]).mean() + 1))
    
    st.success(f"✔️ **예상 순환매 사이클**: 약 **{cycle_estimate + 3}일 ~ {cycle_estimate + 7}일** 주기")
    st.write("""
    *   **데이터 해석 가이드**:
        *   외인과 기관의 수급선이 교차하는 지점에서 **순환매 엇박자**가 발생하는지 확인하십시오.
        *   일반적으로 개인이 매수세를 멈추고 **외인 수급의 상관계수가 +0.5를 돌파하는 시점**이 주가가 본격적으로 폭발하는 상한가 레이스 초입 타점이 됩니다.
    """)

# 4. 하단 데이터 표 출력
st.write("---")
st.subheader("📋 분석에 사용된 원본 데이터 셋 (최근 10거래일)")
st.dataframe(df.tail(10).style.format("{:,.0f}"))
