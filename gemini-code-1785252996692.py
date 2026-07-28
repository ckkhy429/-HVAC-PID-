import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(page_title="서울 지하철 스마트 HVAC 제어 시스템", layout="wide")

st.title("🚇 서울교통공사 실데이터 기반 스마트 HVAC PID 제어기")
st.caption("📱 실시간 승객 피드백(더워요/추워요) 연동 시뮬레이터")

# ---------------------------------------------------------
# [핵심] 모든 접속자가 공유하는 전역 데이터베이스 (서버 RAM 공유)
# ---------------------------------------------------------
@st.cache_resource
def get_global_data():
    return {
        "hot_votes": 0, 
        "cold_votes": 0,
        "users": {}  # {"이름": {"hot": 0, "cold": 0}}
    }

global_data = get_global_data()

# 2. 노선 선택 및 리셋
st.subheader("🎛️ 기본 설정")
col_line, col_reset = st.columns([3, 1])
with col_line:
    selected_line = st.selectbox("조회할 지하철 노선", [f"{i}호선" for i in range(1, 10)], index=1)
with col_reset:
    st.write("") 
    if st.button("🔄 전체 데이터 리셋", use_container_width=True):
        global_data["hot_votes"] = 0
        global_data["cold_votes"] = 0
        global_data["users"] = {}
        st.rerun()

st.markdown("---")

# 3. 참여자 이름 입력 및 피드백 버튼
st.subheader("👤 승객 등록 및 피드백 전달")

# 이름 입력
user_name = st.text_input("참여자 이름(또는 닉네임)을 입력하세요:", key="user_name_input").strip()

if user_name:
    st.success(f"**'{user_name}'** 승객님 환영합니다! 아래 버튼을 터치하여 의견을 남겨주세요.")
    
    # 해당 유저 최초 등록
    if user_name not in global_data["users"]:
        global_data["users"][user_name] = {"hot": 0, "cold": 0}

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🥵 더워요 (냉방 강화)", use_container_width=True):
            global_data["hot_votes"] += 1
            global_data["users"][user_name]["hot"] += 1
            st.rerun()

    with col_btn2:
        if st.button("🥶 추워요 (냉방 약화)", use_container_width=True):
            global_data["cold_votes"] += 1
            global_data["users"][user_name]["cold"] += 1
            st.rerun()
else:
    st.warning("⚠️ **버튼을 누르시려면 먼저 위 칸에 이름을 입력해 주세요.**")

# 4. 투표 결과 및 전체 현황
total_votes = global_data["hot_votes"] + global_data["cold_votes"]

if total_votes > 0:
    hot_ratio = global_data["hot_votes"] / total_votes
    target_offset = (0.5 - hot_ratio) * 1.0
else:
    hot_ratio = 0.5
    target_offset = 0.0

T_TARGET_BASE = 24.0
T_TARGET = T_TARGET_BASE + target_offset

# 핵심 요약 지표
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
m1.metric("선택된 노선", selected_line)
m2.metric("기본 목표 온도", f"{T_TARGET_BASE}°C")
m3.metric("승객 피드백 보정 온도", f"{T_TARGET:.2f}°C", delta=f"{target_offset:.2f}°C")
m4.metric("전체 누적 참여자 수", f"{total_votes} 명")

# 5. 참여자별 실시간 투표 현황 표 출력
st.markdown("---")
st.subheader("👥 참여자별 실시간 투표 현황")

if global_data["users"]:
    user_list = []
    for name, votes in global_data["users"].items():
        user_total = votes["hot"] + votes["cold"]
        user_list.append({
            "참여자 이름": name,
            "🥵 더워요": f"{votes['hot']} 회",
            "🥶 추워요": f"{votes['cold']} 회",
            "총 클릭 횟수": f"{user_total} 회"
        })
    df_users = pd.DataFrame(user_list)
    st.dataframe(df_users, use_container_width=True, hide_index
