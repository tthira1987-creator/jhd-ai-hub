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
        
        if user in st.secrets["credentials"] and st.secrets["credentials"][user] == pwd:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = user 
            del st.session_state["password_input"]  
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
# ⚙️ ระบบควบคุมและเปลี่ยนโหมด (ล้างแชท)
# ==========================================
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Internal Mode (Lead)"
if "messages" not in st.session_state: 
    st.session_state.messages = []

st.sidebar.title("⚙️ System Control")
current_user = st.session_state.get('current_user', 'User').upper()
st.sidebar.success(f"👤 เข้าสู่ระบบโดย: **{current_user}**")
st.sidebar.markdown("---")

# ปุ่มเลือกโหมด
selected_mode = st.sidebar.radio(
    "สถานะโหมดใช้งาน:", 
    ["Internal Mode (Lead)", "Service Mode (Customer)"],
    index=0 if st.session_state.active_mode == "Internal Mode (Lead)" else 1
)

# ดักจับการเปลี่ยนโหมด
if selected_mode != st.session_state.active_mode:
    if len(st.session_state.messages) > 0:
        st.warning(f"⚠️ คุณกำลังสลับไปยังโหมด **{selected_mode}** ระบบจะทำการล้างแชทเดิมเพื่อเริ่มใหม่ ต้องการบันทึกบทสนทนานี้ไว้หรือไม่?")
        
        # เตรียมไฟล์ Text สำหรับดาวน์โหลด
        chat_log = "=== JHD Intelligence Chat Log ===\n\n"
        for msg in st.session_state.messages:
            role = "ผู้ใช้งาน" if msg['role'] == 'user' else "SUN"
            chat_log += f"[{role}]:\n{msg['content']}\n\n"
            chat_log += "-"*40 + "\n"
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="💾 บันทึกเป็นไฟล์ Text & เริ่มใหม่",
                data=chat_log,
                file_name=f"JHD_ChatLog_{int(time.time())}.txt",
                mime="text/plain",
                on_click=lambda: st.session_state.update({"messages": [], "active_mode": selected_mode})
            )
        with col2:
            if st.button("🗑️ ไม่บันทึก (ล้างแชทเลย)"):
                st.session_state.messages = []
                st.session_state.active_mode = selected_mode
                st.rerun()
        
        st.stop() # หยุดการทำงานชั่วคราวจนกว่าจะกดเลือก
    else:
        st.session_state.active_mode = selected_mode

mode = st.session_state.active_mode

# ==========================================
# ☀️ โค้ดหลักของน้อง SUN 
# ==========================================
st.title("☀️ น้อง SUN (JHD Secretary)")
st.caption(f"Status: {mode}")

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("⚠️ API Key Error")
    st.stop()

jhd_manager = JHDWorkflowManager(API_KEY)

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
