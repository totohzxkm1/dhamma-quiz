    # --- โหมด 2: แก้ไขคำถามที่มีอยู่ ---
    elif manage_action == "✏️ แก้ไขคำถาม":
        st.subheader("✏️ แก้ไขคำถาม/คำตอบ")
        
        if not all_categories:
            st.info("ยังไม่มีข้อมูลคำถามในระบบ")
        else:
            selected_cat = st.selectbox("เลือกหมวดหมู่:", list(all_categories.keys()), key="edit_cat_select")
            questions_list = all_categories[selected_cat]
            
            if not questions_list:
                st.info("หมวดหมู่นี้ไม่มีคำถาม")
            else:
                q_options = [f"ข้อ {q['id']}: {q['question']}" for q in questions_list]
                selected_q_str = st.selectbox("เลือกข้อที่ต้องการแก้ไข:", q_options, key="edit_q_select")
                
                selected_index = q_options.index(selected_q_str)
                target_q = questions_list[selected_index]
                
                st.markdown("---")
                
                # ใช้ Dynamic Key ผูกกับ ID เพื่อรีเฟรชข้อความเมื่อเปลี่ยนตัวเลือก
                edit_key_suffix = f"{selected_cat}_{target_q['id']}"
                
                edit_question = st.text_area(
                    "แก้ไขโจทย์คำถาม:", 
                    value=target_q['question'], 
                    key=f"edit_q_text_{edit_key_suffix}"
                )
                edit_answer = st.text_area(
                    "แก้ไขคำตอบที่ถูกต้อง:", 
                    value=target_q['answer'], 
                    key=f"edit_a_text_{edit_key_suffix}"
                )
                
                if st.button("💾 บันทึกการแก้ไข", type="primary"):
                    if not edit_question.strip() or not edit_answer.strip():
                        st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
                    else:
                        questions_list[selected_index]['question'] = edit_question.strip()
                        questions_list[selected_index]['answer'] = edit_answer.strip()
                        
                        save_category_data(selected_cat, questions_list)
                        st.success("อัปเดตข้อมูลคำถามเรียบร้อยแล้ว!")
                        st.rerun()
