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
        
        # 1. แยกว่าใครเป็นคนคุย เพื่อตัดคำว่า Lead ออกจากสมอง AI ในโหมดลูกค้า
        speaker = "คุณลูกค้า" if mode == "Service Mode (Customer)" else "Lead"
        internal_memory = [{"role": "user", "content": f"{speaker} พิมพ์มาว่า: {latest_message}"}]

        if mode == "Service Mode (Customer)":
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: วิเคราะห์ข้อมูลลูกค้าตาม SOP Step 1 เสนอราคาประเมินเบื้องต้นถ้าทำได้ คุยให้กระชับที่สุด"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            # 2. ดักคอ SUN โหมดลูกค้า
            final_prompt = """ถึง SUN: ตอนนี้คุณคือ "แอดมินบริการลูกค้า" กำลังตอบแชท "ลูกค้า" โดยตรง ให้แปลงข้อมูลวิเคราะห์จากทีมงานเป็นข้อความตอบลูกค้าที่สุภาพและจัดบรรทัดให้อ่านง่าย โดยยึดกฎเหล็กนี้:
            1. สรรพนาม: เรียกผู้สนทนาว่า "คุณลูกค้า" (ห้ามหลุดคำว่า Lead หรือรายงานหลังบ้านเด็ดขาด)
            2. การจัดรูปแบบข้อความ (สำคัญมาก): หากต้องถามข้อมูลลูกค้าหลายข้อ ให้ขึ้นบรรทัดใหม่ (Enter) เป็นข้อ 1., 2., 3. ให้อ่านง่าย ห้ามพิมพ์ติดกันเป็นพรืดยาวๆ
            3. การแบ่งกล่องข้อความ: ใช้ [SPLIT] คั่นเพื่อแบ่งกล่องให้เป็นธรรมชาติ อนุญาตให้แบ่งได้ 2-4 กล่อง เช่น:
               (ข้อความเกริ่นนำ) [SPLIT] 
               (ข้อความคำถามที่จัดเรียงบรรทัดแล้ว) [SPLIT] 
               (ข้อความลงท้าย)"""
            
        else:
            # Internal Mode
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode ให้คำปรึกษา Lead แบบกระชับที่สุด ฟันธงมาเลย ไม่ต้องอธิบายน้ำท่วมทุ่ง"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            # ดักคอ SUN โหมด Lead (อัปเดตเรื่องการจัดบรรทัด)
            final_prompt = """ถึง SUN: สรุปข้อมูลจากทีมงานเพื่อตอบ Lead โดยต้องทำตามกฎนี้เคร่งครัด:
            1. ห้ามกล่าวสวัสดีซ้ำเด็ดขาด เข้าประเด็นทันที
            2. การจัดรูปแบบข้อความ (สำคัญมาก): หากมีการแจกแจงตัวเลือก, สรุปประเด็น, หรือลิสต์ข้อมูล ให้ขึ้นบรรทัดใหม่ (Enter) และใช้ Bullet/ตัวเลข เสมอ ห้ามพิมพ์ติดกันเป็นก้อนเดียว
            3. การแบ่งกล่องข้อความ: ให้รวมใจความที่เกี่ยวข้องกันไว้ในกล่องเดียวกัน แบ่งกล่องข้อความสูงสุด 2-4 กล่อง (ใช้ [SPLIT] คั่น)
            4. ตอบให้ตรงคำถามที่สุด ถ้าขอตัวเลือกที่ถูกสุด ให้ตอบชื่อรุ่นและราคามาเลย ไม่ต้องอธิบายยืดยาว"""

        internal_memory.append({"role": "user", "content": final_prompt})
        return self._call_agent("SUN", internal_memory)
