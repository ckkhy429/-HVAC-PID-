import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(page_title="서울 지하철 스마트 HVAC 제어 시스템", layout="wide")

st.title("🚇 서울교통공사 실데이터 기반 스마트 HVAC PID 제어기")
st.caption("📱 스마트폰 모바일 최적화 버전 | 승객 체감 피드백(더워요/추워요) 연동")

# ---------------------------------------------------------
# [핵심] 모든 접속자가 공유하는 전역 데이터베이스 (서버 RAM 공유)
# ---------------------------------------------------------
@st.cache_resource
def get_global_data():
    return {"hot_votes": 0, "cold_votes": 0}

global_data = get_global_data()

# 2. 메인 화면: 노선 선택 및 승객 피드백 버튼 (모바일 전면 배치)
st.subheader("🎛️ 노선 선택 및 피드백")

col_line, col_reset = st.columns([3, 1])
with col_line:
    selected_line = st.selectbox("조회할 지하철 노선", [f"{i}호선" for i in range(1, 10)], index=1)
with col_reset:
    st.write("") # 간격 맞춤용
    if st.button("🔄 리셋", use_container_width=True):
        global_data["hot_votes"] = 0
        global_data["cold_votes"] = 0
        st.rerun()

st.markdown("---")
st.subheader("📱 실시간 객실 승객 피드백 (모바일 터치)")
st.caption("※ 접속한 모든 승객의 버튼 터치가 실시간 통합 연동됩니다.")

# 모바일용 큼직한 터치 버튼
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🥵 더워요 (냉방 강화)", use_container_width=True):
        global_data["hot_votes"] += 1
        st.rerun()

with col_btn2:
    if st.button("🥶 추워요 (냉방 약화)", use_container_width=True):
        global_data["cold_votes"] += 1
        st.rerun()

total_votes = global_data["hot_votes"] + global_data["cold_votes"]

# 3. 투표 결과에 따른 목표 온도(T_target) 보정 가중치 계산
if total_votes > 0:
    hot_ratio = global_data["hot_votes"] / total_votes
    target_offset = (0.5 - hot_ratio) * 1.0
    st.write(f"📊 **누적 현황:** 더워요 **{global_data['hot_votes']}**표 / 추워요 **{global_data['cold_votes']}**표")
    st.progress(hot_ratio, text=f"더워요 비율 ({int(hot_ratio * 100)}%)")
else:
    hot_ratio = 0.5
    target_offset = 0.0
    st.info("💡 위 버튼을 터치하여 현재 체감 온도를 전송해 보세요!")

T_TARGET_BASE = 24.0
T_TARGET = T_TARGET_BASE + target_offset

# 메인 화면 메트릭 표시
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
m1.metric("선택된 노선", selected_line)
m2.metric("기본 목표 온도", f"{T_TARGET_BASE}°C")
m3.metric("승객 피드백 보정 온도", f"{T_TARGET:.2f}°C", delta=f"{target_offset:.2f}°C")
m4.metric("전체 누적 참여자 수", f"{total_votes} 명")

# 4. PID 제어 시뮬레이션 연산
hours = np.arange(5, 25)
line_weight = {"1호선": 0.8, "2호선": 1.0, "
