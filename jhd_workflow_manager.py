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
                # สอนมารยาทรับแขก: ถ้าทักทายเฉยๆ อย่าเพิ่งรัวคำถาม
                instruction = f"ถึง {agent}: วิเคราะห์ข้อความลูกค้า หากลูกค้าเพียงแค่ทักทาย (เช่น สวัสดี) ให้เตรียมข้อความต้อนรับและถามความต้องการเบื้องต้น ห้ามรัวคำถามสเปกยาวๆ เด็ดขาด! แต่หากลูกค้าเริ่มบรีฟงานแล้ว ค่อยวิเคราะห์ตาม SOP Step 1 (ต้องขอชื่อ/เบอร์โทรด้วย) คุยให้กระชับที่สุด"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            # ดักคอ SUN โหมดลูกค้า (บังคับขึ้นบรรทัดใหม่)
            final_prompt = """ถึง SUN: ตอนนี้คุณคือ "แอดมินบริการลูกค้า" กำลังตอบแชท "ลูกค้า" ให้แปลงข้อมูลจากทีมงานเป็นข้อความตอบลูกค้าที่สุภาพ โดยยึดกฎเหล็กนี้:
            1. มารยาทพื้นฐาน: หากลูกค้าเพิ่งทักทาย (เช่น "สวัสดีครับ") ให้ทักทายกลับอย่างเป็นมิตรและถามว่าสนใจงานป้ายประเภทไหน หรือมีอะไรให้ช่วย (ห้ามส่งลิสต์คำถามยาวๆ เด็ดขาด)
            2. การเรียกชื่อ: หากลูกค้าแจ้งชื่อ ให้เรียกชื่อลูกค้าเสมอ หากยังไม่ทราบ ให้เรียก "คุณลูกค้า"
            3. การจัดรูปแบบ (บังคับขั้นเด็ดขาด!): หากมีการพิมพ์ข้อความที่เป็นข้อๆ (1., 2., 3.) "ต้องขึ้นบรรทัดใหม่เสมอ" ห้ามพิมพ์ติดกันเป็นพรืดยาวๆ ในย่อหน้าเดียวเด็ดขาด!
            4. การแบ่งกล่องข้อความ: ใช้ [SPLIT] คั่นเพื่อแบ่งกล่องให้เป็นธรรมชาติ อนุญาตให้แบ่ง 2-3 กล่อง"""
            
        else:
            # Internal Mode
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode ให้คำปรึกษา Lead แบบกระชับที่สุด (หากข้อความของ Lead เป็นเพียงการทักทายเฉยๆ ไม่ต้องพยายามวิเคราะห์งานหรือทวงถามข้อมูล ให้ข้ามไปเลย)"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            # ดักคอ SUN โหมด Lead 
            final_prompt = """ถึง SUN: สรุปข้อมูลจากทีมงานเพื่อตอบ Lead โดยต้องทำตามกฎนี้เคร่งครัด:
            1. มารยาทการทักทาย: หาก Lead พิมพ์มาแค่ทักทาย (เช่น "สวัสดี") ให้ตอบรับแบบผู้ช่วยส่วนตัว เช่น "สวัสดีครับ Lead วันนี้มีโปรเจกต์อะไรให้ทีมงานช่วยดูแลไหมครับ" (ห้ามรายงานว่าขาดข้อมูลงาน)
            2. การเข้าประเด็น: แต่หาก Lead สั่งงาน ให้ตอบตรงประเด็นทันที ห้ามเกริ่นนำทักทายซ้ำ
            3. การจัดรูปแบบข้อความ (บังคับขั้นเด็ดขาด!): หากมีการแจกแจงตัวเลือก หรือลิสต์เป็นข้อๆ "ต้องขึ้นบรรทัดใหม่เสมอ" ห้ามพิมพ์ติดกันเป็นก้อนเดียว
            4. การแบ่งกล่องข้อความ: แบ่งกล่องข้อความสูงสุด 2-3 กล่อง (ใช้ [SPLIT] คั่น)"""

        internal_memory.append({"role": "user", "content": final_prompt})
        return self._call_agent("SUN", internal_memory)
