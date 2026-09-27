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
                if isinstance(data, list):
                    categories_data[category_name] = data
        except Exception:
            pass
            
    return categories_data

# 5. ฟังก์ชันบันทึกข้อมูลลงไฟล์ JSON
def save_category_data(category_name, data):
    folder_path = "questions"
    file_path = os.path.join(folder_path, f"{category_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Session States
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'answered' not in st.session_state:
    st.session_state.answered = False
if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""
if 'question_index' not in st.session_state:
    st.session_state.question_index = 0

all_categories = load_all_categories()

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
        st.session_state.question_index += 1
    else:
        st.session_state.current_question = None

# --- แถบเมนูด้านข้าง (Sidebar) สำหรับสลับหน้า ---
st.sidebar.title("📌 เมนูหลัก")
mode = st.sidebar.radio("เลือกหน้าทำรายการ:", ["🎯 ทำแบบทดสอบ", "⚙️ จัดการคำถาม (เพิ่ม/ลบ)"])

# ==========================================
# หน้า 1: ทำแบบทดสอบ
# ==========================================
if mode == "🎯 ทำแบบทดสอบ":
    st.title("☸️ แอปตอบคำถามธรรมะ")
    st.caption("ระบบตรวจคำตอบภาษาไทย ข้ามการตรวจเว้นวรรคอัตโนมัติ")

    if not all_categories:
        st.warning("ยังไม่มีคำถามในระบบ กรุณาไปที่เมนู '⚙️ จัดการคำถาม' เพื่อเพิ่มคำถามใหม่ครับ")
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

# ==========================================
# หน้า 2: จัดการคำถาม (เพิ่ม/ลบ)
# ==========================================
else:
    st.title("⚙️ จัดการชุดคำถาม")
    
    manage_action = st.radio("เลือกรายการที่ต้องการทำ:", ["➕ เพิ่มคำถามใหม่", "🗑️ ลบคำถาม"], horizontal=True)
    st.markdown("---")

    if manage_action == "➕ เพิ่มคำถามใหม่":
        st.subheader("➕ เพิ่มคำถามใหม่ลงในหมวดหมู่")
        
        existing_cats = list(all_categories.keys())
        cat_option = st.radio("เลือกประเภทหมวดหมู่:", ["เลือกหมวดที่มีอยู่", "สร้างหมวดหมู่ใหม่"])
        
        if cat_option == "เลือกหมวดที่มีอยู่" and existing_cats:
            cat_name = st.selectbox("เลือกหมวดหมู่:", existing_cats)
        else:
            cat_name = st.text_input("ชื่อหมวดหมู่ใหม่ (ภาษาอังกฤษ เช่น vinaya, sutta):").strip().lower()
            cat_name = re.sub(r'[^a-zA-Z0-9_-]', '', cat_name) # กรองเอาเฉพาะตัวอักษรที่ปลอดภัยสำหรับชื่อไฟล์

        new_question = st.text_area("โจทย์คำถาม:")
        new_answer = st.text_area("คำตอบที่ถูกต้อง:")

        if st.button("💾 บันทึกคำถาม", type="primary"):
            if not cat_name:
                st.error("กรุณาระบุชื่อหมวดหมู่ให้ถูกต้อง")
            elif not new_question.strip() or not new_answer.strip():
                st.error("กรุณากรอกทั้งโจทย์คำถามและคำตอบ")
            else:
                cat_questions = all_categories.get(cat_name, [])
                new_id = len(cat_questions) + 1
                
                new_item = {
                    "id": new_id,
                    "question": new_question.strip(),
                    "answer": new_answer.strip()
                }
                
                cat_questions.append(new_item)
                save_category_data(cat_name, cat_questions)
                
                st.success(f"บันทึกคำถามใหม่ลงหมวด '{cat_name}' เรียบร้อยแล้ว!")
                st.rerun()

    elif manage_action == "🗑️ ลบคำถาม":
        st.subheader("🗑️ ลบคำถามออกจากระบบ")
        
        if not all_categories:
            st.info("ยังไม่มีหมวดหมู่คำถามให้ลบ")
        else:
            selected_cat = st.selectbox("เลือกหมวดหมู่ที่ต้องการจัดการ:", list(all_categories.keys()))
            questions_list = all_categories[selected_cat]
            
            if not questions_list:
                st.info("หมวดหมู่นี้ไม่มีคำถาม")
            else:
                q_options = [f"ID {q['id']}: {q['question']}" for q in questions_list]
                selected_q_str = st.selectbox("เลือกข้อที่ต้องการลบ:", q_options)
                
                # หา Index ของข้อที่เลือก
                selected_index = q_options.index(selected_q_str)
                
                if st.button("❌ ยืนยันการลบข้อนี้", type="primary"):
                    deleted_item = questions_list.pop(selected_index)
                    save_category_data(selected_cat, questions_list)
                    st.success(f"ลบคำถาม '{deleted_item['question']}' เรียบร้อยแล้ว!")
                    st.rerun()
