import os
import streamlit as st
from openai import OpenAI

# ==========================================
# ⚙️ JHD INTELLIGENCE: BACKEND AUTOMATION
# ==========================================

class JHDAutomationSystem:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "google/gemini-2.5-flash"
        
        # 📌 อัปเดต: ใส่ไฟล์คัมภีร์ทั้งหมดให้ตรงกับหน้าที่
        self.agent_files = {
            "SUN": ["jhd_persona_sun.md", "jhd_role_sun.md"],
            "NOTE": [
                "jhd_persona_note.md", "jhd_role_note.md", 
                "jhd_formula_pricing_note.md", "jhd_company_pitch_note.md", 
                "jhd_script_sales_note.md", "jhd_script_quick_reply_note.md"
            ],
            "TERRA": ["jhd_persona_terra.md", "jhd_role_terra.md", "jhd_company_core_terra.md"],
            "NAVARA": ["jhd_persona_navara.md", "jhd_role_navara.md"],
            "BIGM": ["jhd_persona_bigm.md", "jhd_role_bigm.md"]
        }

    def _load_system_prompt(self, agent_name):
        prompt = f"คุณคือ {agent_name} หนึ่งในทีม JHD Intelligence System\n\n"
        for file in self.agent_files.get(agent_name, []):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    prompt += f.read() + "\n\n"
            except FileNotFoundError:
                pass
        return prompt

    def _call_agent(self, agent_name, context_history):
        system_prompt = self._load_system_prompt(agent_name)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_history)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content

    def run_full_workflow(self, user_prompt):
        internal_memory = [{"role": "user", "content": f"ข้อความจากลูกค้า/เจ้านาย: {user_prompt}"}]
        workflow_sequence = ["SUN", "NOTE", "TERRA", "NAVARA", "BIGM"]
        
        # 📌 อัปเดต: สั่งบอทตัวที่ไม่เกี่ยวให้ข้ามงานไปเลย (ลดความเวิ่นเว้อ)
        for agent in workflow_sequence:
            trigger_msg = {
                "role": "user", 
                "content": f"ถึง {agent}: วิเคราะห์คำสั่งล่าสุด หากคุณมีข้อมูลในคู่มือที่ตรงกับคำถาม ให้ดึงข้อมูลนั้นมาตอบให้ครบถ้วน แต่หากคำสั่งนี้ 'ไม่เกี่ยวกับหน้าที่คุณเลย' ให้ตอบแค่คำว่า 'PASS' สั้นๆ คำเดียว ห้ามแต่งเรื่องเพิ่ม"
            }
            internal_memory.append(trigger_msg)
            agent_response = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": f"[{agent} OUTPUT]:\n{agent_response}"})

        # 📌 อัปเดต: สั่ง SUN ให้เลิกเป็นนักข่าว แล้วเป็นคนส่งของแทน
        final_instruction = {
            "role": "user", 
            "content": """ถึง SUN: คุณคือ 'น้องซัน' เลขาหน้าห้อง 
กฎการตอบ:
1. หากลูกค้าขอข้อมูล (เช่น ประวัติบริษัท, สคริปต์, ราคา) ให้คุณไปดึง 'เนื้อหาจริงๆ' ที่เพื่อนร่วมทีมพิมพ์ไว้ด้านบน มาตอบกลับลูกค้าโดยตรงทันที
2. ห้าม! เล่ากระบวนการทำงาน ห้ามบอกว่าใครทำอะไร (เช่น ห้ามพิมพ์ว่า 'NOTE แจ้งว่า...', 'TERRA วิเคราะห์ว่า...')
3. ห้ามพิมพ์ชื่อเพื่อนร่วมทีม หรือคำว่า [OUTPUT], PASS ออกมาให้เห็นเด็ดขาด
4. ปรับเนื้อหาให้เป็นระเบียบ อ่านง่าย พร้อมก๊อปปี้ไปส่งต่อใน LINE ได้เลย
5. ตอบด้วยความสุภาพ เป็นกันเอง และสั้นกระชับที่สุดเท่าที่ทำได้"""
        }
        internal_memory.append(final_instruction)
        return self._call_agent("SUN", internal_memory)

# ==========================================
# 🚀 ส่วนแสดงผลบนหน้าเว็บ Streamlit (Chat UI)
# ==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")
    st.title("☀️ น้อง SUN (JHD Secretary)")
    st.caption("พิมพ์ข้อความแล้วกด Enter เพื่อคุยกับระบบได้เลยครับ")

    try:
        API_KEY = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        st.error("⚠️ ไม่พบ API Key! กรุณาไปใส่ใน Settings > Secrets ของ Streamlit ครับ")
        st.stop()

    jhd_system = JHDAutomationSystem(API_KEY)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("💬 ทักทายหรือสั่งงานน้อง SUN ได้เลย..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("น้องซันกำลังไปค้นข้อมูลให้ค่ะ รอสักครู่นะคะ..."):
                result = jhd_system.run_full_workflow(prompt)
                st.markdown(result)
        
        st.session_state.messages.append({"role": "assistant", "content": result})
