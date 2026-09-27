import glob
import json
import os
import random
import re
import difflib  # เพิ่มไลบรารีเปรียบเทียบตัวอักษร
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

CATEGORY_FILES = {
    "พระวินัย": "vinaya.json",
    "พระสูตร": "sutta.json",
    "อริยสัจ 4": "ariya.json"
}

def clean_text(text):
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r'\s+', '', text) # ลบเว้นวรรค
    text = re.sub(r'[^\w\u0E00-\u0E7F]', '', text) # ลบเครื่องหมายพิเศษ
    return text

# ฟังก์ชันเปรียบเทียบตัวอักษรและไฮไลต์ตัวที่พิมพ์ตก/พิมพ์ผิด
def compare_and_highlight(user_ans, real_ans):
    c_user = clean_text(user_ans)
    c_real = clean_text(real_ans)
    
    # ถ้าพิมพ์ถูกต้องครบถ้วน
    if c_user == c_real:
        return True, f'<span style="color: #28a745;">{real_ans}</span>'
    
    # เปรียบเทียบตัวอักษรระหว่างเฉลยกับคำตอบผู้ใช้
    matcher = difflib.SequenceMatcher(None, c_real, c_user)
    highlighted_result = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # ตัวอักษรที่พิมพ์ถูกต้อง -> สีเขียว
            highlighted_result.append(f'<span style="color: #28a745;">{c_real[i1:i2]}</span>')
        elif tag in ('delete', 'replace'):
            # ตัวอักษร/สระที่พิมพ์ตกหรือพิมพ์ผิด -> แสดงสีแดง
            highlighted_result.append(f'<span style="color: #dc3545; font-weight: bold; text-decoration: underline;">{c_real[i1:i2]}</span>')
            
    diff_html = "".join(highlighted_result)
    return False, diff_html

def load_category_questions(cat_name):
    filename = CATEGORY_FILES.get(cat_name)
    if filename and os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

question_weights = {}

def get_weighted_question(category):
    questions = load_category_questions(category)
    if not questions:
        return None
    
    for q in questions:
        q_id = q['id']
        if q_id not in question_weights:
            question_weights[q_id] = {'score': 10, 'data': q}
            
    pool = []
    for q in questions:
        q_id = q['id']
        weight = max(1, question_weights[q_id]['score'])
        pool.extend([q] * weight)
        
    return random.choice(pool)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบควิซทบทวนธรรมะ</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 15px; background: #f4f4f9; color: #333; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 420px; margin: auto; }
        select, input[type="text"] { width: 90%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; margin: 8px 0; }
        button { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 5px; }
        .btn-next { background: #007bff; display: none; }
        .score-board { background: #e9ecef; padding: 8px; border-radius: 6px; margin-bottom: 15px; font-weight: bold; }
        .result { font-weight: bold; font-size: 18px; margin-top: 12px; }
        .correct { color: #28a745; }
        .wrong { color: #dc3545; }
        .diff-box { background: #fff3cd; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 18px; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="card">
        <h3>📖 ควิซทบทวนความรู้</h3>
        
        <label><b>เลือกหมวดหมู่:</b></label><br>
        <select id="category-select" onchange="loadNewQuestion()">
            {% for cat in categories %}
                <option value="{{ cat }}">{{ cat }}</option>
            {% endfor %}
        </select>

        <div class="score-board">
            สะสม: <span id="total-score" style="color:blue;">0</span> คะแนน
        </div>

        <hr>

        <p style="font-size: 18px;"><strong id="question-text">กำลังโหลด...</strong></p>
        
        <input type="text" id="user-ans" placeholder="พิมพ์คำตอบแล้วกด Enter..." autocomplete="off" onkeydown="handleKeyPress(event)">
        <button id="btn-submit" onclick="checkAnswer()">ส่งคำตอบ</button>
        <button id="btn-next" class="btn-next" onclick="loadNewQuestion()">🎲 ข้อถัดไป ➔</button>

        <div id="result-box"></div>
    </div>

    <script>
        let currentQA = null;
        let totalScore = 0;
        let isAnswered = false;

        async function loadNewQuestion() {
            let cat = document.getElementById('category-select').value;
            document.getElementById('user-ans').value = '';
            document.getElementById('result-box').innerHTML = '';
            document.getElementById('btn-submit').style.display = 'inline-block';
            document.getElementById('btn-next').style.display = 'none';
            document.getElementById('user-ans').focus();
            isAnswered = false;

            let response = await fetch('/api/get_question?cat=' + encodeURIComponent(cat));
            currentQA = await response.json();

            if (currentQA.error) {
                document.getElementById('question-text').innerText = "ไม่มีคำถามในไฟล์นี้ หรือหาไฟล์ไม่พบ";
            } else {
                document.getElementById('question-text').innerText = currentQA.q;
            }
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') {
                if (!isAnswered) {
                    checkAnswer();
                } else {
                    loadNewQuestion();
                }
            }
        }

        async function checkAnswer() {
            let userAns = document.getElementById('user-ans').value;
            if (!userAns || !currentQA || currentQA.error) return;

            let response = await fetch('/api/check_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: currentQA.id,
                    user_ans: userAns,
                    real_ans: currentQA.a
                })
            });

            let resData = await response.json();
            let resultBox = document.getElementById('result-box');
            
            if (resData.is_correct) {
                resultBox.innerHTML = '<p class="result correct">✅ ถูกต้องครับ!</p>';
                totalScore += 1;
            } else {
                resultBox.innerHTML = `
                    <p class="result wrong">❌ พิมพ์ตก/ยังไม่ถูกต้อง!</p>
                    <div class="diff-box">
                        คำตอบที่ขาด: ${resData.diff_html}
                    </div>
                    <small style="color:#666; display:block; margin-top:5px;">(ตัวสีแดงขีดเส้นใต้ คือตัวอักษร/สระที่ตกไป)</small>
                `;
            }

            document.getElementById('total-score').innerText = totalScore;
            document.getElementById('btn-submit').style.display = 'none';
            document.getElementById('btn-next').style.display = 'inline-block';
            isAnswered = true;
        }

        loadNewQuestion();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    categories = list(CATEGORY_FILES.keys())
    return render_template_string(HTML_TEMPLATE, categories=categories)

@app.route('/api/get_question')
def api_get_question():
    cat = request.args.get('cat', '')
    q = get_weighted_question(cat)
    if q:
        return jsonify(q)
    return jsonify({"error": "No questions"})

@app.route('/api/check_answer', methods=['POST'])
def api_check_answer():
    req = request.get_json()
    q_id = req.get('id')
    user_ans = req.get('user_ans', '')
    real_ans = req.get('real_ans', '')

    is_correct, diff_html = compare_and_highlight(user_ans, real_ans)

    if q_id in question_weights:
        if is_correct:
            question_weights[q_id]['score'] = max(1, int(question_weights[q_id]['score'] / 2))
        else:
            question_weights[q_id]['score'] += 10

    return jsonify({
        'is_correct': is_correct,
        'diff_html': diff_html
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
