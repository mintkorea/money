from pykrx import stock

# 2026년 1월 1일부터 오늘까지 SK하이닉스(000660)의 일별 가격/거래량 데이터 가져오기
df_price = stock.get_market_ohlcv_by_date("20260101", "20260603", "000660")

# 같은 기간 외국인, 기관 등의 순매수 거래량 데이터 가져오기
df_investor = stock.get_market_net_purchases_of_equities_by_ticker("20260101", "20260603", "000660")

# 엑셀 파일로 바로 저장하기
df_price.to_excel("sk_hynix_data.xlsx")
