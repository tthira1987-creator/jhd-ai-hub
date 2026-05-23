import streamlit as st
import os
import json
import requests
import pandas as pd
from openai import OpenAI # เปลี่ยนมาใช้ตัวนี้ครับ
from datetime import datetime
import gspread
import math

def calculate_jhd_price(char_count, height, width, material, thickness, option_num):
    # 1. ตาราง Material Factor 2026
    factors = {
        'CN': {6: 0.45, 10: 0.60, 15: 0.95, 20: 1.40, 25: 1.85},
        'CT': {6: 0.95, 10: 1.35, 15: 1.95, 20: 2.60, 25: 3.20},
        'AU': {6: 0.70, 10: 1.05, 15: 1.85, 20: 2.40, 25: 3.00}
    }
    # 2. ตาราง % Option Layer
    options_pct = {1: 0.0, 2: 0.20, 3: 0.45, 4: 0.35, 5: 0.60, 6: 1.20, 7: 1.55}
    
    # 3. คำนวณราคา (คณิตศาสตร์ตรง ๆ ทศนิยมไม่แกว่ง)
    area = height * width
    factor = factors[material][thickness]
    
    base_price = area * factor
    option_price = base_price * options_pct[option_num]
    final_price_per_char = base_price + option_price
    
    total_no_vat = final_price_per_char * char_count
    vat = total_no_vat * 0.07
    grand_total = math.ceil(total_no_vat + vat) # ปัดเศษขึ้นเป็นจำนวนเต็ม
    
    return {
        "base_price": base_price,
        "option_price": option_price,
        "price_per_char": final_price_per_char,
        "total_no_vat": total_no_vat,
        "vat": vat,
        "grand_total": grand_total
    }
from google.oauth2.service_account import Credentials

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

# ⚙️ เชื่อมต่อ OpenRouter
if "OPENROUTER_API_KEY" in st.secrets:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"],
    )
else:
    st.error("❌ ไม่พบ OPENROUTER_API_KEY ใน Streamlit Secrets กรุณาไปตั้งค่าก่อนครับ")
    st.stop()

# ... (ส่วน GITHUB_RAW_URL, GOOGLE_SHEET_KEY และ init_google_sheets เก็บไว้เหมือนเดิม)
GITHUB_USER = "tthira1987-creator"
GITHUB_REPO = "jhd-ai-hub"
GITHUB_BRANCH = "main"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/"
GOOGLE_SHEET_KEY = "1X2vs1tFsRK6_6fBDFfORxkFu645u8idvx__AfnBgE64"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def init_google_sheets():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = json.loads(st.secrets["gcp_service_account"]["json_key"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            return client.open_by_key(GOOGLE_SHEET_KEY)
    except Exception as e:
        st.sidebar.warning(f"⚠️ Sheets ยังไม่ทำงาน: {e}")
    return None

def fetch_sop_from_github(filename):
    url = f"{GITHUB_RAW_URL}{filename}"
    try:
        response = requests.get(url)
        if response.status_code == 200: return response.text
    except: pass
    return "ไม่พบข้อมูลระบบ (.md)"

sheet_db = init_google_sheets()

# ==================================================
# 3. SUB AGENT DESIGN SYSTEM
# ==================================================
agents = {
    "☀️ SUN (ผู้ควบคุมระบบ)": {"file": "jhd_sun.md", "tab": "System_SOP"},
    "⛰️ TERRA (กลยุทธ์ & มาตรฐาน)": {"file": "jhd_terra.md", "tab": "Finance_Data"},
    "📝 NOTE (ฝ่ายขาย & การตลาด)": {"file": "jhd_note.md", "tab": "Sales_&_Brief"},
    "🎨 NAVARA (ออกแบบ & ครีเอทีฟ)": {"file": "jhd_navara.md", "tab": "Design_Brief"},
    "🖨️ BIGM (ผลิต & ปฏิบัติการ)": {"file": "jhd_bigm.md", "tab": "Production_Spec"}
}

selected_agent_name = st.selectbox("เลือกผู้ช่วยที่คุณต้องการสั่งงาน:", list(agents.keys()))
agent_info = agents[selected_agent_name]
system_instruction = fetch_sop_from_github(agent_info["file"])

# ==================================================
# 4. CHAT LOGIC (ปรับแก้มาใช้ client ของ OpenAI)
# ==================================================
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_agent" not in st.session_state or st.session_state.current_agent != selected_agent_name:
    st.session_state.chat_history = []
    st.session_state.current_agent = selected_agent_name

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if prompt := st.chat_input(f"พิมพ์สั่งงาน {selected_agent_name} ที่นี่..."):
    with st.chat_message("user"): st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    try:
        # เตรียมประวัติแชท (OpenRouter ใช้รูปแบบ message list)
        messages = [{"role": "system", "content": system_instruction}]
        for m in st.session_state.chat_history:
            messages.append({"role": m["role"], "content": m["content"]})
        
        with st.chat_message("assistant"):
            with st.spinner("กำลังประมวลผลผ่าน OpenRouter..."):
                response = client.chat.completions.create(
                    model="google/gemini-2.5-flash",
                    messages=messages
                )
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
        
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
        if sheet_db:
            try:
                sheet_db.worksheet(agent_info["tab"]).append_row([str(datetime.now()), selected_agent_name, prompt])
            except: pass
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
