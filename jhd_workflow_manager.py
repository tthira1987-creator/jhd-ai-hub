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
                "jhd_sales_framework_note.md", "jhd_product_jhd3dletter.md",
                "jhd_product_jhd_hybrid_letter.md", "jhd_product_jhd_standard_letter.md"
            ],
            "TERRA": [
                "jhd_persona_terra.md", "jhd_role_terra.md", 
                "jhd_company_core_terra.md", "jhd_master_sop_terra.md",
                "jhd_service_system_terra.md", "jhd_product_jhd3dletter.md",
                "jhd_product_jhd_hybrid_letter.md", "jhd_product_jhd_standard_letter.md"
            ],
            "NAVARA": [
                "jhd_persona_navara.md", "jhd_role_navara.md", "jhd_product_jhd3dletter.md",
                "jhd_product_jhd_hybrid_letter.md", "jhd_product_jhd_standard_letter.md"
            ],
            "BIGM": [
                "jhd_persona_bigm.md", "jhd_role_bigm.md", "jhd_product_jhd3dletter.md",
                "jhd_product_jhd_hybrid_letter.md", "jhd_product_jhd_standard_letter.md"
            ]
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
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: วิเคราะห์ข้อมูลลูกค้าตาม SOP Step 1 โดยให้เสนอ 'ราคาประเมินเบื้องต้น' ทันทีที่ทำได้ คุยให้กระชับที่สุด"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: สรุปคำแนะนำจากทีมงานเพื่อตอบลูกค้า โดยต้องทำตามกฎนี้เคร่งครัด:
            1. ห้ามกล่าวสวัสดีซ้ำเด็ดขาด
            2. รวมประโยคที่เกี่ยวข้องกันไว้ด้วยกัน ห้ามหั่นข้อความถี่ยิบเด็ดขาด ให้ตอบสูงสุดไม่เกิน 2-3 กล่องข้อความ (ใช้ [SPLIT] คั่นสูงสุดแค่ 1-2 ครั้งเท่านั้น)
            3. ห้ามอธิบายการทำงานของระบบ เข้าประเด็นทันที"""
            
        else:
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode ให้คำปรึกษา Lead แบบกระชับที่สุด ฟันธงมาเลย ไม่ต้องอธิบายน้ำท่วมทุ่ง"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: สรุปข้อมูลจากทีมงานเพื่อตอบ Lead โดยต้องทำตามกฎนี้เคร่งครัด:
            1. ห้ามกล่าวสวัสดีซ้ำเด็ดขาด เข้าประเด็นทันที
            2. ห้ามหั่นประโยคสั้นเกินไป (เช่น ห้ามแยกคำว่า "Lead ครับ" ออกมาเดี่ยวๆ) ให้รวมใจความไว้ด้วยกัน ตอบสูงสุดไม่เกิน 2-3 กล่องข้อความ (ใช้ [SPLIT] คั่นสูงสุดแค่ 1-2 ครั้ง)
            3. ตอบให้ตรงคำถามที่สุด ถ้าขอตัวเลือกที่ถูกสุด ให้ตอบชื่อรุ่นและราคามาเลย ไม่ต้องอธิบายยืดยาว"""

        internal_memory.append({"role": "user", "content": final_prompt})
        return self._call_agent("SUN", internal_memory)
