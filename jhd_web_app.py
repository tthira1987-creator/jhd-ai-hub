import streamlit as st
import os
import json
import requests
import pandas as pd
import google.generativeai as genai
from google.oauth2.service_account import Credentials
import gspread

# ==================================================
# 1. JHD INTELLIGENCE SYSTEM™ - CONFIGURATION
# ==================================================
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

# ⚙️ ดึงคีย์หลักจากคลังเก็บความลับ (Secrets)
if "GEMINI_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
else:
    st.error("❌ ไม่พบ GEMINI_KEY ใน Streamlit Secrets")

# ⚙️ กำหนดค่าคลังข้อมูลเพื่อดึง SOP จาก GitHub ของพี่ออฟ
GITHUB_USER = "tthira1987-creator"
GITHUB_REPO = "jhd-ai-hub"
GITHUB_BRANCH = "main"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/"

# ⚙️ กำหนดรหัสลิงก์เชื่อมโยงไปยังคลังความทรงจำ Google Sheets ของ JHD
GOOGLE_SHEET_KEY = "1X2vs1tfSRK6_6fBDfORxkFu645u8idvx_AfnBgE64"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# ==================================================
# 2. DATABASE & MEMORY CONNECTIONS (ระบบเชื่อมต่อฐานข้อมูล)
# ==================================================
@st.cache_resource
def init_google_sheets():
    """เชื่อมต่อฐานข้อมูลความทรงจำ JHD ใน Google Sheets ผ่านสิทธิ์ที่ใส่ไว้ใน Secrets"""
    try:
        if "gcp_service_account" in st.secrets and "json_key" in st.secrets["gcp_service_account"]:
            creds_dict = json.loads(st.secrets["gcp_service_account"]["json_key"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(GOOGLE_SHEET_KEY)
            return sheet
    except Exception as e:
        st.sidebar.warning(f"⚠️ สัญชาตญาณความทรงจำ Sheets ยังไม่เริ่มทำงาน: {e}")
    return None

def fetch_sop_from_github(filename):
    """ดึงกฎและข้อบังคับงานดีไซน์ล่าสุดสดๆ จาก GitHub"""
    url = f"{GITHUB_RAW_URL}{filename}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return "ไม่พบข้อมูลระบบ (.md)"

# เริ่มต้นระบบอ่านฐานข้อมูลความทรงจำ
sheet_db = init_google_sheets()

# ==================================================
# 3. SUB AGENT DESIGN SYSTEM
# ==================================================
agents = {
    "☀️ SUN (ผู้ควบคุมระบบ)": {"file": "jhd_sun.md", "color": "blue", "tab": "System_SOP"},
    "⛰️ TERRA (กลยุทธ์ & มาตรฐาน)": {"file": "jhd_terra.md", "color": "brown", "tab": "Finance_Data"},
    "📝 NOTE (ฝ่ายขาย & การตลาด)": {"file": "jhd_note.md", "color": "red", "tab": "Sales_&_Brief"},
    "🎨 NAVARA (ออกแบบ & ครีเอทีฟ)": {"file": "jhd_navara.md", "color": "gray", "tab": "Design_Brief"},
    "🖨️ BIGM (ผลิต & ปฏิบัติการ)": {"file": "jhd_bigm.md", "color": "black", "tab": "Production_Spec"}
}

selected_agent_name = st.selectbox("เลือกแอปพลิเคชันหรือผู้ช่วยที่คุณต้องการสั่งงาน:", list(agents.keys()))
agent_info = agents[selected_agent_name]

# โหลดกฎสัญชาตญาณ (.md) จาก GitHub เข้าไปในสมอง AI ทันทีที่เลือกแถบเมนู
system_instruction = fetch_sop_from_github(agent_info["file"])

# ==================================================
# 4. CHAT HISTORY & SMART FLOW RUNNING
# ==================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_agent" not in st.session_state or st.session_state.current_agent != selected_agent_name:
    st.session_state.chat_history = [] # ล้างแชทเมื่อเปลี่ยนแผนก
    st.session_state.current_agent = selected_agent_name

# แสดงบทสนทนาเก่าบนหน้าจอ
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ดึงประวัติสั้น 5 แถวจาก Google Sheets ตามสิทธิ์แผนกมาโชว์แบคอัพความจำ (ถ้ามีข้อมูล)
if sheet_db:
    try:
        worksheet = sheet_db.worksheet(agent_info["tab"])
        records = worksheet.get_all_records()
        if records:
            with st.expander(f"📊 ฐานความทรงจำล่าสุดของระบบใน Google Sheets (แท็บ: {agent_info['tab']})"):
                st.dataframe(pd.DataFrame(records).tail(5))
    except:
        pass

# กล่องแชทรองรับการรับคำสั่งบรีฟงานหน้าจอ
if prompt := st.chat_input(f"พิมพ์สั่งงาน {selected_agent_name} ที่นี่..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # ส่งข้อความคำสั่งบรีฟงานเข้าประมวลผลร่วมกับโมเดลหลัก Gemini AI 
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        
        # หลอมประวัติคุยรวมกับบรีฟล่าสุดเพื่อให้ AI มีความจำต่อเนื่อง
        history_for_gemini = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m["content"]]} for m in st.session_state.chat_history[:-1]]
        chat = model.start_chat(history=history_for_gemini)
        
        with st.chat_message("assistant"):
            with st.spinner(f"กำลังประมวลผลโดย {selected_agent_name.split(' ')[1]}..."):
                response = chat.send_message(prompt)
                ai_response = response.text
                st.markdown(ai_response)
                
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
        # เขียนประวัติงานใหม่ลงไปบันทึกเพิ่มใน Google Sheets อัตโนมัติ ป้องกันข้อมูลตกหล่น
        if sheet_db:
            try:
                worksheet = sheet_db.worksheet(agent_info["tab"])
                from datetime import datetime
                worksheet.append_row([str(datetime.now()), selected_agent_name, prompt])
            except:
                pass
                
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
