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
        chat_context = "--- ประวัติการสนทนาที่ผ่านมา ---\n"
        for msg in chat_history[:-1]: 
            sender = "Lead" if msg["role"] == "user" else "น้อง SUN"
            chat_context += f"{sender}: {msg['content']}\n"
        
        latest_message = chat_history[-1]['content']
        full_prompt = f"{chat_context}\n--- ข้อความล่าสุด ---\nLead ได้พิมพ์มาว่า: {latest_message}"
        internal_memory = [{"role": "user", "content": full_prompt}]
        workflow_sequence = ["SUN", "NOTE", "TERRA", "NAVARA", "BIGM"]
        
        mode_instruction = ""
        if mode == "Service Mode (Customer)":
            mode_instruction = """
ถึงทุกคน: ขณะนี้เราอยู่ใน 'Service Mode' (โหมดคุยกับลูกค้า)
กฎเหล็ก: 
1. ตรวจสอบว่าข้อมูลเบื้องต้น (SOP Step 1: ชื่อ, ประเภทงาน, ขนาด, งบ) ครบถ้วนหรือไม่
2. หากไม่ครบ: ต้องเป็นฝ่ายถามข้อมูลให้ครบ ห้ามข้ามขั้นตอน
3. หากข้อมูลครบแล้ว: ให้วิเคราะห์ตามหน้าที่ของตัวคุณ
4. ห้ามหลุดคำว่า [OUTPUT] หรือ [SUN OUTPUT] เด็ดขาด"""
        else:
            mode_instruction = "ถึงทุกคน: ขณะนี้อยู่ใน 'Internal Mode' (โหมดคุยกับ Lead) คุณคือทีมงานคุณภาพ ปฏิบัติภารกิจงานที่ Lead สั่งได้ทันที"

        for agent in workflow_sequence:
            trigger_msg = {"role": "user", "content": f"{mode_instruction}\n\nถึง {agent}: วิเคราะห์และตอบคำถามล่าสุด หากไม่เกี่ยวข้องกับหน้าที่ของคุณให้ตอบว่า 'PASS'"}
            internal_memory.append(trigger_msg)
            agent_response = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": agent_response})

        final_instruction = {
            "role": "user", 
            "content": """ถึง SUN: คุณคือ 'น้องซัน' เลขาหน้าห้อง 
กฎการตอบ:
1. สรุปผลจากทีมงานให้ตรงคำถามที่สุด ตอบแบบยืดหยุ่น เป็นธรรมชาติ
2. ห้ามอธิบายกระบวนการทำงานหลังบ้าน ห้ามบอกว่าใครทำอะไร
3. 🚨 ห้ามมีคำว่า [SUN OUTPUT]:, [OUTPUT], หรือ PASS เด็ดขาด!
4. ตอบด้วยความสุภาพ มืออาชีพ และมั่นใจ ไม่ต้องเรียกผู้ใช้ว่าเจ้านาย ให้เรียกแทนตัวว่าคุณ หรือเรียก Lead"""
        }
        internal_memory.append(final_instruction)
        return self._call_agent("SUN", internal_memory)

if __name__ == "__main__":
    st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")
    
    st.sidebar.title("⚙️ System Control")
    mode = st.sidebar.radio("สถานะโหมดใช้งาน:", ["Internal Mode (Lead)", "Service Mode (Customer)"])
    
    st.title("☀️ น้อง SUN (JHD Secretary)")
    st.caption(f"Status: {mode}")

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

    if prompt := st.chat_input("💬 พิมพ์คุยกับน้อง SUN..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("น้องซันกำลังประมวลผล..."):
                result = jhd_system.run_full_workflow(st.session_state.messages, mode)
                st.markdown(result)
        
        st.session_state.messages.append({"role": "assistant", "content": result})
