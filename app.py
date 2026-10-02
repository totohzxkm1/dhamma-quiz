import json, random, re, unicodedata, difflib
from pathlib import Path
import streamlit as st

BASE = Path(__file__).parent
Q_FILE, S_FILE = BASE / "questions.json", BASE / "stats.json"
TONE = re.compile("[\u0e47-\u0e4c]")  # วรรณยุกต์ ไม้ไต่คู่ ทัณฑฆาต
TH_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

st.set_page_config(page_title="ตอบคำถามนักธรรมตรี", page_icon="🪷")


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data, msg):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        st.toast(msg, icon="✅")
    except Exception as e:
        st.toast(f"บันทึกไม่สำเร็จ: {e}", icon="⚠️")


def norm(t):
    t = unicodedata.normalize("NFC", t).translate(TH_DIGITS)
    t = re.sub(r"[ฯๆ\s.,;:!?\"'()\-–“”]", "", t)
    return TONE.sub("", t).lower()


def score(user, ans):