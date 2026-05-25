import os
import streamlit as st
from openai import OpenAI

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
                "jhd_script_sales_note.md", "jhd_script_quick_reply_note.md",
                "jhd_sales_intelligence_note.md", "jhd_sales_strategy_note.md",
                "jhd_sales_framework_note.md"
            ],
            "TERRA": [
                "jhd_persona_terra.md", "jhd_role_terra.md", 
                "jhd_company_core_terra.md", "jhd_master_sop_terra.md", "jhd_service_system_terra.md"
            ],
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

    def run_full_workflow(self, chat_history):
        chat_context = "--- ประวัติการสนทนาที่ผ่านมา ---\n"
        for msg in chat_history[:-1]: 
            sender = "เจ้านาย" if msg["role"] == "user" else "น้อง SUN"
            chat_context += f"{sender}: {msg['content']}\n"
        
        latest_message = chat_history[-1]['content']
        
        full_prompt = f"{chat_context}\n--- ข้อความล่าสุด ---\nเจ้านายพิมพ์มาว่า: {latest_message}"
        internal_memory = [{"role": "user", "content": full_prompt}]
        workflow_sequence = ["SUN", "NOTE", "TERRA", "NAVARA", "BIGM"]
        
        for agent in workflow_sequence:
            trigger_msg = {
                "role": "user", 
                "content": f"ถึง {agent}: โปรดแยกแยะข้อความล่าสุด... 1) หากเป็นการ 'ถามข้อมูลทั่วไป/ถามคำศัพท์' ที่มีในคู่มือ ให้คุณอธิบายตอบไปตรงๆ แบบยืดหยุ่น 2) หากเป็นการ 'สั่งวิเคราะห์ลูกค้า/หน้างาน' ให้ใช้ Format มาตรฐานแบบจัดเต็ม 3) หากไม่เกี่ยวกับหน้าที่คุณ ให้ตอบ 'PASS' คำเดียว"
            }
            internal_memory.append(trigger_msg)
            agent_response = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": f"[{agent} OUTPUT]:\n{agent_response}"})

        final_instruction = {
            "role": "user", 
            "content": """ถึง SUN: คุณคือ 'น้องซัน' เลขาหน้าห้อง 
กฎการตอบ:
1. อ่านข้อมูลจากเพื่อนร่วมทีมและสรุปตอบเจ้านายให้ตรงคำถามที่สุด ตอบแบบยืดหยุ่น คุยเป็นธรรมชาติเหมือนมนุษย์
2. ห้ามอธิบายกระบวนการทำงานหลังบ้าน ห้ามบอกว่าใครทำอะไร
3. 🚨 กฎเหล็กสูงสุด: ห้ามมีคำว่า [SUN OUTPUT]:, [OUTPUT], หรือ PASS หลุดออกมาในข้อความเด็ดขาด!
4. ตอบด้วยความสุภาพ เป็นกันเอง"""
        }
        internal_memory.append(final_instruction)
        return self._call_agent("SUN", internal_memory)

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
                result = jhd_system.run_full_workflow(st.session_state.messages)
                st.markdown(result)
        
        st.session_state.messages.append({"role": "assistant", "content": result})
