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
            "NOTE": [
                "jhd_persona_note.md", "jhd_role_note.md", 
                "jhd_formula_pricing_note.md", "jhd_company_pitch_note.md", 
                "jhd_script_sales_note.md", "jhd_script_quick_reply_note.md" ,
                "jhd_sales_intelligence_note.md", "jhd_sales_strategy_note.md", "jhd_sales_framework_note.md"
            ],
            "TERRA": ["jhd_persona_terra.md", "jhd_role_terra.md", "jhd_company_core_terra.md", "jhd_master_sop_terra.md"],
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

    # 📌 อัปเดต: เปลี่ยนจากการรับแค่คำสั่งเดียว เป็นรับ "ประวัติแชททั้งหมด"
    def run_full_workflow(self, chat_history):
        # 1. จัดเรียงประวัติแชทให้บอทอ่านง่ายๆ
        chat_context = "--- ประวัติการสนทนาที่ผ่านมา ---\n"
        for msg in chat_history[:-1]: # ดึงมาหมดยกเว้นข้อความล่าสุด
            sender = "เจ้านาย/ลูกค้า" if msg["role"] == "user" else "น้อง SUN"
            chat_context += f"{sender}: {msg['content']}\n"
        
        latest_message = chat_history[-1]['content']
        
        # 2. ป้อนข้อมูลให้ห้องประชุมหลังบ้าน
        full_prompt = f"{chat_context}\n--- ข้อความล่าสุด ---\nเจ้านาย/ลูกค้าพิมพ์มาว่า: {latest_message}"
        internal_memory = [{"role": "user", "content": full_prompt}]
        workflow_sequence = ["SUN", "NOTE", "TERRA", "NAVARA", "BIGM"]
        
        for agent in workflow_sequence:
            trigger_msg = {
                "role": "user", 
                "content": f"ถึง {agent}: ให้อ่าน 'ประวัติการสนทนา' และ 'ข้อความล่าสุด' ด้านบน หากคำสั่งล่าสุดเกี่ยวเนื่องกับหน้าที่ของคุณหรือต่อเนื่องจากเรื่องเดิม ให้ดึงข้อมูลมาตอบให้ครบถ้วน แต่หากไม่เกี่ยวกับหน้าที่คุณเลย ให้ตอบแค่คำว่า 'PASS'"
            }
            internal_memory.append(trigger_msg)
            agent_response = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": f"[{agent} OUTPUT]:\n{agent_response}"})

        final_instruction = {
            "role": "user", 
            "content": """ถึง SUN: คุณคือ 'น้องซัน' เลขาหน้าห้อง 
กฎการตอบ:
1. ให้อ่านผลลัพธ์จากเพื่อนร่วมทีม ถ้ามีข้อมูลตรงกับคำถามล่าสุด ให้เอามาตอบ
2. หากเป็นบทสนทนาต่อเนื่อง ให้ตอบให้ลื่นไหลไปกับประวัติการคุยเดิม
3. ห้ามอธิบายกระบวนการทำงาน ห้ามบอกว่าใครทำอะไร
4. ห้ามพิมพ์ชื่อเพื่อนร่วมทีม หรือคำว่า [OUTPUT], PASS
5. ตอบด้วยความสุภาพ เป็นกันเอง และสั้นกระชับ"""
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
            with st.spinner("น้องซันกำลังประมวลผล รอสักครู่นะคะ..."):
                # 📌 อัปเดต: โยนก้อนประวัติแชท (messages) ทั้งหมดเข้าไปในระบบ
                result = jhd_system.run_full_workflow(st.session_state.messages)
                st.markdown(result)
        
        st.session_state.messages.append({"role": "assistant", "content": result})
