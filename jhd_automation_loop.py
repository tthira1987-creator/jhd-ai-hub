import streamlit as st
import time
from jhd_workflow_manager import JHDWorkflowManager

st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")

st.sidebar.title("⚙️ System Control")
mode = st.sidebar.radio("สถานะโหมดใช้งาน:", ["Internal Mode (Lead)", "Service Mode (Customer)"])

st.title("☀️ น้อง SUN (JHD Secretary)")
st.caption(f"Status: {mode}")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("⚠️ API Key Error")
    st.stop()

jhd_manager = JHDWorkflowManager(API_KEY)

if "messages" not in st.session_state: 
    st.session_state.messages = []

# แสดงประวัติแชททั้งหมด
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

if prompt := st.chat_input("💬 พิมพ์คุยกับน้อง SUN..."):
    # 1. แสดงข้อความผู้ใช้
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)
        
    # 2. ประมวลผลจาก AI
    with st.spinner("น้องซันกำลังพิมพ์..."):
        full_result = jhd_manager.run_workflow(st.session_state.messages, mode)
        
    # 3. แยกข้อความและแสดงผลเป็น Bubble สไตล์ LINE
    bubbles = full_result.split("[SPLIT]")
    
    for bubble in bubbles:
        clean_bubble = bubble.strip()
        if clean_bubble:
            with st.chat_message("assistant"):
                st.markdown(clean_bubble)
            # บันทึกแต่ละ Bubble ลงประวัติ
            st.session_state.messages.append({"role": "assistant", "content": clean_bubble})
            time.sleep(0.8) # หน่วงเวลา 0.8 วินาทีให้ดูเป็นธรรมชาติ
