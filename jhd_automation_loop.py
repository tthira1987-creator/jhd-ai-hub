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
                "jhd_company_core_terra.md", "jhd_master_sop_terra.md",
                "jhd_service_system_terra.md"
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

    def run_full_workflow(self, chat_history, mode):
        chat_context = "--- ประวัติการสนทนา ---\n"
        for msg in chat_history[:-1]: 
            sender = "Lead" if msg["role"] == "user" else "น้อง SUN"
            chat_context += f"{sender}: {msg['content']}\n"
        
        latest_message = chat_history[-1]['content']
        internal_memory = [{"role": "user", "content": f"{chat_context}\n--- ล่าสุด ---\n{latest_message}"}]
        
        # Internal Analysis (ไม่แสดงให้ลูกค้าเห็น)
        for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
            analysis = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})

        # SUN Response Formulation
        prompt_to_sun = f"""
        ถึง SUN: คุณคือ 'น้องซัน' เลขาหน้าห้อง
        
        โหมดใช้งาน: {mode}
        
        กฎการตอบสำหรับ Service Mode (Customer):
        1. **ห้ามพูดภาษาระบบ** (ห้ามพูดเรื่อง Job Type, Priority, Confidence Score) ให้พูดเหมือนเลขาฯ คุยกับลูกค้า
        2. **ตรวจสอบข้อมูล SOP Step 1**: หากข้อมูล (ชื่อร้าน, สิ่งที่ทำ, ขนาด, งบ) ยังไม่ครบ ห้ามสรุปงาน ให้ถามหาข้อมูลที่ขาดไปอย่างสุภาพจนกว่าจะครบ
        3. **ถ้าข้อมูลครบ**: ให้ใช้ข้อมูลที่เพื่อนร่วมทีมวิเคราะห์มา สรุปตอบลูกค้าแบบเป็นธรรมชาติที่สุด
        4. ห้ามมีคำว่า [SUN OUTPUT] หรือ [Analysis] หลุดออกมา
        
        กฎการตอบสำหรับ Internal Mode (Lead):
        1. รายงานผลสรุปงานแบบมืออาชีพ สั้น กระชับ แม่นยำ
        """
        
        internal_memory.append({"role": "user", "content": prompt_to_sun})
        return self._call_agent("SUN", internal_memory)

if __name__ == "__main__":
    st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")
    st.sidebar.title("⚙️ System Control")
    mode = st.sidebar.radio("สถานะโหมดใช้งาน:", ["Internal Mode (Lead)", "Service Mode (Customer)"])
    st.title("☀️ น้อง SUN (JHD Secretary)")
    
    try:
        API_KEY = st.secrets["OPENROUTER_API_KEY"]
    except:
        st.error("⚠️ API Key Error")
        st.stop()

    jhd_system = JHDAutomationSystem(API_KEY)
    if "messages" not in st.session_state: st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("💬..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("น้องซันกำลังประมวลผล..."):
                result = jhd_system.run_full_workflow(st.session_state.messages, mode)
                st.markdown(result)
        st.session_state.messages.append({"role": "assistant", "content": result})
