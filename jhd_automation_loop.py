import streamlit as st
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

# เรียกใช้ Workflow Manager
jhd_manager = JHDWorkflowManager(API_KEY)

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("💬 พิมพ์คุยกับน้อง SUN..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("น้องซันกำลังประมวลผล..."):
            result = jhd_manager.run_workflow(st.session_state.messages, mode)
            st.markdown(result)
    st.session_state.messages.append({"role": "assistant", "content": result})
