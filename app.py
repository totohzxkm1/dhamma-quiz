import streamlit as st
import json
import random
import unicodedata
import os
import glob
import re
import difflib

# ตั้งค่าหน้าตาของเว็บ
st.set_page_config(
    page_title="แบบทดสอบธรรมะ",
    page_icon="☸️",
    layout="centered"
)

# Custom CSS
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

# 1. ฟังก์ชันดึงและแยกตัวอักษรภาษาไทยพร้อมสระ/วรรณยุกต์ (ลบช่องว่างออกทั้งหมด)
def clean_and_split_thai(text):
    if not text:
        return []
    text = re.sub(r'\s+', '', text.strip())
    text = unicodedata.normalize('NFC', text)
    
    clusters = []
    for char in text:
        if unicodedata.category(char) in ['Mn', 'Mc', 'Me'] and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters

# 2. ฟังก์ชันไฮไลต์ข้อความที่พิมพ์ผิด/เกิน/ตก
def highlight_differences(user_input, correct_answer):
    user_clusters = clean_and_split_thai(user_input)
    correct_clusters = clean_and_split_thai(correct_answer)
    
    matcher = difflib.SequenceMatcher(None, user_clusters, correct_clusters)
    html_output = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for char in user_clusters[i1:i2]:
                html_output.append(f'<span class="char-match">{char}</span>')
        elif tag in ('replace', 'insert', 'delete'):
            for char in user_clusters[i1:i2]:
                html_output.append(f'<span class="char-mismatch">{char}</span>')
                
    return "".join(html_output)

# 3. ฟังก์ชันตรวจว่าถูกต้องหรือไม่
def is_answer_correct(user_input, correct_answer):
    return clean_and_split_thai(user_input) == clean_and_split_thai(correct_answer)

# 4. โหลดไฟล์ JSON ทั้งหมดจากโฟลเดอร์ questions
@st.cache_data
def load_all_categories():
    categories_data = {}
    folder_path = "questions"
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    for file_path in json_files:
        category_name = os.path.basename(file_path).replace(".json", "")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    categories_data[category_name] = data
        except Exception:
            pass
            
    return categories_data

all_categories = load_all_categories()

# Session States
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""
if 'question_index' not in st.session_state:
    st.session_state.question_index = 0

def get_new_question(selected_cat):
    pool = []
    if selected_cat == "รวมทุกหมวดหมู่":
        for cat_questions in all_categories.values():
            pool.extend(cat_questions)
    elif selected_cat in all_categories:
        pool = all_categories[selected_cat]
        
    if pool:
        st.session_state.current_question = random.choice(pool)
        st.session_state.answered = False
        st.session_state.user_answer = ""
        # เพิ่ม Index เพื่อใช้เปลี่ยน Key ของช่องพิมพ์ข้อความ
        st.session_state.question_index += 1

# UI หน้าเว็บ
st.title("☸️ แอปตอบคำถามธรรมะ")
st.caption("ระบบตรวจคำตอบภาษาไทย ข้ามการตรวจเว้นวรรคอัตโนมัติ")

if not all_categories:
    st.error("ไม่พบไฟล์คำถามในโฟลเดอร์ 'questions/' กรุณาสร้างไฟล์ .json ด้านในโฟลเดอร์ก่อนครับ")
else:
    cat_list = ["รวมทุกหมวดหมู่"] + list(all_categories.keys())
    selected_category = st.selectbox("📌 เลือกหมวดหมู่คำถาม:", cat_list)

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🎲 สุ่มคำถามใหม่", use_container_width=True):
            get_new_question(selected_category)

    if st.session_state.current_question is None:
        get_new_question(selected_category)

    q = st.session_state.current_question

    if q:
        st.markdown("---")
        st.info(f"**โจทย์:** {q['question']}")

        # ใช้ Dynamic Key เพื่อล้างช่องข้อความทุกครั้งที่สุ่มคำถามใหม่
        input_key = f"input_{st.session_state.question_index}"
        
        user_input = st.text_input(
            "✍️ พิมพ์คำตอบของคุณที่นี่:",
            key=input_key,
            placeholder="พิมพ์คำตอบแล้วกดส่ง..."
        )

        if st.button("ส่งคำตอบ", type="primary"):
            if user_input.strip() == "":
                st.warning("กรุณาพิมพ์คำตอบก่อนส่งครับ")
            else:
                st.session_state.answered = True
                st.session_state.user_answer = user_input

        if st.session_state.answered:
            st.markdown("### 📊 ผลการตรวจคำตอบ")
            
            if is_answer_correct(st.session_state.user_answer, q['answer']):
                st.success("🎉 ถูกต้องเก่งมากครับ!")
            else:
                st.error("❌ ยังไม่ถูกต้อง มีตัวอักษรหรือสระที่พิมพ์ผิด/เกิน/ตก")
                
                st.markdown("**คำตอบที่ถูกต้อง:**")
                st.markdown(f'<div class="correct-text">{q["answer"]}</div>', unsafe_allow_html=True)
                
                st.markdown("**เปรียบเทียบคำตอบของคุณ (ตัวที่ผิด/เกิน ไฮไลต์สีแดง):**")
                highlighted_html = highlight_differences(st.session_state.user_answer, q['answer'])
                st.markdown(f'<div class="diff-box">{highlighted_html}</div>', unsafe_allow_html=True)
