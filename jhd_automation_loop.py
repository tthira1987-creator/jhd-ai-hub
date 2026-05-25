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
        # 1. จัดเรียงประวัติแชท
        chat_context = "--- ประวัติการสนทนา ---\n"
        for msg in chat_history[:-1]: 
            sender = "Lead" if msg["role"] == "user" else "น้อง SUN"
            chat_context += f"{sender}: {msg['content']}\n"
        
        latest_message = chat_history[-1]['content']
        internal_memory = [{"role": "user", "content": f"{chat_context}\n--- ข้อความล่าสุดจาก Lead: ---\n{latest_message}"}]
        
        # 2. ปรับการทำงานตามโหมด
        if mode == "Service Mode (Customer)":
            # โหมดบริการลูกค้า: NOTE ต้องคุม SOP / SUN ต้องเป็น Interface
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                # ให้ NOTE ทำหน้าที่คัดกรองงานเป็นหลัก
                instruction = f"ถึง {agent}: คุณอยู่ในโหมดบริการลูกค้า (Service Mode) 1. ตรวจสอบข้อมูล SOP Step 1 หากไม่ครบให้ร่างคำถามกลับมา 2. ห้ามข้ามไปเสนอราคา 3. ห้ามพูดภาษาระบบ"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            # สรุปให้ SUN พูด
            final_prompt = "ถึง SUN: คุณคือเลขาหน้าห้อง (Interface) ให้สรุปคำแนะนำจาก NOTE มาตอบลูกค้าด้วยภาษาที่เป็นธรรมชาติที่สุด ห้ามหลุดเรื่องระบบหลังบ้าน"
            
        else:
            # Internal Mode (โหมดใช้งานปกติ/Lead): ให้ทีมทำงานเต็มที่ ไม่ต้องมี Gatekeeper
            # ให้ NOTE/TERRA วิเคราะห์งานเหมือนเดิม
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode (โหมดทำงานกับ Lead) 1. ให้คำปรึกษาที่ลึกซึ้ง 2. วิเคราะห์งานได้เลยเต็มที่ 3. นำเสนอแนวทางแบบผู้เชี่ยวชาญได้ทันที ไม่ต้องถามข้อมูลเบื้องต้นซ้ำซ้อน"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            # สรุปให้ SUN พูดในฐานะทีมงาน
            final_prompt = "ถึง SUN: คุณคือสมาชิกทีมงาน JHD สรุปการวิเคราะห์ทั้งหมดจากเพื่อนร่วมทีมให้ Lead ทราบแบบมืออาชีพ สั้น กระชับ แม่นยำ"

        internal_memory.append({"role": "user", "content": final_prompt})
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
