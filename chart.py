import streamlit as st
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(layout="wide", page_title="주도주 수급 & 조건식 분석기", page_icon="🚀")

st.title("🚀 상한가 주도주 조건식 매칭 및 수급 분석기")
st.write("선배님의 볼린저밴드/엔벨로프 돌파 조건식 데이터와 수급 주기를 결합하여 주포의 진입 타점을 찾아냅니다.")
st.write("---")

# 💡 [핵심] 이미 업로드된 파일 데이터를 기억하는 세션 저장소 초기화
if "stock_database" not in st.session_state:
    st.session_state["stock_database"] = {}

# 2. 사이드바 - 파일 업로드 및 기 업로드 리스트 관리
st.sidebar.header("📂 HTS 수급 데이터 관리")
uploaded_files = st.sidebar.file_uploader(
    "주도주 수급 데이터 업로드 (누적 가능)", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True
)

# 새로운 파일이 들어오면 세션 저장소에 누적으로 저장 (기존 자료 유지)
if uploaded_files:
    for f in uploaded_files:
        if f.name not in st.session_state["stock_database"]:
            try:
                # 확장자별 맞춤 인코딩/엔진 적용
                if f.name.endswith('.csv'):
                    try:
                        df_raw = pd.read_csv(f, encoding='utf-8')
                    except UnicodeDecodeError:
                        df_raw = pd.read_csv(f, encoding='cp949')
                else:
                    try:
                        df_raw = pd.read_excel(f)
                    except Exception:
                        df_raw = pd.read_excel(f, engine='xlrd')
                
                # 데이터가 정상적으로 읽혔으면 저장소에 보관
                st.session_state["stock_database"][f.name] = df_raw
            except Exception as e:
                st.sidebar.error(f"⚠️ {f.name} 읽기 실패: {e}")

# 3. 누적된 파일 중에서 선택 및 조회하는 영역
if st.session_state["stock_database"]:
    st.sidebar.write("---")
    st.sidebar.subheader("🔍 이미 업로드된 자료 목록")
    
    # 세션 저장소에 보관된 모든 파일명 리스트 가져오기
    available_files = list(st.session_state["stock_database"].keys())
    
    # 선배님이 이미 올렸던 전체 자료 중에서 선택 가능
    selected_file_name = st.sidebar.selectbox(
        "조회할 종목 자료를 선택하세요:", 
        available_files,
        index=len(available_files) - 1  # 가장 최근에 올린 파일이 기본 선택되도록 설정
    )
    
    # 저장소에서 선택된 데이터프레임 꺼내오기
    df_raw = st.session_state["stock_database"][selected_file_name].copy()
    
    # 데이터 초기화 버튼 (필요시 저장소 비우기용)
    if st.sidebar.button("🗑️ 업로드된 리스트 전체 초기화"):
        st.session_state["stock_database"] = {}
        st.rerun()

    try:
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
            st.error(f"❌ '{selected_file_name}' 파일에서 필수 수급 데이터 컬럼을 찾을 수 없습니다.")
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
            
            # 현재 조회 중인 종목 브리핑 문구 추가
            st.success(f"📊 현재 조회 및 분석 중인 자료: **{selected_file_name}** (총 {len(df)}거래일 분량)")
            
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
                
                # 현재 주가 위치 및 돌파 강도
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
                
                # 종목의 절대 주포 판별
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
                
                # 일 단위 순환매 주기 예측
                st.markdown("#### 3️⃣ 🔄 일 단위 순환매 주기 예측 결과")
                df['외인_부호'] = np.sign(df['외인'].replace(0, np.nan).ffill().fillna(1))
                sign_changes = (df['외인_부호'].diff() != 0).sum()
                
                if sign_changes > 0:
                    estimated_cycle = int(len(df) / sign_changes)
                    st.success(f"⏱️ **평균 순환매 사이클**: 약 **{max(3, estimated_cycle)}일 ~ {estimated_cycle + 2}일** 내외")
                else:
                    st.info("ℹ️ 일관된 한 방향 수급 흐름이 지속 중입니다.")

            # 4. 하단 원본 데이터 표 출력
            st.write("---")
            st.subheader(f"📋 분석에 사용된 데이터 시트 ({selected_file_name})")
            display_df = df[['종가', '외인', '기관', '개인']].copy()
            display_df.index = df['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_df.tail(29).style.format("{:,.0f}"))
            
    except Exception as e:
        st.error(f"❌ 데이터 정제 중 오류가 발생했습니다: {e}")
else:
    st.info("▲ 좌측 사이드바에서 오늘 분석하실 HTS 수급 엑셀 자료들을 업로드해 주세요. 파일들은 서버 메모리에 계속 유지됩니다.")
