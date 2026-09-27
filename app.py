import streamlit as st
import json
import random
import unicodedata
import os
import glob

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

def normalize_and_split_thai(text):
    text = unicodedata.normalize('NFC', text.strip())
    clusters = []
    for char in text:
        if unicodedata.category(char) in ['Mn', 'Mc', 'Me'] and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
    return clusters

def highlight_differences(user_input, correct_answer):
    user_clusters = normalize_and_split_thai(user_input)
    correct_clusters = normalize_and_split_thai(correct_answer)
    
    html_output = []
    for i in range(len(user_clusters)):
        u_char = user_clusters[i]
        c_char = correct_clusters[i] if i < len(correct_clusters) else ""
        
        if u_char == c_char:
            html_output.append(f'<span class="char-match">{u_char}</span>')
        else:
            html_output.append(f'<span class="char-mismatch">{u_char}</span>')
            
    return "".join(html_output)

# --- ฟังก์ชันดึงไฟล์ JSON แยกตามหมวดหมู่จากโฟลเดอร์ questions ---
@st.cache_data
def load_all_categories():
    categories_data = {}
    folder_path = "questions"
    
    # ตรวจสอบว่ามีโฟลเดอร์ questions หรือไม่
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    for file_path in json_files:
        # ใช้ชื่อไฟล์ (ตัด .json ออก) เป็นชื่อหมวดหมู่
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

# --- UI หน้าเว็บ Streamlit ---
st.title("☸️ แอปตอบคำถามธรรมะ")
st.caption("ระบบตรวจคำตอบภาษาไทย แยกหมวดหมู่อัตโนมัติจากไฟล์ JSON")

if not all_categories:
    st.error("ไม่พบไฟล์คำถามในโฟลเดอร์ 'questions/' กรุณาสร้างไฟล์ .json ด้านในโฟลเดอร์ก่อนครับ")
else:
    # สร้างตัวเลือกหมวดหมู่จากชื่อไฟล์ที่มีในโฟลเดอร์
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

        user_input = st.text_input(
            "✍️ พิมพ์คำตอบของคุณที่นี่:",
            value=st.session_state.user_answer,
            key="input_box",
            placeholder="พิมพ์คำตอบแล้วกด Enter..."
        )

        if st.button("ส่งคำตอบ", type="primary"):
            if user_input.strip() == "":
                st.warning("กรุณาพิมพ์คำตอบก่อนส่งครับ")
            else:
                st.session_state.answered = True
                st.session_state.user_answer = user_input

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
                
                st.markdown("**เปรียบเทียบคำตอบ (ตัวที่ผิด/ตก ไฮไลต์สีแดง):**")
                highlighted_html = highlight_differences(st.session_state.user_answer, q['answer'])
                st.markdown(f'<div class="diff-box">{highlighted_html}</div>', unsafe_allow_html=True)
