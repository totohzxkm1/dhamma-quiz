import streamlit as st
import json
import random
import unicodedata

# ตั้งค่าหน้าตาของเว็บ
st.set_page_config(
    page_title="แบบทดสอบธรรมะ",
    page_icon="☸️",
    layout="centered"
)

# Custom CSS เพื่อปรับแต่งปุ่มและกล่องไฮไลต์ข้อความ
st.markdown("""
<style>
    .correct-text {
        color: #2e7d32;
        background-color: #e8f5e9;
        padding: 12px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .diff-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        font-size: 20px;
        line-height: 1.8;
        letter-spacing: 1px;
    }
    .char-match {
        color: #2e7d32;
        font-weight: bold;
    }
    .char-mismatch {
        color: #d32f2f;
        background-color: #ffebee;
        text-decoration: underline;
        font-weight: bold;
        padding: 0 2px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันดึงและแยกตัวอักษรภาษาไทยพร้อมสระ/วรรณยุกต์
def normalize_and_split_thai(text):
    text = unicodedata.normalize('NFC', text.strip())
    clusters = []
    for char in text:
        # แยกแยะวรรณยุกต์/สระบน-ล่างให้รวมกลุ่มกับตัวอักษรหลักอย่างถูกต้อง
        if unicodedata.category(char) in ['Mn', 'Mc', 'Me'] and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters

# ฟังก์ชันไฮไลต์ข้อความที่พิมพ์ผิด/ตก/สลับตำแหน่ง
def highlight_differences(user_input, correct_answer):
    user_clusters = normalize_and_split_thai(user_input)
    correct_clusters = normalize_and_split_thai(correct_answer)
    
    html_output = []
    max_len = max(len(user_clusters), len(correct_clusters))
    
    for i in range(len(user_clusters)):
        u_char = user_clusters[i]
        c_char = correct_clusters[i] if i < len(correct_clusters) else ""
        
        if u_char == c_char:
            html_output.append(f'<span class="char-match">{u_char}</span>')
        else:
            html_output.append(f'<span class="char-mismatch">{u_char}</span>')
            
    return "".join(html_output)

# โหลดคำถามจากไฟล์ JSON
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

questions_data = load_questions()

# กำหนด State สำหรับจดจำค่าในแอป
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""

def get_new_question(selected_cat):
    filtered = [q for q in questions_data if selected_cat == "ทั้งหมด" or q['category'] == selected_cat]
    if filtered:
        st.session_state.current_question = random.choice(filtered)
        st.session_state.answered = False
        st.session_state.user_answer = ""

# ส่วนแสดงผล UI หน้าเว็บ
st.title("☸️ แอปตอบคำถามธรรมะ")
st.caption("ระบบตรวจคำตอบภาษาไทยละเอียด ตรวจสอบสระ วรรณยุกต์ และเว้นวรรคถูกต้อง")

if not questions_data:
    st.error("ไม่พบไฟล์ questions.json กรุณาสร้างไฟล์คำถามก่อนครับ")
else:
    # เลือกหมวดหมู่
    categories = ["ทั้งหมด"] + list(set(q['category'] for q in questions_data))
    selected_category = st.selectbox("📌 เลือกหมวดหมู่คำถาม:", categories)

    # ปุ่มสุ่มคำถาม
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🎲 สุ่มคำถามใหม่", use_container_width=True):
            get_new_question(selected_category)

    if st.session_state.current_question is None:
        get_new_question(selected_category)

    q = st.session_state.current_question

    if q:
        st.markdown("---")
        st.subheader(f"หมวด: {q['category']}")
        st.info(f"**โจทย์:** {q['question']}")

        # กล่องพิมพ์คำตอบ
        user_input = st.text_input(
            "✍️ พิมพ์คำตอบของคุณที่นี่:",
            value=st.session_state.user_answer,
            key="input_box",
            placeholder="พิมพ์คำตอบแล้วกดส่ง..."
        )

        if st.button("ส่งคำตอบ", type="primary"):
            if user_input.strip() == "":
                st.warning("กรุณาพิมพ์คำตอบก่อนส่งครับ")
            else:
                st.session_state.answered = True
                st.session_state.user_answer = user_input

        # แสดงผลการตรวจคำตอบ
        if st.session_state.answered:
            st.markdown("### 📊 ผลการตรวจคำตอบ")
            
            clean_user = normalize_and_split_thai(st.session_state.user_answer)
            clean_correct = normalize_and_split_thai(q['answer'])

            if clean_user == clean_correct:
                st.success("🎉 ถูกต้องเก่งมากครับ! พิมพ์ได้ถูกต้องทุกตัวอักษรและสระวรรณยุกต์")
            else:
                st.error("❌ ยังไม่ถูกต้อง มีตัวอักษร สระ หรือวรรณยุกต์ที่พิมพ์ผิด/ตก")
                
                st.markdown("**คำตอบที่ถูกต้อง:**")
                st.markdown(f'<div class="correct-text">{q["answer"]}</div>', unsafe_allow_html=True)
                
                st.markdown("**การเปรียบเทียบคำตอบของคุณ (ตัวอักษร/สระที่ผิดจะไฮไลต์ สีแดง):**")
                highlighted_html = highlight_differences(st.session_state.user_answer, q['answer'])
                st.markdown(f'<div class="diff-box">{highlighted_html}</div>', unsafe_allow_html=True)
