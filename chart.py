import matplotlib.pyplot as plt
import numpy as np

# 한글 폰트 설정 (인터프리터 환경에 맞춰 기본 폰트 사용, 깨짐 방지용 영어 병기)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 설정
entry_points = ['Early (+5%)', 'Confirmed (+10%)', 'Overheated (+15%)']
max_gain = [25, 20, 15]
avg_risk = [-3.5, -6.5, -11.0]

x = np.arange(len(entry_points))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 6))

# 막대 그래프 그리기
rects1 = ax.bar(x - width/2, max_gain, width, label='Max Expected Gain (To Upper Limit)', color='#d62728')
rects2 = ax.bar(x + width/2, avg_risk, width, label='Avg Downside Risk (Failed Breakout)', color='#1f77b4')

# 레이블 및 디자인 설정
ax.set_ylabel('Percentage (%)', fontsize=12)
ax.set_title('Trading Efficiency by Entry Points (5% vs 10% vs 15%)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(entry_points, fontsize=11)
ax.axhline(0, color='black', linewidth=0.8)
ax.legend(loc='upper right', fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.5)

# 수치 표시
def autolabel(rects, is_positive=True):
    for rect in rects:
        height = rect.get_height()
        va = 'bottom' if is_positive else 'top'
        xytext = (0, 3) if is_positive else (0, -3)
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=xytext, textcoords="offset points",
                    ha='center', va=va, fontweight='bold')

autolabel(rects1, True)
autolabel(rects2, False)

plt.tight_layout()
plt.show()
