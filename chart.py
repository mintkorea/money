import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 (와이드 모드)
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

        if not all([date_col, close_col, foreign_col, inst_col, retail_col]):
            st.error("❌ 필수 수급 데이터 컬럼(일자, 종가, 외인, 기관, 개인)을 파일에서 찾을 수 없습니다.")
            st.info(f"현재 파일 내 존재하는 컬럼 항목들: {raw_cols}")
        else:
            df = pd.DataFrame()
            
            # [날짜 정밀 보정] 엑셀 날짜 꼬임 원천 차단 알고리즘
            raw_date_series = df_raw[date_col]
            parsed_dates = pd.to_datetime(raw_date_series, errors='coerce')
            
            if parsed_dates.isna().any() or (parsed_dates.dt.year != 2026).any():
                corrected_dates = []
                for idx, val in enumerate(raw_date_series):
                    val_str = str(val).strip().replace('/', '').replace('-', '')
                    if len(val_str) in [6, 8, 10] or '26' in val_str:
                        clean_d = ''.join(filter(str.isdigit, val_str))
                        if len(clean_d) == 6:
                            y, m, d = "20" + clean_d[0:2], clean_d[2:4], clean_d[4:6]
                        elif len(clean_d) == 8:
                            y, m, d = clean_d[0:4], clean_d[4:6], clean_d[6:8]
                        else:
                            y, m, d = "2026", "05", "29"
                        corrected_dates.append(pd.to_datetime(f"{y}-{m}-{d}", errors='coerce'))
                    else:
                        try:
                            current_dt = pd.to_datetime(val)
                            y = "20" + str(current_dt.day)
                            m = f"{current_dt.month:02d}"
                            d = f"{str(current_dt.year)[2:4]}"
                            corrected_dates.append(pd.to_datetime(f"{y}-{m}-{d}", errors='coerce'))
                        except:
                            corrected_dates.append(pd.NaT)
                df['날짜'] = corrected_dates
            else:
                df['날짜'] = parsed_dates
                
            def clean_numeric(sequence):
                return pd.to_numeric(sequence.astype(str).str.replace(',', '').str.replace(' ', '').str.strip(), errors='coerce').fillna(0)
            
            df['종가'] = clean_numeric(df_raw[close_col])
            df['외인'] = clean_numeric(df_raw[foreign_col])
            df['기관'] = clean_numeric(df_raw[inst_col])
            df['개인'] = clean_numeric(df_raw[retail_col])
            
            # 날짜 정렬
            df = df.dropna(subset=['날짜', '종가']).sort_values('날짜').reset_index(drop=True)
            
            # 누적 수급 계산
            df['외인 누적수급'] = df['외인'].cumsum()
            df['기관 누적수급'] = df['기관'].cumsum()
            df['개인 누적수급'] = df['개인'].cumsum()
            
            # X축 레이블 고정
            df['일자표시'] = df['날짜'].dt.strftime('%m/%d')
            
            # 3. 레이아웃 분할 (좌측 차트 / 우측 실시간 전략창)
            col1, col2 = st.columns([1.8, 1.2])
            
            with col1:
                st.markdown("### 📈 [차트] 일 단위 주가 변동 및 누적 수급 에너지")
                
                st.write("**[상단 정보] 일별 종가 (Price) 추이**")
                price_chart = df.set_index('일자표시')[['종가']]
                st.line_chart(price_chart, height=220)
                
                st.write("**[하단 정보] 세력 vs 개인 누적 수급 트랙 (단위: 주)**")
                supply_chart = df.set_index('일자표시')[['외인 누적수급', '기관 누적수급', '개인 누적수급']]
                st.line_chart(supply_chart, height=280)
                
                st.caption("💡 차트 연계 판독법: 상단 종가가 직전 고점을 뚫는 순간, 하단 수급창에서 외인/기관선이 동반 수직 상승하는지 체크하세요.")
                
            with col2:
                st.markdown("### 🎯 [전략] 실전 매매 수급 분석창")
                
                # ----------------------------------------------------
                # [위치 교환 1순위] 현재 주가 위치 및 돌파 강도 (최상단 배치)
                # ----------------------------------------------------
                st.markdown("#### 1️⃣ ⚡ 현재 주가 위치 및 조건식 돌파 강도")
                if len(df) >= 5:
                    window_size = min(20, len(df))
                    ma = df['종가'].rolling(window_size).mean()
                    std = df['종가'].rolling(window_size).std()
                    upper_bb = ma + (2 * std)
                    
                    current_close = df['종가'].iloc[-1]
                    current_bb = upper_bb.iloc[-1] if not np.isnan(upper_bb.iloc[-1]) else current_close
                    
                    if current_close >= current_bb and current_bb > 0:
                        st.error(f"💥 **볼린저밴드 상한선 돌파 상태! (매수세 최강)**")
                        st.markdown(f"* **현재가:** `{current_close:,.0f}원`  \n* **상한선 저항대:** `{current_bb:,.0f}원` (상한선 위에서 시세 분출 중)")
                    else:
                        st.info(f"🔍 **정상 밴드 내 매물 소화 중**")
                        st.markdown(f"* **현재가:** `{current_close:,.0f}원`  \n* **상한선 저항대:** `{current_bb:,.0f}원` (상한선 진입 시 돌파 타점)")
                st.write("---")
                
                # ----------------------------------------------------
                # [위치 교환 2순위] 종목의 절대 주포 판별 (중간 배치)
                # ----------------------------------------------------
                st.markdown("#### 2️⃣ 🥇 종목의 절대 주포(세력) 판별")
                corr = df[['종가', '외인', '기관', '개인']].corr()['종가'].drop('종가')
                
                for actor, val in corr.items():
                    if val >= 0.35:
                        st.success(f"🔥 **{actor}** : 주가를 책임지고 밀어 올리는 주포 (+{val:.2f})")
                    elif val <= -0.35:
                        st.warning(f"📉 **{actor}** : 고점 물량 받아내며 밀리는 주체 ({val:.2f})")
                    else:
                        st.text(f"😐 {actor} : 주가 변동과 현재 무관함 ({val:.2f})")
                st.write("---")
                
                # ----------------------------------------------------
                # [위치 교환 3순위] 일 단위 순환매 주기 예측 (하단 배치)
                # ----------------------------------------------------
                st.markdown("#### 3️⃣ 🔄 일 단위 순환매 주기 예측 결과")
                df['외인_부호'] = np.sign(df['외인'].replace(0, np.nan).ffill().fillna(1))
                sign_changes = (df['외인_부호'].diff() != 0).sum()
                
                if sign_changes > 0:
                    estimated_cycle = int(len(df) / sign_changes)
                    st.success(f"⏱️ **평균 순환매 사이클**: 약 **{max(3, estimated_cycle)}일 ~ {estimated_cycle + 2}일** 내외")
                    st.caption("수급이 한 턴 빠져나갔다가 조건식 돌파로 재유입되는 평균 숨고르기 호흡입니다.")
                else:
                    st.info("ℹ️ 일관된 한 방향 수급 흐름이 지속 중입니다.")

            # 4. 하단 원본 데이터 표 출력
            st.write("---")
            st.subheader("📋 분석에 사용된 데이터 시트 (최근 거래일 순 정렬)")
            display_df = df[['종가', '외인', '기관', '개인']].copy()
            display_df.index = df['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_df.tail(29).style.format("{:,.0f}"))
            
    except Exception as e:
        st.error(f"❌ 데이터 정제 중 오류가 발생했습니다: {e}")
else:
    st.info("▲ 단일 종목의 깨끗한 엑셀 또는 HTS CSV 파일을 좌측 사이드바에 올려주세요.")
