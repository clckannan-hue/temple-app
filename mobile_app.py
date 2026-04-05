import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import urllib.parse
import os
from fpdf import FPDF

# உங்களின் Cloud Database Link
NEON_URL = "postgresql://neondb_owner:npg_WqJld5Uu6nCE@ep-lucky-glitter-a14oql0y.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

st.set_page_config(page_title="காங்கேயன் கோவில்", page_icon="🙏", layout="centered")

st.markdown("<h2 style='text-align: center; color: darkred;'>அருள்மிகு காங்கேயன் கோவில்</h2>", unsafe_allow_html=True)
st.divider()

# 4 பக்கங்கள் (Tabs)
tab1, tab2, tab3, tab4 = st.tabs(["📊 டேஷ்போர்டு", "✍️ ரசீது", "🖨️ பழைய ரசீது", "💸 செலவுகள்"])

# ==========================================
# NUMBER TO TAMIL WORDS LOGIC
# ==========================================
def num_to_tamil_words(n):
    if n == 0: return ""
    ones = ["", "ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து", "ஆறு", "ஏழு", "எட்டு", "ஒன்பது"]
    tens = ["", "பத்து", "இருபது", "முப்பது", "நாற்பது", "ஐம்பது", "அறுபது", "எழுபது", "எண்பது", "தொண்ணூறு"]
    teens = ["பத்து", "பதினொன்று", "பன்னிரண்டு", "பதின்மூன்று", "பதினான்கு", "பதினைந்து", "பதினாறு", "பதினேழு", "பதினெட்டு", "பத்தொன்பது"]

    if n < 10: return ones[n]
    elif n < 20: return teens[n - 10]
    elif n < 100: return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
    elif n < 1000:
        h = n // 100
        rem = n % 100
        prefix = ["", "நூற்று", "இருநூற்று", "முந்நூற்று", "நானூற்று", "ஐநூற்று", "அறுநூற்று", "எழுநூற்று", "எண்ணூற்று", "தொள்ளாயிரத்து"]
        exact_h = ["", "நூறு", "இருநூறு", "முந்நூறு", "நானூறு", "ஐநூறு", "அறுநூறு", "எழுநூறு", "எண்ணூறு", "தொள்ளாயிரம்"]
        if rem == 0: return exact_h[h]
        else: return prefix[h] + " " + num_to_tamil_words(rem)
    elif n < 100000:
        th = n // 1000
        rem = n % 1000
        prefix = "ஆயிரத்து" if th == 1 else num_to_tamil_words(th) + " ஆயிரத்து"
        exact_th = "ஆயிரம்" if th == 1 else num_to_tamil_words(th) + " ஆயிரம்"
        return exact_th if rem == 0 else prefix + " " + num_to_tamil_words(rem)
    return str(n)

# ==========================================
# PDF CREATION LOGIC
# ==========================================
def create_pdf(receipt_no, date, name, relation, mobile, purpose, amount, amount_words):
    filename = f"Receipt_{receipt_no}.pdf"
    pdf = FPDF(orientation="L", unit="mm", format=(90, 190))
    pdf.set_margins(left=0, top=0, right=0)
    pdf.set_auto_page_break(auto=False, margin=0)
    pdf.add_page()
    pdf.set_text_shaping(True) 
    
    try:
        pdf.add_font('TamilFont', '', 'NotoSansTamil.ttf')
        pdf.set_font('TamilFont', size=12)
    except: return None
        
    pdf.rect(5, 5, 180, 80)
    try:
        pdf.image('sami_left.jpg', x=8, y=8, w=18)
        pdf.image('sami_right.jpg', x=164, y=8, w=18)
    except: pass
    
    pdf.set_font('TamilFont', size=9)
    pdf.set_xy(5, 8)
    pdf.cell(180, 5, "ஸ்ரீ செண்பக விநாயகர் துணை                    உ                   ஸ்ரீ காங்கேயன் துணை", align="C")
    
    pdf.set_font('TamilFont', size=20) 
    pdf.set_xy(5, 14)
    pdf.cell(180, 8, "அருள்மிகு காங்கேயன் கோவில்", align="C")
    
    pdf.set_font('TamilFont', size=10)
    pdf.set_xy(5, 23)
    pdf.cell(180, 5, "21, மாதாங்கோவில் தெரு, கோவில்பட்டி. பதிவு எண்: 87/2017", align="C")
    
    pdf.set_font('TamilFont', size=11)
    pdf.set_xy(10, 33)
    pdf.cell(40, 6, f"எண் : {receipt_no}")
    pdf.set_xy(140, 33)
    pdf.cell(40, 6, f"தேதி: {date}", align="R")
    
    pdf.rect(75, 31, 40, 8)
    pdf.set_font('TamilFont', size=12)
    pdf.set_xy(75, 32)
    pdf.cell(40, 6, "நன்கொடை ரசீது", align="C")
    
    y_pos = 46
    pdf.set_xy(10, y_pos)
    
    pdf.set_font('TamilFont', size=11)
    pdf.set_text_color(0, 0, 0)
    prefix1 = "உயர்திரு "
    suffix1 = " அவர்களிடமிருந்து"
    
    w_pref1 = pdf.get_string_width(prefix1)
    w_suff1 = pdf.get_string_width(suffix1)
    
    pdf.cell(w_pref1, 6, prefix1)
    
    if relation and relation.strip(): name_text = f" {name} {relation} "
    else: name_text = f" {name} "
        
    name_font_size = 16
    pdf.set_font('TamilFont', size=name_font_size)
    avail_name_width = max(10, 170 - w_pref1 - w_suff1)
    while pdf.get_string_width(name_text) > avail_name_width and name_font_size > 8:
        name_font_size -= 1
        pdf.set_font('TamilFont', size=name_font_size)
        
    pdf.set_text_color(139, 0, 0)
    pdf.cell(pdf.get_string_width(name_text), 6, name_text)
    
    pdf.set_font('TamilFont', size=11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w_suff1, 6, suffix1)

    y_pos += 10
    pdf.set_xy(10, y_pos)
    
    pdf.set_font('TamilFont', size=11)
    purpose_text = f"{purpose} வகைக்கு ரூபாய் "
    suffix2 = " மட்டும் நன்கொடையாக"
    
    w_pref2 = pdf.get_string_width(purpose_text)
    w_suff2 = pdf.get_string_width(suffix2)
    
    pdf.cell(w_pref2, 6, purpose_text)
    
    amount_words_text = f" {amount_words} "
    amt_font_size = 16
    pdf.set_font('TamilFont', size=amt_font_size)
    avail_amt_width = max(10, 170 - w_pref2 - w_suff2)
    while pdf.get_string_width(amount_words_text) > avail_amt_width and amt_font_size > 8:
        amt_font_size -= 1
        pdf.set_font('TamilFont', size=amt_font_size)
        
    pdf.set_text_color(139, 0, 0)
    pdf.cell(pdf.get_string_width(amount_words_text), 6, amount_words_text)
    
    pdf.set_font('TamilFont', size=11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w_suff2, 6, suffix2)

    y_pos += 10
    pdf.set_xy(10, y_pos)
    pdf.cell(130, 6, "நன்றியுடன் பெற்றுக்கொள்கிறோம்.")
    
    pdf.rect(145, y_pos - 4, 35, 12)
    pdf.set_font('Helvetica', 'B', 14) 
    pdf.set_xy(145, y_pos - 2)
    pdf.cell(35, 8, f"RS. {amount}/-", align="C")
    
    pdf.set_font('TamilFont', size=9)
    pdf.set_xy(5, 78)
    pdf.cell(180, 6, "* இது கணினியால் உருவாக்கப்பட்ட ரசீது, எனவே கையொப்பம் தேவையில்லை *", align="C")
    
    pdf.output(filename)
    return filename

# ==========================================
# SUPER FAST DATA LOADING (Cache Optimized)
# ==========================================
@st.cache_data(ttl=3600) 
def load_data(query):
    conn = psycopg2.connect(NEON_URL)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=3600)
def get_all_donors():
    conn = psycopg2.connect(NEON_URL)
    cur = conn.cursor()
    cur.execute("SELECT mobile, name, relation, address, thalaikattu FROM donors")
    data = cur.fetchall()
    conn.close()
    return data

@st.cache_data(ttl=3600)
def get_all_receipts_history():
    conn = psycopg2.connect(NEON_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT r.receipt_no, r.date, r.mobile, d.name, d.relation, r.purpose, r.amount 
        FROM receipts r 
        LEFT JOIN donors d ON r.mobile = d.mobile 
        ORDER BY r.receipt_no DESC LIMIT 100
    """)
    data = cur.fetchall()
    conn.close()
    return data

# ==========================================
# TAB 1: டேஷ்போர்டு (Dashboard)
# ==========================================
with tab1:
    try:
        df_receipts = load_data("SELECT SUM(amount) as total_income FROM receipts")
        df_expenses = load_data("SELECT SUM(amount) as total_expense FROM expenses")
        
        total_income = df_receipts['total_income'][0] if not df_receipts.empty and pd.notna(df_receipts['total_income'][0]) else 0
        total_expense = df_expenses['total_expense'][0] if not df_expenses.empty and pd.notna(df_expenses['total_expense'][0]) else 0
        current_balance = total_income - total_expense

        col1, col2, col3 = st.columns(3)
        col1.metric(label="🟢 வரவு", value=f"₹ {int(total_income):,}")
        col2.metric(label="🔴 செலவு", value=f"₹ {int(total_expense):,}")
        col3.metric(label="💰 இருப்பு", value=f"₹ {int(current_balance):,}")

        st.divider()

        st.subheader("சமீபத்திய ரசீதுகள் (வரவு)")
        recent_receipts = load_data("""
            SELECT r.receipt_no as "எண்", r.date as "தேதி", d.name as "பெயர்", r.amount as "தொகை", r.purpose as "விவரம்" 
            FROM receipts r 
            LEFT JOIN donors d ON r.mobile = d.mobile 
            ORDER BY r.receipt_no DESC LIMIT 5
        """)
        st.dataframe(recent_receipts, use_container_width=True, hide_index=True)

        st.subheader("சமீபத்திய செலவுகள் (செலவு)")
        recent_expenses = load_data("""
            SELECT expense_id as "எண்", date as "தேதி", category as "வகை", amount as "தொகை", spent_by as "செய்தவர்" 
            FROM expenses 
            ORDER BY expense_id DESC LIMIT 5
        """)
        st.dataframe(recent_expenses, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"டேட்டாபேஸ் இணைப்புப் பிழை: {e}")

# ==========================================
# TAB 2: புதிய ரசீது போடும் வசதி
# ==========================================
with tab2:
    st.subheader("புதிய நன்கொடை பதிவு")
    
    try:
        donors_data = get_all_donors()
        donor_options = ["➕ புதிய பக்தர் (New Donor)"] + [f"{d[0]} - {d[1]}" for d in donors_data]
    except:
        donors_data = []
        donor_options = ["➕ புதிய பக்தர் (New Donor)"]

    selected_option = st.selectbox("🔍 பழைய பக்தரைத் தேடுக", donor_options)
    
    def_mob, def_name, def_rel, def_add, def_thal = "", "", "", "", "இல்லை (No)"
    
    if selected_option != "➕ புதிய பக்தர் (New Donor)":
        sel_mob = selected_option.split(" - ")[0]
        for d in donors_data:
            if d[0] == sel_mob:
                def_mob, def_name = d[0], d[1]
                def_rel = d[2] if d[2] else ""
                def_add = d[3] if d[3] else ""
                def_thal = d[4] if d[4] else "இல்லை (No)"
                break
    
    with st.form("receipt_form", clear_on_submit=False):
        mobile = st.text_input("மொபைல் எண் *", value=def_mob, max_chars=10)
        name = st.text_input("பெயர் *", value=def_name)
        relation = st.text_input("த/பெ (அ) க/பெ", value=def_rel)
        address = st.text_area("முகவரி", value=def_add)
        
        thal_index = 0 if def_thal == "ஆம் (Yes)" else 1
        thalaikattu = st.radio("தலைக்கட்டு", ["ஆம் (Yes)", "இல்லை (No)"], index=thal_index, horizontal=True)
        
        purpose = st.selectbox("நன்கொடை விவரம் *", ["சிவராத்திரி பூஜை", "மாதாந்திர பூஜை", "அபிஷேகம்", "பொது நன்கொடை"])
        pay_mode = st.selectbox("பணம் செலுத்தும் முறை", ["பணம் (Cash)", "UPI (GPay/PhonePe)", "Bank Transfer"])
        amount = st.number_input("மொத்த தொகை (Rs) *", min_value=1, step=100)
        
        submitted = st.form_submit_button("ரசீதைச் சேமிக்க (Save)", use_container_width=True)

    if submitted:
        if not mobile or not name or amount <= 0:
            st.error("⚠️ மொபைல் எண், பெயர் மற்றும் தொகையைச் சரியாக நிரப்பவும்!")
        else:
            try:
                conn = psycopg2.connect(NEON_URL)
                cur = conn.cursor()
                
                cur.execute("""
                    INSERT INTO donors (mobile, name, relation, address, thalaikattu) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (mobile) DO UPDATE 
                    SET name=EXCLUDED.name, relation=EXCLUDED.relation, address=EXCLUDED.address, thalaikattu=EXCLUDED.thalaikattu
                """, (mobile, name, relation, address, thalaikattu))
                
                date_today = datetime.now().strftime("%d-%m-%Y")
                generated_receipts = [] 
                
                if thalaikattu == "ஆம் (Yes)" and purpose == "சிவராத்திரி பூஜை" and amount >= 500:
                    cur.execute("INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) VALUES (%s, %s, %s, %s, %s) RETURNING receipt_no", (mobile, 500, "தலைக்கட்டு வரி", date_today, pay_mode))
                    generated_receipts.append({"no": cur.fetchone()[0], "purpose": "தலைக்கட்டு வரி", "amt": 500})
                    
                    amt2 = amount - 500
                    if amt2 > 0:
                        cur.execute("INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) VALUES (%s, %s, %s, %s, %s) RETURNING receipt_no", (mobile, amt2, "சிவராத்திரி நன்கொடை", date_today, pay_mode))
                        generated_receipts.append({"no": cur.fetchone()[0], "purpose": "சிவராத்திரி நன்கொடை", "amt": int(amt2)})
                else:
                    cur.execute("INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) VALUES (%s, %s, %s, %s, %s) RETURNING receipt_no", (mobile, amount, purpose, date_today, pay_mode))
                    generated_receipts.append({"no": cur.fetchone()[0], "purpose": purpose, "amt": int(amount)})
                
                conn.commit()
                conn.close()
                st.cache_data.clear()
                
                st.success("✅ தரவுகள் வெற்றிகரமாக கிளவுடில் சேமிக்கப்பட்டன!")
                
                st.markdown("### 🧾 உங்களின் PDF ரசீதுகள்:")
                
                for rec in generated_receipts:
                    pdf_filename = create_pdf(rec['no'], date_today, name, relation, mobile, rec['purpose'], rec['amt'], num_to_tamil_words(rec['amt']))
                    
                    if pdf_filename and os.path.exists(pdf_filename):
                        with open(pdf_filename, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        colA, colB = st.columns(2)
                        with colA:
                            st.download_button(
                                label=f"📄 PDF டவுன்லோட் (ரசீது: {rec['no']})",
                                data=pdf_bytes,
                                file_name=f"Kangeyan_Temple_Receipt_{rec['no']}.pdf",
                                mime="application/pdf",
                                key=f"dl_btn_{rec['no']}",
                                use_container_width=True
                            )
                        with colB:
                            msg = f"வணக்கம் {name}, அருள்மிகு காங்கேயன் கோவில் நன்கொடை பெறப்பட்டது. விவரம்: {rec['purpose']}, தொகை: Rs.{rec['amt']}. ரசீது எண்: {rec['no']}. நன்றி!"
                            safe_msg = urllib.parse.quote(msg)
                            wa_url = f"https://wa.me/91{mobile}?text={safe_msg}"
                            st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:8px 16px; border-radius:4px; font-weight:bold; width:100%;">📱 WhatsApp</button></a>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ பிழை ஏற்பட்டது: {e}")

# ==========================================
# TAB 3: பழைய ரசீது டவுன்லோட் (Reprint)
# ==========================================
with tab3:
    st.subheader("🖨️ பழைய ரசீதை மீண்டும் எடுக்க")
    st.info("💡 நீங்கள் டவுன்லோட் செய்யத் தவறிய அல்லது பழைய ரசீதுகளை இங்கிருந்து மீண்டும் PDF-ஆக எடுத்துக்கொள்ளலாம்.")
    
    try:
        all_recs = get_all_receipts_history()

        if all_recs:
            rec_options = [f"ரசீது எண்: {r[0]} | {r[3]} | {r[5]} (Rs.{int(r[6])})" for r in all_recs]
            selected_rec_str = st.selectbox("டவுன்லோட் செய்ய வேண்டிய ரசீதைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்ந்தெடுக்கவும் --"] + rec_options)
            
            if selected_rec_str != "-- தேர்ந்தெடுக்கவும் --":
                sel_no = int(selected_rec_str.split(" | ")[0].replace("ரசீது எண்: ", ""))
                rec_data = next(r for r in all_recs if r[0] == sel_no)
                
                amt = int(rec_data[6]) 
                
                pdf_file = create_pdf(rec_data[0], rec_data[1], rec_data[3], rec_data[4] if rec_data[4] else "", rec_data[2], rec_data[5], amt, num_to_tamil_words(amt))
                
                if pdf_file and os.path.exists(pdf_file):
                    with open(pdf_file, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.write("---")
                    st.success(f"✅ ரசீது எண் {sel_no} டவுன்லோட் செய்யத் தயார்!")
                    st.download_button(
                        label=f"📄 ரசீது {sel_no}-ஐ டவுன்லோட் செய்யவும்", 
                        data=pdf_bytes, 
                        file_name=f"Kangeyan_Temple_Receipt_{sel_no}.pdf", 
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.warning("ரசீதுகள் எதுவும் காணப்படவில்லை.")
            
    except Exception as e:
        st.error(f"பிழை: {e}")

# ==========================================
# TAB 4: செலவுகள் பதிவு (Expenses)
# ==========================================
with tab4:
    st.subheader("💸 புதிய செலவு பதிவு")
    st.info("💡 கோவிலின் மாதாந்திர மற்றும் இதர செலவுகளை இங்கே பதிவு செய்து கொள்ளலாம்.")
    
    with st.form("expense_form", clear_on_submit=True):
        date_today = datetime.now().strftime("%d-%m-%Y")
        
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.text_input("தேதி (Date) *", value=date_today)
        with col2:
            exp_amount = st.number_input("தொகை (Amount Rs) *", min_value=1, step=50)
            
        # செலவு வகைகள் உங்கள் புகைப்படத்தில் உள்ளபடி அப்டேட் செய்யப்பட்டுள்ளது
        exp_category = st.selectbox("செலவு வகை (Category) *", [
            "பூக்கள் / மாலை", 
            "மின்சாரம்", 
            "சம்பளம்", 
            "பராமரிப்பு", 
            "அன்னதானம்", 
            "பண்டிகை செலவு", 
            "வங்கி செலவுகள்", 
            "இதர செலவுகள்"
        ])
        
        exp_desc = st.text_area("குறிப்பு (Description)")
        
        col3, col4 = st.columns(2)
        with col3:
            exp_spent_by = st.text_input("செலவு செய்தவர் (Spent By) *")
        with col4:
            exp_pay_mode = st.selectbox("பணம் செலுத்தும் முறை", ["பணம் (Cash)", "UPI (GPay/PhonePe)", "Bank Transfer"])
        
        submitted_exp = st.form_submit_button("செலவைச் சேமிக்க (Save Expense)", use_container_width=True)
        
        if submitted_exp:
            if not exp_amount or not exp_spent_by:
                st.error("⚠️ தொகையையும், செலவு செய்தவர் பெயரையும் கட்டாயம் நிரப்பவும்!")
            else:
                try:
                    conn = psycopg2.connect(NEON_URL)
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO expenses (date, category, amount, description, spent_by, pay_mode) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (exp_date, exp_category, exp_amount, exp_desc, exp_spent_by, exp_pay_mode))
                    conn.commit()
                    conn.close()
                    
                    st.cache_data.clear() # டேஷ்போர்டை Refresh செய்ய
                    st.success(f"✅ செலவு (Rs.{exp_amount}) வெற்றிகரமாக கிளவுடில் பதியப்பட்டது!")
                except Exception as e:
                    st.error(f"❌ பிழை: {e}")

st.caption("Developed for Kangeyan Temple by G.S. Kannan")
