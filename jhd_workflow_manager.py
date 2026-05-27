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
        latest_message = chat_history[-1]['content']
        
        speaker = "คุณลูกค้า" if mode == "Service Mode (Customer)" else "Lead"
        internal_memory = [{"role": "user", "content": f"{speaker} พิมพ์มาว่า: {latest_message}"}]

        if mode == "Service Mode (Customer)":
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                # อัปเดต: สั่งให้กล้าแนะนำแพ็กเกจ/ราคาคร่าวๆ ก่อน แล้วค่อยถามรายละเอียด
                instruction = f"ถึง {agent}: วิเคราะห์ข้อความลูกค้า หากลูกค้าบอกความต้องการเบื้องต้น (แม้ข้อมูลยังไม่ครบ) ให้ 'แนะนำแพ็กเกจ (A/B/C) หรือแจ้งช่วงราคาคร่าวๆ ตาม Scale งาน (S/M/L/XL)' ให้ลูกค้าทราบก่อนได้เลย พร้อมบอกจุดเด่นสั้นๆ จากนั้นค่อยตบท้ายว่า 'ราคาเป๊ะๆ จะขึ้นอยู่กับขนาดและรายละเอียด' และตามด้วยลิสต์คำถามขอข้อมูลที่ขาด (เช่น ขนาด, รูปหน้างาน, เบอร์โทร) คุยให้กระชับที่สุด"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: ตอนนี้คุณคือ "แอดมินบริการลูกค้า" ตอบแชท "ลูกค้า" ยึดกฎเหล็กนี้:
            1. เสนอราคาเบื้องต้นได้ทันที (สำคัญมาก): ให้นำเสนอแพ็กเกจที่เหมาะสม หรือช่วงราคาคร่าวๆ ให้ลูกค้าทราบก่อนเสมอ เพื่อให้ลูกค้าเห็นภาพ จากนั้นค่อยสอบถามรายละเอียดเชิงลึก (เช่น ขอขนาด, รูปหน้างาน) ไว้ที่ส่วนท้ายของข้อความ
            2. ห้ามทักทายซ้ำ: หากมีการทักทายไปแล้วในประวัติการแชท ห้ามพิมพ์สวัสดีซ้ำอีกเด็ดขาด ให้ตอบคำถามต่อเนื่องได้เลย
            3. การเรียกชื่อ: หากลูกค้าแจ้งชื่อ ให้เรียกชื่อลูกค้า หากยังไม่ทราบเรียก "คุณลูกค้า"
            4. การจัดรูปแบบ (บังคับ!): หากพิมพ์เป็นข้อๆ (1., 2., 3.) ต้องขึ้นบรรทัดใหม่เสมอ ห้ามพิมพ์ติดกัน
            5. การแบ่งกล่องข้อความ: ใช้ [SPLIT] คั่นเพื่อแบ่งกล่องให้เป็นธรรมชาติ อนุญาตให้แบ่ง 2-3 กล่อง"""
            
        else:
            for agent in ["NOTE", "TERRA", "NAVARA", "BIGM"]:
                instruction = f"ถึง {agent}: คุณอยู่ใน Internal Mode หาก Lead ถามคำถามต่อเนื่อง ให้ดึงข้อมูลมาตอบให้ตรงประเด็นที่สุด ฟันธงมาเลย"
                internal_memory.append({"role": "user", "content": instruction})
                analysis = self._call_agent(agent, internal_memory)
                internal_memory.append({"role": "assistant", "content": f"[{agent} Analysis]: {analysis}"})
            
            final_prompt = """ถึง SUN: สรุปข้อมูลจากทีมงานเพื่อตอบ Lead โดยต้องทำตามกฎนี้เคร่งครัด:
            1. ตอบคำถามทันทีและห้ามทักทายซ้ำ: หาก Lead ถามคำถามต่อเนื่อง ให้ตอบเข้าประเด็นทันที (ห้ามพิมพ์ประโยคทักทายซ้ำเด็ดขาดหากเคยทักทายไปแล้ว)
            2. การจัดรูปแบบข้อความ (บังคับ!): หากมีการแจกแจงตัวเลือก หรือลิสต์เป็นข้อๆ ต้องขึ้นบรรทัดใหม่เสมอ
            3. การแบ่งกล่องข้อความ: แบ่งกล่องข้อความสูงสุด 2-3 กล่อง (ใช้ [SPLIT] คั่น)"""

        internal_memory.append({"role": "user", "content": final_prompt})
        return self._call_agent("SUN", internal_memory)
