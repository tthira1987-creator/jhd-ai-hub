import os
from openai import OpenAI

class JHDWorkflowManager:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        self.model = "google/gemini-2.5-flash"
        
        self.agent_files = {
            "SUN": ["jhd_persona_sun.md", "jhd_role_sun.md"],
            "NOTE": [
                "NOTE": [
                "jhd_persona_note.md",          # นิสัยและคาแรคเตอร์
                "jhd_role_note.md",             # หน้าที่และขอบเขตงาน
                "jhd_formula_pricing_note.md",  # สูตรคำนวณราคา (รอกลับมาเติม)
                "jhd_company_pitch_note.md",    # ข้อมูลจุดเด่นบริษัท
                "jhd_team_manual_note.md"       # 🌟 คัมภีร์หลัก (รวมทุกอย่างไว้ที่นี่)
            ],
            "TERRA": [
                "jhd_persona_terra.md", "jhd_role_terra.md", 
                "jhd_company_core_terra.md", "jhd_master_sop_terra.md",
                "jhd_service_system_terra.md"
            ],
            "NAVARA": [
                "jhd_persona_navara.md", "jhd_role_navara.md"
            ],
            "BIGM": [
                "jhd_persona_bigm.md", "jhd_role_bigm.md"
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
        # 1. ดึงประวัติแชทย้อนหลัง (ให้ AI จำบริบทได้ ไม่ถามซ้ำ)
        recent_history = chat_history[-6:]
        
        if mode == "Service Mode (Customer)":
            # จัดรูปแบบแชทให้ SUN รู้ว่านี่คือการคุยกับ "ลูกค้า"
            chat_context = "\n".join([f"{'แอดมิน JHD' if msg['role'] == 'assistant' else 'ลูกค้า'}: {msg['content']}" for msg in recent_history])
            
            # ให้ NOTE แอบวิเคราะห์ราคาและแพ็กเกจอยู่หลังบ้าน (เงียบๆ)
            note_instruction = f"วิเคราะห์ลูกค้าจากแชทนี้:\n{chat_context}\nให้ประเมินแพ็กเกจ (A/B/C) และราคาคร่าวๆ หรือระบุสิ่งที่ต้องถามเพิ่มสั้นๆ"
            note_analysis = self._call_agent("NOTE", [{"role": "user", "content": note_instruction}])
            
            # บังคับสมอง SUN ให้เป็นแอดมินขายของ 100%
            final_prompt = f"""จากประวัติการคุยกับลูกค้าด้านล่างนี้:
            {chat_context}
            
            ข้อมูลสนับสนุนจากฝ่ายขาย (ห้ามบอกลูกค้าว่ามีข้อมูลนี้): {note_analysis}
            
            หน้าที่ของคุณ: พิมพ์ "ตอบลูกค้า" ในฐานะ "แอดมินบริการลูกค้าของ JHD"
            กฎเหล็กขั้นสูงสุด (Strict Rules) ที่ต้องทำตาม:
            1. 🛑 ห้ามหลุดคำว่า "Lead", "NOTE", "TERRA", "NAVARA", "BIGM" หรือ "Sub Agent" ออกมาเด็ดขาด!
            2. 🛑 ห้ามรายงานผล หรือพิมพ์สรุปการทำงานแบบ AI ให้พิมพ์คุยเหมือนมนุษย์(แอดมิน) คุยกับลูกค้าจริงๆ
            3. 💰 กล้าเสนอราคา: ให้นำข้อมูลจากฝ่ายขายมา "เสนอแพ็กเกจ (A/B/C) และบอกราคาคร่าวๆ" ให้ลูกค้าทราบทันที ไม่ต้องรอให้ข้อมูลครบ 100%
            4. 🗣️ ความเป็นธรรมชาติ: จำข้อมูลที่ลูกค้าเคยบอกไว้ ห้ามถามซ้ำ! หากต้องขอข้อมูลเพิ่ม (เช่น ขนาด, หน้างาน) ให้เนียนถามต่อท้ายทีละ 1-2 ข้อ ห้ามทำตัวเป็นหุ่นยนต์ลิสต์คำถาม 1-5 ข้อเด็ดขาด
            5. 📦 ใช้ [SPLIT] คั่นกล่องข้อความให้อ่านง่าย
            
            พิมพ์ข้อความตอบลูกค้าได้เลย:"""
            
            return self._call_agent("SUN", [{"role": "user", "content": final_prompt}])
            
        else:
            # ==========================================
            # โหมด Internal (Lead) - ให้ทีมงานประชุมกันตามปกติ
            # ==========================================
            speaker = "Lead"
            chat_context = "\n".join([f"{'SUN' if msg['role'] == 'assistant' else speaker}: {msg['content']}" for msg in recent_history])
            internal_memory = [{"role": "user", "content": f"นี่คือประวัติการสนทนา:\n{chat_context}"}]
            
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: วิเคราะห์ข้อมูลจากแชทล่าสุดให้ Lead"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: สรุปข้อมูลทั้งหมดจาก Sub-Agent เพื่อรายงาน Lead (คุณออฟ)
            1. ตอบเข้าประเด็นทันที ห้ามทักทายซ้ำซาก
            2. หากมีการแจกแจง ต้องขึ้นบรรทัดใหม่
            3. แบ่งกล่องข้อความใช้ [SPLIT] คั่น"""
            
            internal_memory.append({"role": "user", "content": final_prompt})
            return self._call_agent("SUN", internal_memory)
