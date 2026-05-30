import streamlit as st
import pandas as pd
import numpy as np
import os

# 1. 페이지 기본 설정 (와이드 모드 및 타이틀)
st.set_page_config(layout="wide", page_title="주도주 수급 & 조건식 분석기", page_icon="🚀")

# 모바일/PC 화면 크기별 제목 폰트 자동 조절 반응형 CSS
st.markdown("""
    <style>
        /* 기본 PC 화면용 폰트 스타일 */
        .responsive-title {
            font-size: 2.2rem !important;
            font-weight: 800;
            line-height: 1.3;
            margin-bottom: 0.5rem;
            color: #1E1E1E;
        }
        .responsive-subtitle {
            font-size: 1.05rem !important;
            color: #808495;
            margin-bottom: 1.5rem;
        }
        
        /* 📱 모바일 화면 (화면 폭 768px 이하) 자동 반응형 대응 */
        @media (max-width: 768px) {
            .responsive-title {
                font-size: 1.35rem !important; /* 스마트폰 환경에 맞춰 폰트 크기 자동 축소 */
                font-weight: 700;
                line-height: 1.2;
                letter-spacing: -0.05rem;
            }
            .responsive-subtitle {
                font-size: 0.85rem !important;
            }
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# 반응형 클래스가 적용된 제목 영역
st.markdown('<div class="responsive-title">🚀 상한가 주도주 조건식 매칭 및 수급 분석기</div>', unsafe_allow_html=True)
st.markdown('<div class="responsive-subtitle">PC에서 등록한 엑셀 수급 자료가 서버에 동기화되어, 휴대폰에서도 실시간 조회가 가능합니다.</div>', unsafe_allow_html=True)
st.write("---")

# 서버 내부 공간에 파일을 저장할 폴더 생성 로직
SERVER_STORE_DIR = "stored_stocks"
if not os.path.exists(SERVER_STORE_DIR):
    os.makedirs(SERVER_STORE_DIR)

# 2. 사이드바 - 파일 업로드 및 서버 저장 관리
st.sidebar.header("📂 [PC용] HTS 수급 데이터 서버 업로드")
uploaded_files = st.sidebar.file_uploader(
    "새로운 주도주 엑셀/CSV 자료를 서버에 등록하세요:", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    for f in uploaded_files:
        file_path = os.path.join(SERVER_STORE_DIR, f.name)
        with open(file_path, "wb") as buffer:
            buffer.write(f.getbuffer())
    st.sidebar.success("✅ 선택한 파일들이 서버 저장소에 안전하게 보관되었습니다!")
    st.rerun()

# 3. 📱 [모바일/PC 공용] 서버에 보관된 전체 목록 가져오기 및 자료 검색
server_files = sorted([fname for fname in os.listdir(SERVER_STORE_DIR) if fname.endswith(('.xlsx', '.csv'))])

if server_files:
    st.sidebar.write("---")
    st.sidebar.subheader("📱 서버 자료 목록 (검색 가능)")
    
    selected_file_name = st.sidebar.selectbox(
        "조회(검색)할 종목을 선택하세요:", 
        server_files,
        index=0
    )
    
    target_file_path = os.path.join(SERVER_STORE_DIR, selected_file_name)
    
    if st.sidebar.button(f"🗑️ 현재 종목({selected_file_name}) 서버에서 삭제"):
        if os.path.exists(target_file_path):
            os.remove(target_file_path)
            st.rerun()

    try:
        # 파일 로드 및 파일 타입별 엔진 최적화
        if selected_file_name.endswith('.csv'):
            try:
                df_raw = pd.read_csv(target_file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df_raw = pd.read_csv(target_file_path, encoding='cp949')
        else:
            try:
                df_raw = pd.read_excel(target_file_path, engine='openpyxl')
            except ImportError:
                try:
                    df_raw = pd.read_excel(target_file_path, engine='xlrd')
                except:
                    df_raw = pd.read_excel(target_file_path)
        
        # 컬럼명 공백 제거 및 전처리
        df_raw.columns = df_raw.columns.astype(str).str.replace(' ', '').str.strip()
        raw_cols = df_raw.columns.tolist()
        
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
        else:
            df = pd.DataFrame()
            
            # 날짜 파싱 정밀 보정
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
            
            df = df.dropna(subset=['날짜', '종가']).sort_values('날짜').reset_index(drop=True)
            
            df['외인 누적수급'] = df['외인'].cumsum()
            df['기관 누적수급'] = df['기관'].cumsum()
            df['개인 누적수급'] = df['개인'].cumsum()
            
            df['일자표시'] = df['날짜'].dt.strftime('%m/%d')
            
            st.success(f"🌐 [서버 연동 데이터] 분석 중: **{selected_file_name}**")
            
            # 레이아웃 분할 (좌측 차트 / 우측 실시간 전략창)
            col1, col2 = st.columns([1.8, 1.2])
            
            with col1:
                st.markdown("### 📈 [차트] 일 단위 주가 및 누적 수급")
                st.write("**[상단 정보] 일별 종가 (Price) 추이**")
                price_chart = df.set_index('일자표시')[['종가']]
                st.line_chart(price_chart, height=220)
                
                st.write("**[하단 정보] 세력 vs 개인 누적 수급 트랙**")
                supply_chart = df.set_index('일자표시')[['외인 누적수급', '기관 누적수급', '개인 누적수급']]
                st.line_chart(supply_chart, height=280)
                
            with col2:
                st.markdown("### 🎯 [전략] 실전 매매 분석창")
                
                st.markdown("#### 1️⃣ ⚡ 현재 주가 위치 및 조건식 돌파 강도")
                if len(df) >= 5:
                    window_size = min(20, len(df))
                    ma = df['종가'].rolling(window_size).mean()
                    std = df['종가'].rolling(window_size).std()
                    upper_bb = ma + (2 * std)
                    
                    current_close = df['종가'].iloc[-1]
                    current_bb = upper_bb.iloc[-1] if not np.isnan(upper_bb.iloc[-1]) else current_close
                    
                    if current_close >= current_bb and current_bb > 0:
                        st.error(f"💥 **볼린저밴드 상한선 돌파 상태!**")
                        st.markdown(f"* **현재가:** `{current_close:,.0f}원` \n* **상한선:** `{current_bb:,.0f}원` (시세 분출 중)")
                    else:
                        st.info(f"🔍 **정상 밴드 내 매물 소화 중**")
                        st.markdown(f"* **현재가:** `{current_close:,.0f}원` \n* **상한선 저항대:** `{current_bb:,.0f}원` ")
                st.write("---")
                
                st.markdown("#### 2️⃣ 🥇 종목의 절대 주포(세력) 판별")
                corr = df[['종가', '외인', '기관', '개인']].corr()['종가'].drop('종가')
                for actor, val in corr.items():
                    if val >= 0.35:
                        st.success(f"🔥 **{actor}** : 주가 견인 주포 (+{val:.2f})")
                    elif val <= -0.35:
                        st.warning(f"📉 **{actor}** : 물량 받아내는 주체 ({val:.2f})")
                    else:
                        st.text(f"😐 {actor} : 현재 무관함 ({val:.2f})")
                st.write("---")
                
                st.markdown("#### 3️⃣ 🔄 일 단위 순환매 주기 예측 결과")
                df['외인_부호'] = np.sign(df['외인'].replace(0, np.nan).ffill().fillna(1))
                sign_changes = (df['외인_부호'].diff() != 0).sum()
                if sign_changes > 0:
                    estimated_cycle = int(len(df) / sign_changes)
                    st.success(f"⏱️ **평균 순환매 사이클**: 약 **{max(3, estimated_cycle)}일 ~ {estimated_cycle + 2}일** 내외")

         # 4. 🛠️ [HTML 융단폭격] 하단 원본 데이터 표 출력 (이중 스크롤 100% 박멸)
            st.write("---")
            st.subheader(f"📋 데이터 시트 ({selected_file_name})")
            
            display_df = df[['종가', '외인', '외인 누적수급', '기관', '기관 누적수급', '개인', '개인 누적수급']].copy()
            display_df.index = df['날짜'].dt.strftime('%Y-%m-%d')
            
            # 천단위 콤마 포맷팅 변환
            for col in display_df.columns:
                display_df[col] = display_df[col].map(lambda x: f"{x:,.0f}")
                
            reversed_df = display_df.iloc[::-1]

            # 💡 판다스 데이터프레임을 완벽한 HTML 테이블로 변환하여 CSS와 함께 주입
            html_style = """
            <style>
                .scroll-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: sans-serif;
                    font-size: 14px;
                }
                .scroll-table th {
                    background-color: #F8F9FA;
                    color: #333333;
                    padding: 10px;
                    border-bottom: 2px solid #E2E8F0;
                    text-align: right;
                }
                .scroll-table th:first-child, .scroll-table td:first-child {
                    text-align: center; /* 날짜 열은 가운데 정렬 */
                }
                .scroll-table td {
                    padding: 8px 10px;
                    border-bottom: 1px solid #E2E8F0;
                    text-align: right;
                    color: #1A202C;
                }
                /* 양수(+) 값인 칸에 은은한 파스텔톤 연두색 배경 마킹 */
                .pos-bg {
                    background-color: #E8F5E9 !important;
                    color: #2E7D32 !important;
                    font-weight: 500;
                }
            </style>
            """

            # HTML 표 생성 로직
            table_html = f'<table class="scroll-table"><thead><tr><th>날짜</th>'
            for col in reversed_df.columns:
                table_html += f'<th>{col}</th>'
            table_html += '</tr></thead><tbody>'

            for date, row in reversed_df.iterrows():
                table_html += f'<tr><td>{date}</td>'
                for col in reversed_df.columns:
                    val_str = row[col]
                    # 원본 값이 양수인지 판단 (마이너스 부호가 없는 경우, 단 0은 제외)
                    is_positive = '-' not in val_str and val_str != '0'
                    
                    if is_positive:
                        table_html += f'<td class="pos-bg">{val_str}</td>'
                    else:
                        table_html += f'<td>{val_str}</td>'
                table_html += '</tr>'
            table_html += '</tbody></table>'

            # 스트림릿에 순수 HTML로 렌더링 (이중 스크롤 소멸)
            st.markdown(html_style + table_html, unsafe_allow_html=True)
