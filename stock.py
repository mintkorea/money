import os
from pykrx import stock

print("=== 데이터 수집을 시작합니다 ===")

# 1. 날짜 및 종목 설정 (2026년 1월 1일부터 오늘까지)
start_date = "20260101"
end_date = "20260603"
ticker = "000660"  # SK하이닉스 (삼성전자는 "005930")

print(f"▶ 대상 종목: SK하이닉스 ({ticker})")
print(f"▶ 조회 기간: {start_date} ~ {end_date}")

# 2. 가격(OHLCV) 데이터 가져오기
print("▶ 가격 데이터 가져오는 중...")
df_price = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

# 3. 투자자별 순매수 데이터 가져오기
print("▶ 외국인/기관 수급 데이터 가져오는 중...")
df_investor = stock.get_market_net_purchases_of_equities_by_ticker(start_date, end_date, ticker)

# 4. 엑셀 파일로 저장
file_name = "sk_hynix_data.xlsx"
print(f"▶ 엑셀 파일({file_name}) 생성 중...")

# 데이터프레임을 엑셀 파일로 저장
df_price.to_excel(file_name)

print("====================================")
print("🎉 축하합니다! 데이터 수집이 완료되었습니다.")
print(f"📍 파일 위치: {os.getcwd()}\\{file_name}")
print("====================================")
