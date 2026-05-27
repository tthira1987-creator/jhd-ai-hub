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
        speaker = "คุณลูกค้า" if mode == "Service Mode (Customer)" else "Lead"
        
        # 1. ดึงประวัติแชทย้อนหลัง (แก้โรคความจำสั้น ให้ AI จำบริบทได้)
        recent_history = chat_history[-6:] # ดึง 6 ข้อความล่าสุด
        chat_context = "\n".join([f"{'SUN' if msg['role'] == 'assistant' else speaker}: {msg['content']}" for msg in recent_history])

        if mode == "Service Mode (Customer)":
            internal_memory = [{"role": "user", "content": f"นี่คือประวัติการสนทนาล่าสุด:\n{chat_context}"}]
            
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                # 2. ปลดล็อก SOP สั่งให้กล้าเสนอราคาและห้ามถามซ้ำ
                instruction = f"ถึง {agent}: วิเคราะห์แชทล่าสุด กฎพิเศษ: อนุญาตให้ 'ประเมินราคาคร่าวๆ หรือแนะนำแพ็กเกจ (A/B/C)' ให้ลูกค้าทราบได้ทันทีแม้ข้อมูลไม่ครบ (การประเมินเบื้องต้นไม่ผิด SOP) ห้ามทำตัวเป็นหุ่นยนต์ลิสต์คำถาม 1-5 ห้ามถามข้อมูลที่ลูกค้าเคยให้มาแล้วในประวัติแชท"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: ตอนนี้คุณคือ "แอดมินบริการลูกค้า" ยึดกฎเหล็กนี้:
            1. ตอบสิ่งลูกค้าอยากรู้ก่อนทันที: หากลูกค้าถามราคา/แพ็กเกจ ให้บอกช่วงราคาคร่าวๆ หรือแนะนำแพ็กเกจให้เห็นภาพก่อนเสมอ ห้ามอ้างว่าข้อมูลไม่ครบแล้วกั๊กข้อมูล
            2. เป็นธรรมชาติเหมือนมนุษย์: จำข้อมูลที่ลูกค้าพิมพ์มาแล้ว (ชื่อ, ขนาด, วัสดุ) ห้ามทวนถามซ้ำเด็ดขาด 
            3. ห้ามสอบสวนลูกค้า: หากต้องขอข้อมูลเพิ่ม ให้เนียนถามต่อท้ายทีละ 1-2 ข้อแบบชวนคุย ห้ามลิสต์เป็นข้อ 1-5 ยาวๆ 
            4. การจัดรูปแบบ: หากมีการอธิบายตัวเลือกให้ขึ้นบรรทัดใหม่ และใช้ [SPLIT] คั่นแบ่งกล่องข้อความให้สวยงาม"""
            
        else:
            # โหมด Internal
            internal_memory = [{"role": "user", "content": f"นี่คือประวัติการสนทนาล่าสุด:\n{chat_context}"}]
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode อ่านประวัติแชทและสรุปข้อมูลให้ตรงประเด็น ฟันธงมาเลย"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: สรุปข้อมูลเพื่อตอบ Lead โดยทำตามกฎนี้:
            1. ตอบเข้าประเด็นทันที ห้ามทักทายซ้ำซาก
            2. หากมีการแจกแจง ต้องขึ้นบรรทัดใหม่
            3. แบ่งกล่องข้อความใช้ [SPLIT] คั่น"""

        internal_memory.append({"role": "user", "content": final_prompt})
        return self._call_agent("SUN", internal_memory)
