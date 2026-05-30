import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(layout="wide", page_title="실전 수급&순환매 분석기", page_icon="📊")

st.title("📊 실전 데이터 기반 수급 주체 & 순환매 주기 분석기")
st.write("키움증권 등에서 다운로드한 엑셀 파일을 업로드하여 주가를 움직이는 '진짜 주인'과 수급 주기를 추적합니다.")
st.write("---")

# 2. 사이드바 - 엑셀 파일 업로드 컨트롤러
st.sidebar.header("📂 데이터 파일 관리")
uploaded_file = st.sidebar.file_uploader("종목별 일별 수급 엑셀(XLSX) 또는 CSV 파일 업로드", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 파일 확장자에 맞게 읽기
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        
        # 3. 데이터 전처리 (공백 제거 및 숫자형 변환)
        # 컬럼명 양끝 공백 제거
        df_raw.columns = df_raw.columns.str.strip()
        
        # 분석에 필요한 필수 컬럼 매칭 및 복사
        df = pd.DataFrame()
        df['날짜'] = pd.to_datetime(df_raw['일자'].astype(str).str.strip())
        
        # 천단위 콤마(,) 제거 후  float/int 형변환하는 내부 함수
        def clean_numeric(sequence):
            return pd.to_numeric(sequence.astype(str).str.replace(',', '').str.strip(), errors='coerce')
        
        df['종가'] = clean_numeric(df_raw['종가'])
        df['외인'] = clean_numeric(df_raw['외국인합계'])
        df['기관'] = clean_numeric(df_raw['기관합계'])
        df['개인'] = clean_numeric(df_raw['개인'])
        
        # 날짜 기준 오름차순 정렬 (과거 -> 최신) 후 인덱스 지정
        df = df.sort_values('날짜').reset_index(drop=True)
        df.set_index('날짜', inplace=True)
        
        # 4. 실전 화면 레이아웃 분할 (좌측: 차트, 우측: 계량 수치 분석)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 주가 추이와 세력별 누적 수급 차트")
            
            # 수급 주체별 매수량의 '누적 합계(Cumsum)'를 구해야 거래대금 유입 흐름이 차트상에서 주가와 완벽히 동기화됩니다.
            chart_data = pd.DataFrame()
            chart_data["주가 (Price)"] = df["종가"]
            chart_data["외인 누적수급"] = df["외인"].cumsum()
            chart_data["기관 누적수급"] = df["기관"].cumsum()
            chart_data["개인 누적수급"] = df["개인"].cumsum()
            
            # Streamlit 순정 라인 차트 출력
            st.line_chart(chart_data, height=420)
            st.caption("💡 팁: 마우스 스크롤로 차트를 확대/축소할 수 있으며, 주가선과 누적수급선의 동행성을 시각적으로 확인하세요.")
            
        with col2:
            st.subheader("🎯 데이터가 말해주는 수급의 진실")
            
            # [핵심 수치 1] 상관계수 계산 (Pearson Correlation)
            # 1에 가까울수록 주가를 강하게 끌어올리는 주체, -1에 가까울수록 주가와 정반대로 움직이는 주체
            corr = df.corr()['종가'].drop('종가')
            
            st.write("**1. 이 종목을 움직이는 '진짜 주인' 판별**")
            for actor, val in corr.items():
                if val >= 0.4:
                    label = f"🔥 **주가 견인 주포** (상관관계: +{val:.2f})"
                    color_box = st.success
                elif val <= -0.4:
                    label = f"📉 **물량 떠안는 주체** (상관관계: {val:.2f})"
                    color_box = st.error
                else:
                    label = f"😐 **주가와 무관한 흐름** (상관관계: {val:.2f})"
                    color_box = st.info
                color_box(f"- **{actor}**: {label}")
                
            st.write("---")
            st.write("**2. 순환매 및 세력 엇박자 주기 도출**")
            
            # 외인-기관 수급 전환 주기 연산 (부호가 바뀌는 지점 추적)
            df['외인_부호'] = np.sign(df['외인'])
            sign_changes = (df['외인_부호'].diff() != 0).sum()
            
            if sign_changes > 1:
                estimated_cycle = int(len(df) / sign_changes)
                st.warning(f"🔄 **평균 순환매 턴어라운드 주기**: 약 **{estimated_cycle}일 ~ {estimated_cycle + 3}일**")
                st.write(f"""
                * 현재 업로드된 데이터 기준, 메이저 수급이 들어왔다 나가는 주기적 패턴이 **{estimated_cycle}일** 단위로 포착됩니다.
                * **개인 매수세가 마이너스로 꺾이고, 주가 견인 주포의 누적 수급선이 고개를 들기 시작하는 지점**이 단타 진입의 최적 타이밍(3%~5% 초입)입니다.
                """)
            else:
                st.info("ℹ️ 순환매 주기를 도출하기에는 데이터의 기간이 짧거나 수급 일방통행 흐름이 지속 중입니다.")
                
        # 5. 하단 원본 데이터 프레임 확인
        st.write("---")
        st.subheader("📋 업로드된 엑셀 데이터 분석 셋 (최근 15거래일 정렬)")
        st.dataframe(df[['종가', '외인', '기관', '개인']].tail(15).style.format("{:,.0f}"))
        
    except Exception as e:
        st.error(f"❌ 엑셀 파일을 읽는 중 오류가 발생했습니다. 컬럼명이 이미지와 일치하는지 확인해 주세요. (에러 내용: {e})")

else:
    # 파일이 업로드되지 않았을 때 나오는 초기 대기 화면
    st.info("▲ 왼쪽 사이드바의 [Browse files] 버튼을 눌러 준비된 엑셀 파일을 업로드해 주세요.")
    
    # 시각적 이해를 돕기 위한 대시보드 레이아웃 예시 가이드
    st.markdown("""
    ### 📊 이 툴로 분석하게 될 핵심 포인트 2가지
    
    1. **누적 수급선과 주가의 동행성 확인**
       * 당일 매수/매도량만 보면 노이즈가 심해 흐름이 안 보이지만, 이를 **누적(Cumsum)**하여 선그래프로 그리면 주가 차트와 완벽히 겹쳐지는 '주포의 궤적'이 드러납니다.
    
    2. **상관계수(Correlation)를 이용한 세력 구별**
       * 외인이 살 때 주가가 올라갔다면 외인의 상관계수가 `+0.6` 이상으로 치솟습니다. 반대로 개인이 살 때 주가가 빠졌다면 개인의 상관계수가 `-0.5` 이하로 떨어집니다. 이를 통해 장중에 어떤 주체의 호가창 유입을 추종해야 하는지 명확한 아군과 적군이 구별됩니다.
    """)
