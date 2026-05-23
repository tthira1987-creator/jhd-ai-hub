import streamlit as st
import os
import json
import re
import requests
import math
from openai import OpenAI
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==================================================
# PRICING ENGINE — JHD 3D Hybrid Letter™
# ==================================================
def calculate_jhd_price(char_count, height, width, material, thickness, option_num):
    factors = {
        'CN': {6: 0.45, 10: 0.60, 15: 0.95, 20: 1.40, 25: 1.85},
        'CT': {6: 0.95, 10: 1.35, 15: 1.95, 20: 2.60, 25: 3.20},
        'AU': {6: 0.70, 10: 1.05, 15: 1.85, 20: 2.40, 25: 3.00}
    }
    options_pct = {1: 0.0, 2: 0.20, 3: 0.45, 4: 0.35, 5: 0.60, 6: 1.20, 7: 1.55}
    option_names = {
        1: "SIDE RAW — Economy",
        2: "SIDE FINISH — Standard",
        3: "FULL FINISH — Premium Paint",
        4: "TOP ALU / SIDE RAW — Modern Hybrid",
        5: "TOP ALU / SIDE FINISH — Premium Hybrid",
        6: "TOP ALU + HALO / SIDE RAW — Luxury Hybrid LED",
        7: "TOP ALU + HALO / SIDE FINISH — Signature LED Series"
    }
    material_names = {'CN': 'CN — Standard', 'CT': 'CT — Premium', 'AU': 'AU — Color Core'}

    area = height * width
    factor = factors[material][thickness]
    base_price = area * factor
    option_price = base_price * options_pct[option_num]
    price_per_char = base_price + option_price
    total_no_vat = price_per_char * char_count
    vat = total_no_vat * 0.07
    grand_total = math.ceil(total_no_vat + vat)

    return {
        "char_count": char_count,
        "height": height,
        "width": width,
        "material_name": material_names[material],
        "thickness": thickness,
        "option_name": option_names[option_num],
        "area": area,
        "base_price": round(base_price, 2),
        "option_pct": int(options_pct[option_num] * 100),
        "option_price": round(option_price, 2),
        "price_per_char": round(price_per_char, 2),
        "total_no_vat": round(total_no_vat, 2),
        "vat": round(vat, 2),
        "grand_total": grand_total
    }

def format_price_output(r):
    return f"""
━━━━━━━━━━━━━━━━━━
📋 ใบเสนอราคา JHD 3D Hybrid Letter™
━━━━━━━━━━━━━━━━━━
📌 รายละเอียดงาน
• จำนวน: {r['char_count']} ตัว
• วัสดุ: {r['material_name']}
• ความหนา: {r['thickness']} มม.
• ขนาด: {r['height']} × {r['width']} ซม. | พื้นที่: {r['area']} ตร.ซม.
• Option: {r['option_name']}

💰 การคำนวณ
• BASE PRICE: {r['base_price']:,.2f} บาท/ตัว
• ค่า Option (+{r['option_pct']}%): {r['option_price']:,.2f} บาท
• ราคาต่อตัว: {r['price_per_char']:,.2f} บาท

🧾 สรุปราคา
• ราคาก่อน VAT: {r['total_no_vat']:,.2f} บาท
• VAT 7%: {r['vat']:,.2f} บาท
• **ราคารวม {r['char_count']} ตัว: {r['grand_total']:,} บาท**

⚠️ ราคารวม VAT 7% แล้ว
━━━━━━━━━━━━━━━━━━
"""

def try_extract_and_calculate(text):
    """ดักจับ JSON จาก AI response แล้วคำนวณราคาอัตโนมัติ"""
    try:
        match = re.search(r'\{[^{}]*"char_count"[^{}]*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            required = ["char_count", "height", "width", "material", "thickness", "option_num"]
            if all(k in data for k in required):
                result = calculate_jhd_price(
                    int(data["char_count"]),
                    float(data["height"]),
                    float(data["width"]),
                    str(data["material"]).upper(),
                    int(data["thickness"]),
                    int(data["option_num"])
                )
                return format_price_output(result)
    except Exception:
        pass
    return None

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="JHD Intelligence Hub", page_icon="💼", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3 { color: #1B1B1B !important; font-family: 'Segoe UI', sans-serif; font-weight: 600; }
    .stMarkdown p, .stMarkdown li { color: #1B1B1B !important; font-size: 16px; }
    .stChatMessage { border-radius: 12px; padding: 15px; margin-bottom: 15px;
                     border: 1px solid #EAEAEA; background-color: #F9F9F9; }
    .price-box { background: #F0FFF4; border-left: 4px solid #38A169;
                 padding: 16px; border-radius: 8px; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

st.title("💼 JHD Intelligence System")
st.subheader("Central Control Hub — Smart Flow Automation")
st.markdown("---")

# ==================================================
# API CLIENT
# ==================================================
if "OPENROUTER_API_KEY" in st.secrets:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"],
    )
else:
    st.error("❌ ไม่พบ OPENROUTER_API_KEY ใน Streamlit Secrets")
    st.stop()

# ==================================================
# GITHUB CONFIG
# ==================================================
GITHUB_USER   = "tthira1987-creator"
GITHUB_REPO   = "jhd-ai-hub"
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
            gc = gspread.authorize(creds)
            return gc.open_by_key(GOOGLE_SHEET_KEY)
    except Exception as e:
        st.sidebar.warning(f"⚠️ Sheets ยังไม่ทำงาน: {e}")
    return None

@st.cache_data(ttl=300)
def fetch_md(filename):
    """ดึง .md จาก GitHub — cache 5 นาที"""
    url = GITHUB_RAW_URL + filename
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return f"⚠️ ไม่พบไฟล์ {filename} บน GitHub"

sheet_db = init_google_sheets()

# ==================================================
# AGENT REGISTRY — รองรับทุก sub-agent ที่แก้ไขแล้ว
# ==================================================
AGENTS = {
    "☀️ SUN — ผู้ควบคุมระบบ": {
        "file": "jhd_sun.md",
        "context_file": "jhd_context.md",   # โหลดเสริมอัตโนมัติ
        "tab": "System_SOP",
        "pricing": False,
        "desc": "Single Point of Contact · Route งานทุกประเภท"
    },
    "🚙 TERRA — กลยุทธ์ & มาตรฐาน": {
        "file": "jhd_terra.md",
        "context_file": None,
        "tab": "Finance_Data",
        "pricing": False,
        "desc": "SOP · Framework · Knowledge Base · Cost Standard"
    },
    "🚗 NOTE — ฝ่ายขาย & ราคา": {
        "file": "jhd_note.md",
        "context_file": None,
        "tab": "Sales_&_Brief",
        "pricing": True,   # trigger Pricing Engine อัตโนมัติ
        "desc": "ประเมินราคา · ใบเสนอราคา · CRM · Sales Script"
    },
    "🛻 NAVARA — ออกแบบ & ครีเอทีฟ": {
        "file": "jhd_navara.md",
        "context_file": None,
        "tab": "Design_Brief",
        "pricing": False,
        "desc": "Concept · Mood & Tone · Mockup · Design Direction"
    },
    "🛻 BIGM — ผลิต & ปฏิบัติการ": {
        "file": "jhd_bigm.md",
        "context_file": None,
        "tab": "Production_Spec",
        "pricing": True,   # trigger Pricing Engine (รีเช็กสเปก)
        "desc": "Production · QC · ต้นทุนวัสดุ · จัดคิว CNC"
    },
}

# ==================================================
# SIDEBAR — เลือก Agent + info
# ==================================================
with st.sidebar:
    st.markdown("### 🤖 เลือก Sub-Agent")
    selected_name = st.selectbox(
        "Agent:", list(AGENTS.keys()), label_visibility="collapsed", key="agent_selector"
    )
    agent = AGENTS[selected_name]
    st.markdown(f"**{selected_name}**")
    st.caption(agent["desc"])
    st.markdown("---")

    if agent["pricing"]:
        st.markdown("### 🧮 Pricing Engine")
        st.caption("คำนวณราคา JHD 3D Hybrid Letter™ ได้ทันทีโดยไม่ต้องพิมพ์")

        with st.expander("กรอกสเปกด้วยตัวเอง"):
            p_chars   = st.number_input("จำนวนตัวอักษร", 1, 200, 5)
            p_height  = st.number_input("ความสูง (ซม.)", 5.0, 200.0, 30.0, step=1.0)
            p_width   = st.number_input("ความกว้าง (ซม.)", 5.0, 200.0, 30.0, step=1.0)
            p_mat     = st.selectbox("เกรดวัสดุ", ["CN", "CT", "AU"])
            p_thick   = st.selectbox("ความหนา (มม.)", [6, 10, 15, 20, 25])
            p_opt     = st.selectbox("Option", [1,2,3,4,5,6,7],
                            format_func=lambda x: f"OPT {x:02d}")
            if st.button("💰 คำนวณราคา"):
                r = calculate_jhd_price(p_chars, p_height, p_width, p_mat, p_thick, p_opt)
                st.markdown(f"<div class='price-box'>{format_price_output(r)}</div>",
                            unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ ล้างประวัติแชท"):
        st.session_state.chat_history = []
        st.session_state.current_agent = None
        st.rerun()

# ==================================================
# SYSTEM PROMPT BUILDER
# ==================================================
def build_system_prompt(agent_info):
    base = fetch_md(agent_info["file"])
    if agent_info.get("context_file"):
        ctx = fetch_md(agent_info["context_file"])
        base += f"\n\n---\n## 📚 CONTEXT REFERENCE\n{ctx}"
    return base

# ==================================================
# CHAT STATE
# ==================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if st.session_state.get("current_agent") != selected_name:
    st.session_state.chat_history = []
    st.session_state.current_agent = selected_name

# ==================================================
# CHAT UI
# ==================================================
st.markdown(f"### {selected_name}")
st.caption(agent["desc"])

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"สั่งงาน {selected_name} ที่นี่..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    try:
        system_prompt = build_system_prompt(agent)
        messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.chat_history:
            messages.append({"role": m["role"], "content": m["content"]})

        with st.chat_message("assistant"):
            with st.spinner("กำลังประมวลผล..."):
                response = client.chat.completions.create(
                    model="google/gemini-2.5-flash",
                    messages=messages
                )
                ai_text = response.choices[0].message.content

            st.markdown(ai_text)

            # Auto Pricing Engine — ดักจับ JSON จาก NOTE / BIGM
            if agent["pricing"]:
                price_output = try_extract_and_calculate(ai_text)
                if price_output:
                    st.markdown("---")
                    st.markdown("**📊 ผลคำนวณจาก Pricing Engine:**")
                    st.markdown(
                        f"<div class='price-box'><pre>{price_output}</pre></div>",
                        unsafe_allow_html=True
                    )
                    ai_text += f"\n\n---\n**[Pricing Engine]**\n{price_output}"

        st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

        # บันทึก Google Sheets
        if sheet_db:
            try:
                sheet_db.worksheet(agent["tab"]).append_row(
                    [str(datetime.now()), selected_name, prompt]
                )
            except Exception:
                pass

        # ==================================================
        # ⚡ AUTOMATION HANDOFF (สายพานสลับสายอัตโนมัติ)
        # ==================================================
        if "[ROUTE_TO:" in ai_text:
            match = re.search(r'\[ROUTE_TO:\s*([A-Z]+)\]', ai_text)
            if match:
                next_agent_short = match.group(1)
                
                agent_mapping = {
                    "NOTE": "🚗 NOTE — ฝ่ายขาย & ราคา",
                    "NAVARA": "🛻 NAVARA — ออกแบบ & ครีเอทีฟ",
                    "BIGM": "🛻 BIGM — ผลิต & ปฏิบัติการ",
                    "TERRA": "🚙 TERRA — กลยุทธ์ & มาตรฐาน"
                }
                
                if next_agent_short in agent_mapping:
                    next_agent_full = agent_mapping[next_agent_short]
                    st.session_state.current_agent = next_agent_full
                    
                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": f"*(ระบบอัตโนมัติส่งต่องานจาก {selected_name.split(' ')[0]}):* โปรดอ่านข้อมูลข้างต้นและดำเนินการในส่วนของคุณต่อทันที"
                    })
                    
                    st.session_state.agent_selector = next_agent_full
                    st.rerun()

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
