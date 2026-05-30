import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 (와이드 모드 및 다크 모드 최적화)
st.set_page_config(layout="wide", page_title="마스터 수급&순환매 분석기", page_icon="📈")

st.title("📈 수급 주체별 매수량 & 주가 변동 및 순환매 분석기")
st.write("엑셀 데이터를 기반으로 주가 상승을 견인하는 핵심 수급 주체를 찾아내고, 순환매 주기를 도출합니다.")
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
        
        # 컬럼명 공백 제거 및 통일
        df_raw.columns = df_raw.columns.astype(str).str.replace(' ', '').str.strip()
        raw_cols = df_raw.columns.tolist()
        
        # 유연한 컬럼 매칭 기능
        def find_column(keywords):
            for col in raw_cols:
                if any(kw in col for kw in keywords):
                    return col
            return None

        date_col = find_column(['일자', '날짜', 'Date'])
        close_col = find_column(['종가', 'Price', '현재가'])
        foreign_col = find_column(['외국인', '외인', 'Foreign'])
        inst_col = find_column(['기관', 'Institution'])
        retail_col = find_column(['개인', '개인합계', 'Retail'])

        # 필수 컬럼 검증
        missing = [name for name, col in [('일자', date_col), ('종가', close_col), ('외국인', foreign_col), ('기관', inst_col), ('개인', retail_col)] if not col]

        if missing:
            st.error(f"❌ 엑셀 파일에서 다음 필수 항목을 찾을 수 없습니다: {', '.join(missing)}")
            st.info(f"현재 엑셀의 항목 이름들: {raw_cols}")
        else:
            # 데이터 정제 전용 데이터프레임 생성
            df = pd.DataFrame()
            df['날짜'] = pd.to_datetime(df_raw[date_col].astype(str).str.replace(' ', '').str.strip())
            
            # 콤마 및 문자 제거 후 숫자 형변환
            def clean_numeric(sequence):
                return pd.to_numeric(sequence.astype(str).str.replace(',', '').str.replace(' ', '').str.strip(), errors='coerce').fillna(0)
            
            df['종가'] = clean_numeric(df_raw[close_col])
            df['외인'] = clean_numeric(df_raw[foreign_col])
            df['기관'] = clean_numeric(df_raw[inst_col])
            df['개인'] = clean_numeric(df_raw[retail_col])
            
            # 💡 [정렬 에러 방지] 날짜를 기준으로 과거에서 최신순으로 완벽하게 재정렬 (누적 차트 왜곡 방지)
            df = df.sort_values('날짜').reset_index(drop=True)
            df.set_index('날짜', inplace=True)
            
            # 3. 화면 레이아웃 분할 (좌측: 차트, 우측: 수치 분석)
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 주가 변동과 주체별 수급 추이 (시각화)")
                
                # 수급의 영속적인 에너지를 보기 위해 누적합(Cumsum) 적용
                chart_df = pd.DataFrame()
                chart_df["주가 (Price)"] = df["종가"]
                chart_df["외인 누적수급"] = df["외인"].cumsum()
                chart_df["기관 누적수급"] = df["기관"].cumsum()
                chart_df["개인 누적수급"] = df["개인"].cumsum()
                
                # 라인 차트 출력
                st.line_chart(chart_df, height=400)
                st.caption("※ 주가(선)의 꼭짓점과 각 수급 주체(선)의 피크(Peak) 구간이 일치하는 지점을 추적하세요.")
                
            with col2:
                st.subheader("🔍 순환매 및 수급 통계 분석")
                
                # 주가와 수급 주체 간 상관계수 산출
                corr = df[['종가', '외인', '기관', '개인']].corr()['종가'].drop('종가')
                
                st.write("**1. 주가 견인 주체 판별 (상관계수)**")
                for actor, val in corr.items():
                    if val >= 0.4:
                        status = f"🔥 강력한 주가 견인 세력 (+{val:.2f})"
                        color_box = st.success
                    elif val <= -0.4:
                        status = f"📉 이 주체가 사면 주가 하락 ({val:.2f})"
                        color_box = st.error
                    else:
                        status = f"😐 주가와 무관함 ({val:.2f})"
                        color_box = st.info
                    color_box(f"- **{actor}**: {status}")
                    
                st.write("---")
                st.write("**2. 순환매 주기 및 패턴 매칭**")
                
                # 💡 [ZeroDivisionError 방어 로직] 수급 부호 전환 일수를 안전하게 연산
                df['외인_부호'] = np.sign(df['외인'].replace(0, np.nan).ffill().fillna(1))
                sign_changes = (df['외인_부호'].diff() != 0).sum()
                
                # 전환 횟수가 0이 아닐 때만 주기를 계산하여 나눗셈 에러 원천 차단
                if sign_changes > 0:
                    estimated_cycle = int(len(df) / sign_changes)
                    # 현실적인 주식 시장의 매매 템포 반영 (최소 3일 이상일 때 의미 부여)
                    if estimated_cycle >= 1:
                        st.success(f"🔄 **예상 순환매 사이클**: 약 **{max(3, estimated_cycle)}일 ~ {estimated_cycle + 5}일** 주기")
                    else:
                        st.info("ℹ️ 현재 데이터 구간에서는 단기 수급 노이즈가 강해 명확한 메이저 순환 주기가 정형화되지 않습니다.")
                else:
                    st.info("ℹ️ 일관된 수급 흐름(연속 매수 또는 연속 매도)이 지속되어 순환 주기를 산출할 분기점이 없습니다.")
                
                st.write("""
                * **데이터 해석 가이드**:
                    * 일반적으로 개인이 매수세를 멈추고 **외인이나 기관의 누적 수급선이 바닥을 치고 턴어라운드하는 시점**이 주가가 본격적으로 폭발하는 상한가 레이스 초입 타점이 됩니다.
                """)

            # 4. 하단 원본 데이터 표 출력
            st.write("---")
            st.subheader("📋 분석에 사용된 원본 데이터 셋 (최근 15거래일)")
            st.dataframe(df[['종가', '외인', '기관', '개인']].tail(15).style.format("{:,.0f}"))
            
    except Exception as e:
        st.error(f"❌ 데이터를 분석하는 과정에서 에러가 발생했습니다: {e}")

else:
    # 초기 파일 미업로드 시 가이드 화면
    st.info("▲ 왼쪽 사이드바의 [Browse files] 버튼을 눌러 준비된 엑셀 파일을 업로드해 주세요.")
    st.markdown("""
    ### 📊 이 툴로 분석하게 될 핵심 포인트 2가지
    1. **누적 수급선과 주가의 동행성 확인**
       * 당일 매수/매도량만 보면 노이즈가 심해 흐름이 안 보이지만, 이를 **누적(Cumsum)**하여 선그래프로 그리면 주가 차트와 완벽히 겹쳐지는 '주포의 궤적'이 드러납니다.
    2. **상관계수(Correlation)를 이용한 세력 구별**
       * 외인이 살 때 주가가 올라갔다면 외인의 상관계수가 `+0.6` 이상으로 치솟습니다. 반대로 개인이 살 때 주가가 빠졌다면 개인의 상관계수가 `-0.5` 이하로 떨어집니다. 이를 통해 장중에 어떤 주체의 호가창 유입을 추종해야 하는지 명확한 아군과 적군이 구별됩니다.
    """)
