import os
from openai import OpenAI

class JHDWorkflowManager:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        self.model = "google/gemini-2.5-flash"
       self.agent_files = {
            "SUN": ["jhd_persona_sun.md", "jhd_role_sun.md"],
            "NOTE": [
                "jhd_persona_note.md", "jhd_role_note.md", 
                "jhd_formula_pricing_note.md", "jhd_company_pitch_note.md", 
                "jhd_script_sales_note.md", "jhd_script_quick_reply_note.md",
                "jhd_sales_intelligence_note.md", "jhd_sales_strategy_note.md",
                "jhd_sales_framework_note.md", "jhd_product_jhd3dletter.md"  # <--- เพิ่มตรงนี้
            ],
            "TERRA": [
                "jhd_persona_terra.md", "jhd_role_terra.md", 
                "jhd_company_core_terra.md", "jhd_master_sop_terra.md",
                "jhd_service_system_terra.md", "jhd_product_jhd3dletter.md"  # <--- เพิ่มตรงนี้
            ],
            "NAVARA": ["jhd_persona_navara.md", "jhd_role_navara.md", "jhd_product_jhd3dletter.md"], # <--- เพิ่มตรงนี้
            "BIGM": ["jhd_persona_bigm.md", "jhd_role_bigm.md", "jhd_product_jhd3dletter.md"]        # <--- เพิ่มตรงนี้
        }

    def _load_system_prompt(self, agent_name):
        prompt = f"คุณคือ {agent_name} หนึ่งในทีม JHD Intelligence System\n\n"
        for file in self.agent_files.get(agent_name, []):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    prompt += f.read() + "\n\n"
            except FileNotFoundError: pass
        return prompt

    def _call_agent(self, agent_name, context_history):
        system_prompt = self._load_system_prompt(agent_name)
        messages = [{"role": "system", "content": system_prompt}] + context_history
        response = self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=1500, temperature=0.7)
        return response.choices[0].message.content

    def run_workflow(self, chat_history, mode):
        latest_message = chat_history[-1]['content']
        internal_memory = [{"role": "user", "content": f"Lead/ลูกค้า ถามว่า: {latest_message}"}]

        if mode == "Service Mode (Customer)":
            # NOTE คุม SOP
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: วิเคราะห์ข้อมูลลูกค้าตาม SOP Step 1 หากไม่ครบให้ร่างคำถามกลับมา อย่าเพิ่งเสนอราคา"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            final_prompt = "ถึง SUN: สรุปคำแนะนำจาก NOTE มาตอบลูกค้าให้ดูเป็นธรรมชาติที่สุด ห้ามพูดเรื่องระบบ"
        else:
            # Internal Mode
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode (โหมดทำงานกับ Lead) 1. ให้คำปรึกษาที่ลึกซึ้ง 2. วิเคราะห์งานได้เลยเต็มที่ ไม่ต้องถามข้อมูลเบื้องต้นซ้ำซ้อน"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            final_prompt = "ถึง SUN: ตอบคำถามของ Lead ในฐานะเลขาฯ มืออาชีพ โดยใช้ความรู้จากทีมงานตอบให้ตรงประเด็น ยืดหยุ่น เป็นธรรมชาติ"

        internal_memory.append({"role": "user", "content": final_prompt})
        return self._call_agent("SUN", internal_memory)
