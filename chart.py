import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# 앱 제목 및 레이아웃 설정
st.set_page_config(layout="centered", page_title="단타 타점 분석")
st.title("📊 상한가 주도주 타점별 효율 분석")
st.write("10% 이상 뜬 종목을 추격 매수할 때와 5% 초입에 잡을 때의 실전 리스크 비교")

# 1. 데이터 설정
entry_points = ['Early (+5%)', 'Confirmed (+10%)', 'Overheated (+15%)']
max_gain = [25.0, 20.0, 15.0]     # 상한가 도달 시 최대 기대수익
avg_risk = [-3.5, -6.5, -11.0]    # 돌파 실패 시 감당해야 할 리스크

x = np.arange(len(entry_points))
width = 0.35

# 2. Matplotlib 차트 생성
fig, ax = plt.subplots(figsize=(8, 5))

# 수익(빨강)과 리스크(파랑) 막대 그래프
rects1 = ax.bar(x - width/2, max_gain, width, label='Max Gain (To Upper)', color='#d62728')
rects2 = ax.bar(x + width/2, avg_risk, width, label='Avg Downside Risk', color='#1f77b4')

# 그래프 꾸미기
ax.set_ylabel('Percentage (%)')
ax.set_title('Trading Efficiency by Entry Points', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(entry_points)
ax.axhline(0, color='black', linewidth=0.8)
ax.legend(loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.5)

# 막대 위에 숫자 표시해주기
for rect in rects1:
    height = rect.get_height()
    ax.annotate(f'{height:.1f}%', xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
for rect in rects2:
    height = rect.get_height()
    ax.annotate(f'{height:.1f}%', xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, -3), textcoords="offset points", ha='center', va='top', fontweight='bold')

plt.tight_layout()

# 3. Streamlit 화면에 그래프 뿌리기
st.pyplot(fig)

st.markdown("""
