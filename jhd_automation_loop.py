import streamlit as st
import time
from jhd_workflow_manager import JHDWorkflowManager

st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")

# ==========================================
# 🔒 ระบบ LOGIN (รายบุคคล)
# ==========================================
def check_password():
    def login_attempt():
        user = st.session_state["username_input"].lower().strip()
        pwd = st.session_state["password_input"]
        
        # เช็กว่ามีชื่อผู้ใช้นี้ในระบบไหม และรหัสผ่านตรงกันไหม
        if user in st.secrets["credentials"] and st.secrets["credentials"][user] == pwd:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = user # บันทึกไว้ว่าใครกำลังใช้งาน
            del st.session_state["password_input"]  # ลบรหัสออกจากระบบเพื่อความปลอดภัย
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 JHD Intelligence Access")
        st.text_input("👤 Username", key="username_input")
        st.text_input("🔑 Password", type="password", key="password_input")
        st.button("เข้าสู่ระบบ", on_click=login_attempt)
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 JHD Intelligence Access")
        st.text_input("👤 Username", key="username_input")
        st.text_input("🔑 Password", type="password", key="password_input")
        st.button("เข้าสู่ระบบ", on_click=login_attempt)
        st.error("⚠️ Username หรือ รหัสผ่านไม่ถูกต้อง")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# ☀️ โค้ดหลักของน้อง SUN 
# ==========================================
st.sidebar.title("⚙️ System Control")
# ดึงชื่อคนที่ล็อกอินมาโชว์ในแถบด้านข้าง
current_user = st.session_state.get('current_user', 'User').upper()
st.sidebar.success(f"👤 เข้าสู่ระบบโดย: **{current_user}**")
st.sidebar.markdown("---")

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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): 
        if msg["role"] == "assistant":
            st.markdown(f"""
                <div style="background-color: #2E2E38; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #3E3E48; color: #E0E0E0; margin-bottom: 5px;">
                    {msg["content"]}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

if prompt := st.chat_input("💬 พิมพ์คุยกับน้อง SUN..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)
        
    with st.spinner("น้องซันกำลังพิมพ์..."):
        full_result = jhd_manager.run_workflow(st.session_state.messages, mode)
        
    bubbles = full_result.split("[SPLIT]")
    
    for bubble in bubbles:
        clean_bubble = bubble.strip()
        if clean_bubble:
            with st.chat_message("assistant"):
                st.markdown(f"""
                    <div style="background-color: #2E2E38; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #3E3E48; color: #E0E0E0; margin-bottom: 5px;">
                        {clean_bubble}
                    </div>
                """, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": clean_bubble})
            time.sleep(0.8)
