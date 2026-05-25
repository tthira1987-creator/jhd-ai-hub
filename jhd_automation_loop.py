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
        self.agent_files = {
            "SUN": ["jhd_persona_sun.md", "jhd_role_sun.md"],
            "NOTE": ["jhd_persona_note.md", "jhd_role_note.md", "jhd_formula_pricing_note.md"],
            "TERRA": ["jhd_persona_terra.md", "jhd_role_terra.md"],
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
        
        # ปล่อยให้บอทคุยกันหลังบ้าน
        for agent in workflow_sequence:
            trigger_msg = {"role": "user", "content": f"ถึง {agent}: หากนี่คือการทักทายเฉยๆ ให้ตอบสั้นๆ ว่ารับทราบ แต่ถ้ามีบรีฟงาน โปรดวิเคราะห์ตามหน้าที่ของคุณ"}
            internal_memory.append(trigger_msg)
            agent_response = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": f"[{agent} OUTPUT]:\n{agent_response}"})

        # บังคับให้ SUN แปลงสารเป็นภาษามนุษย์ (เลขาหน้าห้อง)
        final_instruction = {
            "role": "user", 
            "content": "ถึง SUN: คุณคือ 'เลขาหน้าห้อง' โปรดอ่านข้อมูลทั้งหมดด้านบน แล้วพิมพ์ตอบกลับผู้ใช้งานด้วยความเป็นกันเอง สุภาพ เหมือนมนุษย์คุยกัน (มีหางเสียง) \n- ถ้าผู้ใช้แค่ทักทาย: ให้สวัสดีตอบและถามอย่างสุภาพว่ามีอะไรให้ช่วยเหลือไหม\n- ถ้าเป็นการสั่งงาน: ให้สรุปผลแบบภาษามนุษย์\n- กฎเหล็ก: ห้ามแสดงข้อความเชิงระบบ (เช่น [SUN OUTPUT], ข้อมูลโค้ด, Priority, หรือการอธิบายกระบวนการ) ออกมาเด็ดขาด!"
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

    # ดึง API Key
    try:
        API_KEY = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        st.error("⚠️ ไม่พบ API Key! กรุณาไปใส่ใน Settings > Secrets ของ Streamlit ครับ")
        st.stop()

    jhd_system = JHDAutomationSystem(API_KEY)

    # สร้างระบบจำประวัติการแชท (Memory)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # แสดงประวัติการแชทเก่าๆ บนจอ
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ช่องพิมพ์ข้อความแบบ Chat (พิมพ์ปุ๊บ กด Enter ส่งได้เลย)
    if prompt := st.chat_input("💬 ทักทายหรือสั่งงานน้อง SUN ได้เลย..."):
        
        # โชว์ข้อความฝั่งเรา (User)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # โชว์ข้อความฝั่ง AI พร้อมโหลดหมุนๆ
        with st.chat_message("assistant"):
            with st.spinner("น้องซันกำลังรับเรื่องค่ะ รอสักครู่นะคะ..."):
                result = jhd_system.run_full_workflow(prompt)
                st.markdown(result)
        
        # บันทึกข้อความ AI ลงประวัติเพื่อจำบทสนทนา
        st.session_state.messages.append({"role": "assistant", "content": result})
