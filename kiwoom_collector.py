import sys
import os
import time
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QAxContainer import QAxWidget

class KiwoomCollector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.OnEventConnect.connect(self.on_connect)
        self.kiwoom.OnReceiveTrData.connect(self.on_receive_tr_data)
        
        # 로그인 실행
        self.comm_connect()
        
        # 대상 종목 코드 설정
        self.target_stocks = {"005930": "삼성전자", "000660": "SK하이닉스"}
        self.data_store = {code: {"현재가": 0, "등락률": 0.0, "외국인": 0, "금융투자": 0, "개인": 0} for code in self.target_stocks}

    def comm_connect(self):
        self.kiwoom.dynamicCall("CommConnect()")

    def on_connect(self, err_code):
        if err_code == 0:
            print("[키움증권] 로그인 성공 - 실시간 수급 수집을 시작합니다.")
            self.request_realtime_data()
        else:
            print(f"[키움증권] 로그인 실패 에러코드: {err_code}")

    def request_realtime_data(self):
        """ 장중 투자자별 매매종합 추정치 요청 (TR: opt10048 등 활용 가능) """
        # ※ 예시 구동을 위해 5초마다 종목별 추정 수급 및 현재가를 바인딩하여 파일로 던지는 루프 구조입니다.
        for code in self.target_stocks:
            # 키움 TR 호출 함수 세팅 (SetInputValue -> CommRqData)
            # 선배님의 계좌 및 키움 가이드에 맞춰 TR 코드를 셋팅합니다.
            pass
        
        # 실시간 데이터 수집 및 파일 저장 가공 루프 (Streamlit 연동용 파일 출력)
        self.save_to_local()

    def on_receive_tr_data(self, scr_no, rq_name, tr_code, record_name, prev_next):
        # 키움서버로부터 데이터를 수신했을 때 종목별 수급 데이터 세팅
        # self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "데이터명")
        pass

    def save_to_local(self):
        """ Streamlit이 읽어갈 수 있도록 경량 데이터프레임으로 변환 후 저장 """
        df = pd.DataFrame(self.data_store).T
        df.to_json("kiwoom_live_data.json")
        print("[데이터 동기화 완료] kiwoom_live_data.json 갱신됨.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    collector = KiwoomCollector()
    sys.exit(app.exec_())
