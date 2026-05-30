import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정
st.set_page_config(layout="wide", page_title="실전 수급&순환매 분석기", page_icon="📊")

st.title("📊 실전 데이터 기반 수급 주체 & 순환매 주기 분석기")
st.write("엑셀 파일을 업로드하여 주가를 움직이는 '진짜 주인'과 수급 주기를 추적합니다.")
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
        
        # 💡 [에러 해결핵심] 컬럼명 전처리: 모든 공백을 제거하고 특수문자를 날려 매칭 확률을 높입니다.
        df_raw.columns = df_raw.columns.astype(str).str.replace(' ', '').str.strip()
        raw_cols = df_raw.columns.tolist()
        
        # 유연한 컬럼 매칭 함수
        def find_column(keywords, default_name):
            for col in raw_cols:
                if any(kw in col for kw in keywords):
                    return col
            return None

        # 엑셀 시트에서 유기적으로 컬럼 찾기
        date_col = find_column(['일자', '날짜', 'Date'], '일자')
        close_col = find_column(['종가', 'Price', '현재가'], '종가')
        foreign_col = find_column(['외국인', '외인', 'Foreign'], '외국인합계')
        inst_col = find_column(['기관', 'Institution'], '기관합계')
        retail_col = find_column(['개인', '개인합계', 'Retail'], '개인')

        # 필수 컬럼 검증
        missing = []
        if not date_col: missing.append('일자(날짜)')
        if not close_col: missing.append('종가')
        if not foreign_col: missing.append('외국인합계')
        if not inst_col: missing.append('기관합계')
        if not retail_col: missing.append('개인')

        if missing:
            st.error(f"❌ 엑셀 파일에서 다음 필수 항목을 찾을 수 없습니다: {', '.join(missing)}")
            st.info(f"현재 엑셀의 항목 이름들: {raw_cols}")
        else:
            # 데이터 정제 및 이관
            df = pd.DataFrame()
            df['날짜'] = pd.to_datetime(df_raw[date_col].astype(str).str.replace(' ', '').str.strip())
            
            # 콤마 제거 및 숫자 형변환 함수
            def clean_numeric(sequence):
                return pd.to_numeric(sequence.astype(str).str.replace(',', '').str.replace(' ', '').str.strip(), errors='coerce')
            
            df['종가'] = clean_numeric(df_raw[close_col])
            df['외인'] = clean_numeric(df_raw[foreign_col])
            df['기관'] = clean_numeric(df_raw[inst_col])
            df['개인'] = clean_numeric(df_raw[retail_col])
            
            # 결측치 정제 및 정렬
            df = df.dropna(subset=['종가']).sort_values('날짜').reset_index(drop=True)
            df.set_index('날짜', inplace=True)
            
            # 3. 화면 레이아웃 분할
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📈 주가 추이와 세력별 누적 수급 차트")
                
                # 수급의 연속성을 보기 위한 누적 수급 계산
                chart_data = pd.DataFrame()
                chart_data["주가 (Price)"] = df["종가"]
                chart_data["외인 누적수급"] = df["외인"].cumsum()
                chart_data["기관 누적수급"] = df["기관"].cumsum()
                chart_data["개인 누적수급"] = df["개인"].cumsum()
                
                # 차트 가시성을 높이기 위해 주가와 수급을 스케일링(0~1)해서 추세 동행성 비교
                # 원본 값으로 보고 싶다면 바로 st.line_chart(chart_data)를 쓰셔도 됩니다.
                st.line_chart(chart_data, height=420)
                st.caption("💡 주가선과 특정 세력의 누적수급선이 일치하여 움직이는지 궤적을 추적하세요.")
                
            with col2:
                st.subheader("🎯 데이터가 말해주는 수급의 진실")
                
                # 주가와 수급 주체 간의 상관계수 계산
                corr = df[['종가', '외인', '기관', '개인']].corr()['종가'].drop('종가')
                
                st.write("**1. 이 종목을 움직이는 '진짜 주인' 판별**")
                for actor, val in corr.items():
                    if val >= 0.35:
                        label = f"🔥 **주가 견인 주포** (상관관계: +{val:.2f})"
                        color_box = st.success
                    elif val <= -0.35:
                        label = f"📉 **물량 떠안는 주체** (상관관계: {val:.2f})"
                        color_box = st.error
                    else:
                        label = f"😐 **주가와 무관한 흐름** (상관관계: {val:.2f})"
                        color_box = st.info
                    color_box(f"- **{actor}**: {label}")
                    
                st.write("---")
                st.write("**2. 순환매 및 세력 엇박자 주기 도출**")
                
                # 외인 수급이 플러스/마이너스로 전환되는 주기 계산
                df['외인_부호'] = np.sign(df['외인'])
                sign_changes = (df['외인_부호'].diff() != 0).sum()
                
                if sign_changes > 1:
                    estimated_cycle = int(len(df) / sign_changes)
                    st.warning(f"🔄 **평균 순환매 턴어라운드 주기**: 약 **{estimated_cycle}일 ~ {estimated_cycle + 3}일**")
                    st.write(f"""
                    * 현재 데이터 기준, 주포의 자금이 유입되었다가 유출되는 순환매 호흡이 약 **{estimated_cycle}일** 단위로 감지됩니다.
                    * **순환매 꿀팁:** 주포의 누적수급선이 바닥을 다지고 우상향으로 꺾이는 첫 번째 날(3%~5% 초입)이 거래대금 분출 전 최적의 매수 길목입니다.
                    """)
                else:
                    st.info("ℹ️ 순환매 주기를 도출하기에는 수급의 일방통행(연속 매수/매도) 흐름이 지속 중입니다.")
                    
            # 4. 하단 원본 데이터 프레임 확인
            st.write("---")
            st.subheader("📋 분석에 사용된 데이터 시트 (최근 15거래일)")
            st.dataframe(df[['종가', '외인', '기관', '개인']].tail(15).style.format("{:,.0f}"))
            
    except Exception as e:
        st.error(f"❌ 데이터 처리 중 예기치 못한 에러가 발생했습니다: {e}")

else:
    st.info("▲ 왼쪽 사이드바의 [Browse files] 버튼을 눌러 준비된 엑셀 파일을 업로드해 주세요.")
    st.markdown("""
    ### 📊 이 툴로 분석하게 될 핵심 포인트
    1. **누적 수급선 추적:** 단발성 매수량이 아닌, 연속성 있게 자금을 투입하는 주포의 흔적을 추적합니다.
    2. **상관계수 매칭:** 세력이 살 때 주가가 진짜 오르는지, 아니면 세력이 사는데도 주가가 밀리는 '가짜 수급'인지를 수학적으로 발라냅니다.
    """)
