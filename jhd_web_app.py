import streamlit as st
import google.generativeai as genai
import os

# 1. ตั้งค่าหน้าเว็บ (UI Configuration)
st.set_page_config(page_title="JHD Intelligence Hub", page_icon="💼", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3 { color: #1B1B1B !important; font-family: 'Segoe UI', sans-serif; font-weight: 600; }
    .stMarkdown p, .stMarkdown li { color: #1B1B1B !important; font-size: 16px; }
    .stChatMessage { border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #EAEAEA; background-color: #F9F9F9; }
    </style>
""", unsafe_allow_html=True)

st.title("💼 JHD Intelligence System")
st.subheader("Central Control Hub (Phase 1 — Core AI Organization)")
st.markdown("---")

# 2. ตั้งค่า API Key
API_KEY = st.secrets["GEMINI_KEY"]
genai.configure(api_key=API_KEY)

# 3. ฟังก์ชันโหลดสมอง (Knowledge Base) ของ AI ทั้ง 5
def load_agent_prompt(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return "ไม่พบข้อมูลสมอง (ไฟล์ .md)"

# 4. กำหนดข้อมูล Sub Agent ทั้ง 5
agents = {
    "☀️ SUN (ผู้ควบคุมระบบ)": {"file": "jhd_sun.md", "color": "blue"},
    "🚙 TERRA (กลยุทธ์ & มาตรฐาน)": {"file": "jhd_terra.md", "color": "brown"},
    "🚗 NOTE (ฝ่ายขาย & การตลาด)": {"file": "jhd_note.md", "color": "red"},
    "🛻 NAVARA (ออกแบบ & ครีเอทีฟ)": {"file": "jhd_navara.md", "color": "gray"},
    "🛻 BIGM (ผลิต & ปฏิบัติการ)": {"file": "jhd_bigm.md", "color": "black"}
}

# 5. UI เลือก Agent ที่ต้องการคุยด้วย
selected_agent_name = st.selectbox("เลือกระบบ AI ที่ต้องการสั่งงาน:", list(agents.keys()))
agent_info = agents[selected_agent_name]
system_instruction = load_agent_prompt(agent_info["file"])

# 6. ระบบแชทและประวัติการสนทนา
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_agent" not in st.session_state or st.session_state.current_agent != selected_agent_name:
    st.session_state.chat_history = [] # ล้างแชทเมื่อเปลี่ยนแผนก
    st.session_state.current_agent = selected_agent_name

# แสดงประวัติแชท
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. กล่องรับคำสั่ง
if prompt := st.chat_input(f"พิมพ์สั่งงาน {selected_agent_name} ที่นี่..."):
    if not API_KEY:
        st.error("กรุณาใส่ API Key ก่อนใช้งาน")
        st.stop()

    # แสดงข้อความผู้ใช้
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # ประมวลผลด้วย Gemini
    with st.chat_message("assistant"):
        with st.spinner(f"กำลังประมวลผลโดย {selected_agent_name.split(' ')[1]}..."):
            try:
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    system_instruction=system_instruction
                )
                
                # รวมประวัติแชทเพื่อให้ AI จำบริบทได้
                history_for_gemini = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m["content"]]} for m in st.session_state.chat_history[:-1]]
                
                chat = model.start_chat(history=history_for_gemini)
                response = chat.send_message(prompt)
                
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
