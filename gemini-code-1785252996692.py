import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(page_title="서울 지하철 스마트 HVAC 제어 시스템", layout="wide")

st.title("🚇 서울교통공사 실데이터 기반 스마트 HVAC PID 제어기")
st.caption("승객 체감 피드백(더워요/추워요) 연동 실시간 PID 냉방 제어 시뮬레이터")

# ---------------------------------------------------------
# [핵심] 모든 접속자가 공유하는 전역 데이터베이스 (서버 RAM 공유)
# ---------------------------------------------------------
@st.cache_resource
def get_global_data():
    return {"hot_votes": 0, "cold_votes": 0}

global_data = get_global_data()

# 2. 사이드바: 노선 선택 및 버튼 피드백
st.sidebar.header("🎛️ 승객 상태 및 노선 설정")
selected_line = st.sidebar.selectbox("조회할 지하철 노선", [f"{i}호선" for i in range(1, 10)], index=1)

st.sidebar.subheader("🌐 실시간 전체 승객 피드백")
st.sidebar.caption("※ 모든 접속자의 투표가 실시간 합산됩니다.")

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🥵 더워요"):
        global_data["hot_votes"] += 1
        st.rerun()

with col_btn2:
    if st.button("🥶 추워요"):
        global_data["cold_votes"] += 1
        st.rerun()

# 테스트용 초기화 버튼
if st.sidebar.button("🔄 실시간 투표 데이터 리셋"):
    global_data["hot_votes"] = 0
    global_data["cold_votes"] = 0
    st.rerun()

total_votes = global_data["hot_votes"] + global_data["cold_votes"]

# 3. 투표 결과에 따른 목표 온도(T_target) 보정 가중치 계산
if total_votes > 0:
    hot_ratio = global_data["hot_votes"] / total_votes
    target_offset = (0.5 - hot_ratio) * 1.0
    st.sidebar.write(f"**누적 현황:** 더워요 {global_data['hot_votes']}표 / 추워요 {global_data['cold_votes']}표")
    st.sidebar.progress(hot_ratio, text=f"더워요 비율 ({int(hot_ratio * 100)}%)")
else:
    hot_ratio = 0.5
    target_offset = 0.0
    st.sidebar.info("버튼을 눌러 승객 체감 피드백을 전달해 보세요!")

T_TARGET_BASE = 24.0
T_TARGET = T_TARGET_BASE + target_offset

# 메인 화면 메트릭 표시
m1, m2, m3, m4 = st.columns(4)
m1.metric("선택된 노선", selected_line)
m2.metric("기본 목표 온도", f"{T_TARGET_BASE}°C")
m3.metric("승객 피드백 보정 온도", f"{T_TARGET:.2f}°C", delta=f"{target_offset:.2f}°C")
m4.metric("전체 누적 참여자 수", f"{total_votes} 명")

# 4. PID 제어 시뮬레이션 연산
hours = np.arange(5, 25)
line_weight = {"1호선": 0.8, "2호선": 1.0, "3호선": 0.85, "4호선": 0.95, "5호선": 0.8, "6호선": 0.65, "7호선": 0.9, "8호선": 0.8, "9호선": 1.1}
base_crowding = [12, 35, 88, 150.4, 95, 55, 48, 52, 50, 53, 58, 65, 92, 145.2, 110, 70, 65, 55, 35, 15]
crowding_pct = [c * line_weight[selected_line] for c in base_crowding]

time_min = np.arange(0, 19 * 60, 1.0)
hours_cont = 5.0 + time_min / 60.0

crowding_pct_cont = np.interp(hours_cont, hours, crowding_pct)
passengers = crowding_pct_cont * 1.6

# PID 시뮬레이션 변수
temp = 24.0
kp, ki, kd = 15.0, 0.35, 8.0
integral, prev_error = 0.0, 0.0
temp_history, power_history = [], []

for i, p in enumerate(passengers):
    t_amb = 23.0 + 10.0 * np.exp(-((hours_cont[i] - 14.5)**2) / 30.0)
    heat_in = (p * 0.08) + 0.12 * (t_amb - temp)
    
    error = temp - T_TARGET
    integral = np.clip(integral + error * 1.0, -20.0, 20.0)
    derivative = (error - prev_error) / 1.0
    prev_error = error
    
    power_pct = np.clip(kp * error + ki * integral + kd * derivative, 0.0, 100.0)
    cooling_out = (power_pct / 100.0) * 22.0
    
    temp += (heat_in - cooling_out) / 45.0
    temp_history.append(temp)
    power_history.append(power_pct)

# 5. 시각화 그래프 출력
st.markdown("---")
st.subheader("📈 실시간 HVAC PID 제어 반응 시뮬레이션")

fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

# 1단: 혼잡도
ax[0].plot(hours_cont, crowding_pct_cont, color="orange", label="Crowding Rate (%)")
ax[0].axhline(100, color="gray", linestyle="--")
ax[0].set_ylabel("Crowding (%)")
ax[0].legend(loc="upper right")
ax[0].grid(alpha=0.3)

# 2단: 실내 온도 및 목표 온도
ax[1].plot(hours_cont, temp_history, color="red", label="Indoor Temp (°C)")
ax[1].axhline(T_TARGET, color="green", linestyle="--", label=f"Target Temp ({T_TARGET:.2f}°C)")
ax[1].set_ylabel("Temp (°C)")
ax[1].legend(loc="upper right")
ax[1].grid(alpha=0.3)

# 3단: 에어컨 가동률
ax[2].plot(hours_cont, power_history, color="blue", label="HVAC Power (%)")
ax[2].set_ylabel("Power (%)")
ax[2].set_xlabel("Hour of Day (05:00 ~ 24:00)")
ax[2].legend(loc="upper right")
ax[2].grid(alpha=0.3)

st.pyplot(fig)
