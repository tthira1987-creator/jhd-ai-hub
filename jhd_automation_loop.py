# ... (ส่วนหัวของ class คงเดิม)

    def run_full_workflow(self, chat_history, mode):
        # 1. จัดเรียงประวัติแชท
        chat_context = "--- ประวัติการสนทนาที่ผ่านมา ---\n"
        for msg in chat_history[:-1]: 
            # เปลี่ยนจาก เจ้านาย เป็น Lead
            sender = "Lead" if msg["role"] == "user" else "น้อง SUN"
            chat_context += f"{sender}: {msg['content']}\n"
        
        latest_message = chat_history[-1]['content']
        
        full_prompt = f"{chat_context}\n--- ข้อความล่าสุด ---\nLead ได้พิมพ์มาว่า: {latest_message}"
        internal_memory = [{"role": "user", "content": full_prompt}]
        workflow_sequence = ["SUN", "NOTE", "TERRA", "NAVARA", "BIGM"]
        
        # 2. กำหนดโหมดการทำงานให้สมาร์ทขึ้น
        mode_instruction = ""
        if mode == "Service Mode (Customer)":
            mode_instruction = """
ถึงทุกคน: ขณะนี้เราอยู่ใน 'Service Mode' (โหมดคุยกับลูกค้า)
กฎเหล็ก: 
1. ตรวจสอบข้อมูลเบื้องต้น (SOP Step 1: ชื่อ, ประเภทงาน, ขนาด, งบ) ให้ครบ
2. หากข้อมูลไม่ครบ: ต้องเป็นฝ่ายถามข้อมูลให้ครบ ห้ามข้ามขั้นตอน
3. หากข้อมูลครบแล้ว: ให้วิเคราะห์งานตามหน้าที่ของคุณเพื่อปิดดีล
4. ห้ามหลุดคำว่า [OUTPUT] หรือ [SUN OUTPUT] เด็ดขาด"""
        else:
            mode_instruction = "ถึงทุกคน: ขณะนี้อยู่ใน 'Internal Mode' (โหมดคุยกับ Lead) คุณคือทีมงานคุณภาพ ปฏิบัติภารกิจตามที่ Lead สั่งงานได้ทันที"

        for agent in workflow_sequence:
            trigger_msg = {"role": "user", "content": f"{mode_instruction}\n\nถึง {agent}: วิเคราะห์และตอบคำถามล่าสุด หากไม่เกี่ยวข้องกับหน้าที่ของคุณให้ตอบว่า 'PASS'"}
            internal_memory.append(trigger_msg)
            agent_response = self._call_agent(agent, internal_memory)
            internal_memory.append({"role": "assistant", "content": agent_response})

        final_instruction = {
            "role": "user", 
            "content": """ถึง SUN: คุณคือ 'น้องซัน' เลขาหน้าห้อง 
กฎการตอบ:
1. สรุปผลจากทีมงานให้ตรงคำถาม ตอบแบบยืดหยุ่น เป็นธรรมชาติ
2. ห้ามอธิบายกระบวนการทำงาน ห้ามบอกว่าใครทำอะไร
3. 🚨 ห้ามมีคำว่า [SUN OUTPUT]:, [OUTPUT], หรือ PASS เด็ดขาด!
4. ตอบด้วยความสุภาพ มืออาชีพ และมั่นใจ"""
        }
        internal_memory.append(final_instruction)
        return self._call_agent("SUN", internal_memory)

if __name__ == "__main__":
    st.set_page_config(page_title="JHD Intelligence", page_icon="☀️", layout="centered")
    
    # Sidebar สำหรับเลือกโหมด
    st.sidebar.title("⚙️ System Control")
    mode = st.sidebar.radio("สถานะโหมดใช้งาน:", ["Internal Mode (Lead)", "Service Mode (Customer)"])
    
    st.title("☀️ น้อง SUN (JHD Secretary)")
    st.caption(f"Status: {mode}")

    # ... (ส่วนที่เหลือของโค้ดคงเดิม)
