import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import urllib.parse

# உங்களின் Cloud Database Link
NEON_URL = "postgresql://neondb_owner:npg_WqJld5Uu6nCE@ep-lucky-glitter-a14oql0y.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

st.set_page_config(page_title="காங்கேயன் கோவில்", page_icon="🙏", layout="centered")

st.markdown("<h2 style='text-align: center; color: darkred;'>அருள்மிகு காங்கேயன் கோவில்</h2>", unsafe_allow_html=True)
st.divider()

tab1, tab2 = st.tabs(["📊 டேஷ்போர்டு", "✍️ புதிய ரசீது போடுக"])

@st.cache_data(ttl=5) 
def load_data(query):
    conn = psycopg2.connect(NEON_URL)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=5)
def get_all_donors():
    conn = psycopg2.connect(NEON_URL)
    cur = conn.cursor()
    # thalaikattu தகவலையும் எடுக்கிறோம்
    cur.execute("SELECT mobile, name, relation, address, thalaikattu FROM donors")
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
        col1.metric(label="🟢 வரவு", value=f"₹ {total_income:,.0f}")
        col2.metric(label="🔴 செலவு", value=f"₹ {total_expense:,.0f}")
        col3.metric(label="💰 இருப்பு", value=f"₹ {current_balance:,.0f}")

        st.divider()

        st.subheader("சமீபத்திய ரசீதுகள்")
        recent_receipts = load_data("""
            SELECT r.receipt_no as "எண்", r.date as "தேதி", d.name as "பெயர்", r.amount as "தொகை", r.purpose as "விவரம்" 
            FROM receipts r 
            LEFT JOIN donors d ON r.mobile = d.mobile 
            ORDER BY r.receipt_no DESC LIMIT 10
        """)
        st.dataframe(recent_receipts, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"டேட்டாபேஸ் இணைப்புப் பிழை: {e}")

# ==========================================
# TAB 2: மொபைலில் புதிய ரசீது போடும் வசதி
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
    
    # Form உருவாக்குதல் (clear_on_submit=False ஆக மாற்றப்பட்டுள்ளது, ரசீது காட்ட ஏதுவாக)
    with st.form("receipt_form", clear_on_submit=False):
        mobile = st.text_input("மொபைல் எண் *", value=def_mob, max_chars=10)
        name = st.text_input("பெயர் *", value=def_name)
        relation = st.text_input("த/பெ (அ) க/பெ", value=def_rel)
        address = st.text_area("முகவரி", value=def_add)
        
        # தலைக்கட்டு ஆப்ஷன் சேர்க்கப்பட்டுள்ளது
        thal_index = 0 if def_thal == "ஆம் (Yes)" else 1
        thalaikattu = st.radio("தலைக்கட்டு", ["ஆம் (Yes)", "இல்லை (No)"], index=thal_index, horizontal=True)
        
        purpose = st.selectbox("நன்கொடை விவரம் *", ["சிவராத்திரி பூஜை", "மாதாந்திர பூஜை", "அபிஷேகம்", "பொது நன்கொடை"])
        pay_mode = st.selectbox("பணம் செலுத்தும் முறை", ["பணம் (Cash)", "UPI (GPay/PhonePe)", "Bank Transfer"])
        amount = st.number_input("மொத்த தொகை (Rs) *", min_value=1, step=100)
        
        submitted = st.form_submit_button("ரசீதைச் சேமிக்க (Save)", use_container_width=True)

    # ==========================================
    # Form Submit செய்த பிறகு நடக்கும் வேலைகள்
    # ==========================================
    if submitted:
        if not mobile or not name or amount <= 0:
            st.error("⚠️ மொபைல் எண், பெயர் மற்றும் தொகையைச் சரியாக நிரப்பவும்!")
        else:
            try:
                conn = psycopg2.connect(NEON_URL)
                cur = conn.cursor()
                
                # 1. முகவரிப் புத்தகத்தில் சேமிக்க
                cur.execute("""
                    INSERT INTO donors (mobile, name, relation, address, thalaikattu) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (mobile) DO UPDATE 
                    SET name=EXCLUDED.name, relation=EXCLUDED.relation, address=EXCLUDED.address, thalaikattu=EXCLUDED.thalaikattu
                """, (mobile, name, relation, address, thalaikattu))
                
                date_today = datetime.now().strftime("%d-%m-%Y")
                generated_receipts = [] # உருவாக்கப்பட்ட ரசீதுகளைச் சேமிக்க
                
                # 2. தலைக்கட்டு விதிமுறை (Splitting Logic)
                if thalaikattu == "ஆம் (Yes)" and purpose == "சிவராத்திரி பூஜை" and amount >= 500:
                    # முதல் ரசீது: தலைக்கட்டு வரி (Rs.500)
                    cur.execute("INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) VALUES (%s, %s, %s, %s, %s) RETURNING receipt_no", (mobile, 500, "தலைக்கட்டு வரி", date_today, pay_mode))
                    rec_no1 = cur.fetchone()[0]
                    generated_receipts.append({"no": rec_no1, "purpose": "தலைக்கட்டு வரி", "amt": 500})
                    
                    # இரண்டாம் ரசீது: மீதித் தொகை
                    amt2 = amount - 500
                    if amt2 > 0:
                        cur.execute("INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) VALUES (%s, %s, %s, %s, %s) RETURNING receipt_no", (mobile, amt2, "சிவராத்திரி நன்கொடை", date_today, pay_mode))
                        rec_no2 = cur.fetchone()[0]
                        generated_receipts.append({"no": rec_no2, "purpose": "சிவராத்திரி நன்கொடை", "amt": amt2})
                else:
                    # சாதாரண ரசீது (தலைக்கட்டு இல்லை என்றால்)
                    cur.execute("INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) VALUES (%s, %s, %s, %s, %s) RETURNING receipt_no", (mobile, amount, purpose, date_today, pay_mode))
                    rec_no = cur.fetchone()[0]
                    generated_receipts.append({"no": rec_no, "purpose": purpose, "amt": amount})
                
                conn.commit()
                conn.close()
                st.cache_data.clear()
                
                st.success("✅ தரவுகள் வெற்றிகரமாக கிளவுடில் சேமிக்கப்பட்டன!")
                
                # ==========================================
                # டிஜிட்டல் ரசீது திரையில் காட்டுதல் (Digital Receipt)
                # ==========================================
                st.markdown("### 🧾 உங்களின் ரசீதுகள்:")
                
                for rec in generated_receipts:
                    st.info(f"""
                    **அருள்மிகு காங்கேயன் கோவில்**
                    ---
                    **ரசீது எண்:** {rec['no']} | **தேதி:** {date_today}
                    **பெயர்:** {name}
                    **விவரம்:** {rec['purpose']}
                    **தொகை:** Rs. {rec['amt']} /-
                    """)
                    
                    # WhatsApp Link உருவாக்குதல்
                    msg = f"வணக்கம் {name}, அருள்மிகு காங்கேயன் கோவில் நன்கொடை பெறப்பட்டது. விவரம்: {rec['purpose']}, தொகை: Rs.{rec['amt']}. ரசீது எண்: {rec['no']}. நன்றி!"
                    safe_msg = urllib.parse.quote(msg)
                    wa_url = f"https://wa.me/91{mobile}?text={safe_msg}"
                    
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:8px 16px; border-radius:4px; font-weight:bold;">📱 WhatsApp-ல் அனுப்பு (Rec {rec["no"]})</button></a>', unsafe_allow_html=True)
                    st.write("") # இடைவெளிக்காக
                
            except Exception as e:
                st.error(f"❌ பிழை ஏற்பட்டது: {e}")

st.caption("Developed for Kangeyan Temple by G.S. Kannan")
