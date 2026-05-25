import os
from openai import OpenAI

# ==========================================
# ⚙️ JHD INTELLIGENCE: BACKEND AUTOMATION
# ==========================================

class JHDAutomationSystem:
    def __init__(self, api_key):
        # ตั้งค่า Client (ปรับใช้ตามที่พี่ออฟใช้งานจริง เช่น OpenRouter หรือ Google API โดยตรง)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1" # เปลี่ยน Base URL ตามที่ใช้งาน
        )
        self.model = "google/gemini-2.5-flash"
        
        # รายชื่อไฟล์ System Prompt ที่เราเพิ่งสร้างกัน
        self.agent_files = {
            "SUN": ["jhd_persona_sun.md", "jhd_role_sun.md"],
            "NOTE": ["jhd_persona_note.md", "jhd_role_note.md", "jhd_formula_pricing_note.md"],
            "TERRA": ["jhd_persona_terra.md", "jhd_role_terra.md"],
            "NAVARA": ["jhd_persona_navara.md", "jhd_role_navara.md"],
            "BIGM": ["jhd_persona_bigm.md", "jhd_role_bigm.md"]
        }

    def _load_system_prompt(self, agent_name):
        """ฟังก์ชันรวมไฟล์ .md ของแต่ละ Agent เพื่อสร้างคัมภีร์สมอง"""
        prompt = f"คุณคือ {agent_name} หนึ่งในทีม JHD Intelligence System\n\n"
        for file in self.agent_files.get(agent_name, []):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    prompt += f.read() + "\n\n"
            except FileNotFoundError:
                pass # ข้ามไฟล์ที่หาไม่เจอ
        return prompt

    def _call_agent(self, agent_name, context_history):
        """ฟังก์ชันส่งข้อมูลให้ Agent ประมวลผล 1 ตัว"""
        system_prompt = self._load_system_prompt(agent_name)
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_history) # โหลดประวัติการประชุมหลังบ้าน
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content

    def run_full_workflow(self, user_prompt):
        """
        🚀 สายพานหลัก: Human ➔ SUN ➔ NOTE ➔ TERRA ➔ NAVARA ➔ BIGM ➔ SUN ➔ Human
        """
        # ห้องประชุมลับหลังบ้าน (Shared Memory)
        internal_memory = [{"role": "user", "content": f"โจทย์จากลูกค้า/ทีมงาน: {user_prompt}"}]
        
        workflow_sequence = ["SUN", "NOTE", "TERRA", "NAVARA", "BIGM"]
        
        print("⚡ [SYSTEM] เริ่มรันกระบวนการหลังบ้าน...")

        # 1. วิ่งตามสายพานทีละตัว (ซ่อนหลังบ้าน ไม่แสดงให้ User เห็น)
        for agent in workflow_sequence:
            print(f"กำลังประมวลผล: {agent}...")
            
            # บังคับให้บอทตัวถัดไปรู้ว่าต้องทำงานต่อจากข้อมูลด้านบน
            trigger_msg = {"role": "user", "content": f"ถึง {agent}: โปรดปฏิบัติหน้าที่ของคุณจากข้อมูลด้านบนให้สมบูรณ์"}
            internal_memory.append(trigger_msg)
            
            # รับคำตอบจาก Agent
            agent_response = self._call_agent(agent, internal_memory)
            
            # บันทึกผลลัพธ์ลงห้องประชุมลับ
            internal_memory.append({"role": "assistant", "content": f"[{agent} OUTPUT]:\n{agent_response}"})

        # 2. วนกลับมาที่ SUN (Final Approval & Output)
        print("กำลังประมวลผล: SUN (สรุปงานขั้นสุดท้าย)...")
        final_instruction = {
            "role": "user", 
            "content": "ถึง SUN: ทีมงานทุกคนประมวลผลเสร็จแล้ว โปรดตรวจสอบความเรียบร้อยทั้งหมด และสรุป Output สุดท้ายเพื่อส่งมอบให้ลูกค้าหรือทีมงานมนุษย์ (ไม่ต้องแสดงขั้นตอนการคุยกันหลังบ้าน)"
        }
        internal_memory.append(final_instruction)
        
        final_output = self._call_agent("SUN", internal_memory)
        
        print("✅ [SYSTEM] กระบวนการเสร็จสิ้น!\n")
        return final_output

# ==========================================
# 🚀 ส่วนแสดงผลบนหน้าเว็บ Streamlit
# ==========================================
if __name__ == "__main__":
    import streamlit as st
    
    # 1. ตั้งค่าหน้าตาเว็บ
    st.set_page_config(page_title="JHD AI Workflow", page_icon="☀️")
    st.title("☀️ JHD Intelligence System")
    st.markdown("**Workflow:** `Human` ➔ `SUN` ➔ `NOTE` ➔ `TERRA` ➔ `NAVARA` ➔ `BIGM` ➔ `SUN` ➔ `Output`")
    
    # 2. ดึง API Key จากหลังบ้าน Streamlit
    try:
        API_KEY = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        st.error("⚠️ ไม่พบ API Key! กรุณาไปใส่ 'OPENROUTER_API_KEY' ในเมนู Settings > Secrets ของ Streamlit ครับ")
        st.stop()
        
    # สร้างระบบ
    jhd_system = JHDAutomationSystem(API_KEY)
    
    # 3. สร้างกล่องรับข้อความและปุ่มกด
    user_prompt = st.text_area("💬 พิมพ์บรีฟงานหรือข้อความจากลูกค้าตรงนี้:", height=100, 
                               placeholder="เช่น ลูกค้าอยากทำป้ายหน้าร้านกาแฟ ขนาด 2x1 เมตร งบ 15,000 บาท...")
    
    if st.button("🚀 เริ่มรันระบบ Automation", type="primary"):
        if user_prompt.strip() == "":
            st.warning("⚠️ กรุณาพิมพ์ข้อความก่อนกดรันระบบครับ")
        else:
            # ขึ้นสถานะโหลดหมุนๆ ระหว่างบอทคุยกัน
            with st.spinner("🤖 บอทกำลังประชุมกันหลังบ้าน (ใช้เวลาประมาณ 10-30 วินาที)..."):
                result = jhd_system.run_full_workflow(user_prompt)
            
            # โชว์ผลลัพธ์สุดท้าย
            st.success("✅ ประมวลผลเสร็จสิ้น!")
            st.markdown("### 📋 Final Output from SUN")
            st.info(result)
