import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정
st.set_page_config(layout="wide", page_title="주도주 수급 & 조건식 분석기", page_icon="🚀")

st.title("🚀 상한가 주도주 조건식 매칭 및 수급 분석기")
st.write("선배님의 볼린저밴드/엔벨로프 돌파 조건식 데이터와 수급 주기를 결합하여 주포의 진입 타점을 찾아냅니다.")
st.write("---")

# 2. 사이드바 - 파일 업로드
st.sidebar.header("📂 HTS 수급 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("단일 종목의 일별 수급 데이터 (XLSX / CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 확장자별 맞춤 인코딩/엔진 적용
        if uploaded_file.name.endswith('.csv'):
            try:
                df_raw = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                df_raw = pd.read_csv(uploaded_file, encoding='cp949')
        else:
            try:
                df_raw = pd.read_excel(uploaded_file)
            except Exception:
                df_raw = pd.read_excel(uploaded_file, engine='xlrd')
        
        # 컬럼명 공백 제거
        df_raw.columns = df_raw.columns.astype(str).str.replace(' ', '').str.strip()
        raw_cols = df_raw.columns.tolist()
        
        # 유연한 컬럼 매칭
        def find_column(keywords):
            for col in raw_cols:
                if any(kw in col for kw in keywords):
                    return col
            return None

        date_col = find_column(['일자', '날짜', 'Date'])
        close_col = find_column(['종가', 'Price', '현재가', '현재값'])
        foreign_col = find_column(['외국인', '외인', 'Foreign'])
        inst_col = find_column(['기관', 'Institution'])
        retail_col = find_column(['개인', 'Retail'])
        volume_col = find_column(['거래량', 'Volume'])

        if not all([date_col, close_col, foreign_col, inst_col, retail_col]):
            st.error("❌ 필수 수급 데이터 컬럼(일자, 종가, 외인, 기관, 개인)을 파일에서 찾을 수 없습니다.")
            st.info(f"현재 파일 내 존재하는 컬럼 항목들: {raw_cols}")
        else:
            # 데이터 정제
            df = pd.DataFrame()
            df['날짜'] = pd.to_datetime(df_raw[date_col].astype(str).str.replace(' ', '').str.strip(), errors='coerce')
            
            def clean_numeric(sequence):
                return pd.to_numeric(sequence.astype(str).str.replace(',', '').str.replace(' ', '').str.strip(), errors='coerce').fillna(0)
            
            df['종가'] = clean_numeric(df_raw[close_col])
            df['외인'] = clean_numeric(df_raw[foreign_col])
            df['기관'] = clean_numeric(df_raw[inst_col])
            df['개인'] = clean_numeric(df_raw[retail_col])
            if volume_col:
                df['거래량'] = clean_numeric(df_raw[volume_col])
            
            # 날짜 정렬 및 결측치 제거
            df = df.dropna(subset=['날짜', '종가']).sort_values('날짜').reset_index(drop=True)
            df.set_index('날짜', inplace=True)
            
            # 3. 레이아웃 배치
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 주가 추이와 주체별 누적 수급 궤적")
                chart_df = pd.DataFrame()
                chart_df["주가 (Price)"] = df["종가"]
                chart_df["외인 누적수급"] = df["외인"].cumsum()
                chart_df["기관 누적수급"] = df["기관"].cumsum()
                chart_df["개인 누적수급"] = df["개인"].cumsum()
                
                st.line_chart(chart_df, height=400)
                st.caption("💡 Tip: 특정 주체의 누적수급선이 주가선과 평행을 이루며 같이 뻗어나가는지 확인하세요.")
                
            with col2:
                st.subheader("🔍 실전 매매 수급 분석창")
                
                # 상관계수 계산
                corr = df[['종가', '외인', '기관', '개인']].corr()['종가'].drop('종가')
                
                st.write("**1. 종목의 절대 주포(세력) 판별**")
                for actor, val in corr.items():
                    if val >= 0.4:
                        st.success(f"🔥 **{actor}**: 주가를 밀어 올리는 주포 (+{val:.2f})")
                    elif val <= -0.4:
                        st.error(f"📉 **{actor}**: 고점 물량 떠안는 주체 ({val:.2f})")
                    else:
                        st.info(f"😐 **{actor}**: 주가 변동과 무관함 ({val:.2f})")
                
                st.write("---")
                st.write("**2. 순환매 주기 예측 결과**")
                
                df['외인_부호'] = np.sign(df['외인'].replace(0, np.nan).ffill().fillna(1))
                sign_changes = (df['외인_부호'].diff() != 0).sum()
                
                if sign_changes > 0:
                    estimated_cycle = int(len(df) / sign_changes)
                    st.success(f"🔄 **평균 순환매 사이클**: 약 **{max(3, estimated_cycle)}일 ~ {estimated_cycle + 4}일** 내외")
                    st.caption("수급이 빠졌다가 다시 거래대금을 붙이며 조건식(볼린저밴드 상한선)을 재돌파하는 최적의 림보 주기입니다.")
                else:
                    st.info("ℹ️ 연속적인 수급 유입으로 일정한 순환 분기점이 없습니다.")
                    
                # 💡 [보너스 기능] 기술적 조건식 강도 자동 계산 (볼린저밴드 20,2 대용 로직)
                st.write("---")
                st.write("**3. ⚡ 현재 주가 위치 및 돌파 강도**")
                if len(df) >= 20:
                    ma20 = df['종가'].rolling(20).mean()
                    std20 = df['종가'].rolling(20).std()
                    upper_bb = ma20 + (2 * std20)
                    
                    current_close = df['종가'].iloc[-1]
                    current_bb = upper_bb.iloc[-1]
                    
                    if current_close >= current_bb:
                        st.warning(f"💥 **볼린저밴드(20,2) 상한선 돌파 상태!**")
                        st.caption(f"현재가({current_close:,.0f}원)가 상한선({current_bb:,.0f}원) 위에 안착하여 조건식 강도가 매우 강합니다.")
                    else:
                        st.info(f"정상 밴드 내 횡보 중 (상한선 저항대: {current_bb:,.0f}원)")

            # 4. 하단 원본 데이터 표 출력
            st.write("---")
            st.subheader("📋 분석에 사용된 데이터 시트 (최근 15거래일)")
            st.dataframe(df[['종가', '외인', '기관', '개인']].tail(15).style.format("{:,.0f}"))
            
    except Exception as e:
        st.error(f"❌ 엑셀 구조 분석 중 예기치 못한 에러가 발생했습니다: {e}")
else:
    st.info("▲ 단일 종목의 깨끗한 엑셀 또는 HTS CSV 파일을 좌측 사이드바에 올려주세요.")
