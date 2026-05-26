import streamlit as st
import time
from jhd_workflow_manager import JHDWorkflowManager

st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")

# ==========================================
# 🔒 ระบบ LOGIN (ดักไว้ก่อนโหลดหน้าเว็บหลัก)
# ==========================================
def check_password():
    def password_entered():
        # เช็กรหัสผ่านที่พิมพ์ กับรหัสใน Secrets
        if st.session_state["password"] == st.secrets["JHD_APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # ลบรหัสออกจากระบบทันทีเพื่อความปลอดภัย
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Restricted Access")
        st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน JHD Intelligence:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Restricted Access")
        st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน JHD Intelligence:", type="password", on_change=password_entered, key="password")
        st.error("⚠️ รหัสผ่านไม่ถูกต้อง")
        return False
    return True

# ถ้ายังไม่ล็อกอิน ให้หยุดการทำงานของโค้ดตรงนี้ทันที
if not check_password():
    st.stop()

# ==========================================
# ☀️ โค้ดหลักของน้อง SUN (จะทำงานเมื่อล็อกอินผ่าน)
# ==========================================
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
