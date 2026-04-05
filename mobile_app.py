import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# உங்களின் Cloud Database Link
NEON_URL = "postgresql://neondb_owner:npg_WqJld5Uu6nCE@ep-lucky-glitter-a14oql0y.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# பக்கத்தின் வடிவமைப்பு (Mobile Friendly)
st.set_page_config(page_title="காங்கேயன் கோவில்", page_icon="🙏", layout="centered")

st.markdown("<h2 style='text-align: center; color: darkred;'>அருள்மிகு காங்கேயன் கோவில்</h2>", unsafe_allow_html=True)
st.divider()

# இரண்டு தனித்தனி பக்கங்கள் (Tabs) உருவாக்குதல்
tab1, tab2 = st.tabs(["📊 டேஷ்போர்டு", "✍️ புதிய ரசீது போடுக"])

# Cloud-ல் இருந்து டேட்டாவை எடுக்கும் Function
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
    cur.execute("SELECT mobile, name, relation, address FROM donors")
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
    
    # 1. டேட்டாபேஸில் உள்ள பழைய முகவரிகளை எடுப்பது
    try:
        donors_data = get_all_donors()
        donor_options = ["➕ புதிய பக்தர் (New Donor)"] + [f"{d[0]} - {d[1]}" for d in donors_data]
    except:
        donors_data = []
        donor_options = ["➕ புதிய பக்தர் (New Donor)"]

    # 2. Search Box: இங்கே டைப் செய்தால் பில்டர் ஆகும்!
    selected_option = st.selectbox("🔍 பழைய பக்தரைத் தேடுக (Search by Mobile/Name)", donor_options)
    
    # 3. தேர்ந்தெடுக்கப்பட்ட பக்தரின் டேட்டாவை பிரித்தெடுத்தல்
    def_mob = ""
    def_name = ""
    def_rel = ""
    def_add = ""
    
    if selected_option != "➕ புதிய பக்தர் (New Donor)":
        sel_mob = selected_option.split(" - ")[0]
        for d in donors_data:
            if d[0] == sel_mob:
                def_mob = d[0]
                def_name = d[1]
                def_rel = d[2] if d[2] else ""
                def_add = d[3] if d[3] else ""
                break
    
    # 4. Form உருவாக்குதல்
    with st.form("receipt_form", clear_on_submit=True):
        mobile = st.text_input("மொபைல் எண் (Mobile No) *", value=def_mob, max_chars=10)
        name = st.text_input("பெயர் (Name) *", value=def_name)
        relation = st.text_input("த/பெ (அ) க/பெ (Relation)", value=def_rel)
        address = st.text_area("முகவரி (Address)", value=def_add)
        
        purpose = st.selectbox("நன்கொடை விவரம் *", ["சிவராத்திரி பூஜை", "மாதாந்திர பூஜை", "அபிஷேகம்", "பொது நன்கொடை"])
        pay_mode = st.selectbox("பணம் செலுத்தும் முறை", ["பணம் (Cash)", "UPI (GPay/PhonePe)", "Bank Transfer"])
        amount = st.number_input("தொகை (Rs) *", min_value=1, step=100)
        
        # Submit Button
        submitted = st.form_submit_button("ரசீதைச் சேமிக்க (Save)", use_container_width=True)
        
        if submitted:
            if not mobile or not name or amount <= 0:
                st.error("⚠️ தயவுசெய்து மொபைல் எண், பெயர் மற்றும் தொகையைச் சரியாக நிரப்பவும்!")
            else:
                try:
                    conn = psycopg2.connect(NEON_URL)
                    cur = conn.cursor()
                    
                    # 1. முகவரிப் புத்தகத்தில் சேமிக்க (Donors Table)
                    cur.execute("""
                        INSERT INTO donors (mobile, name, relation, address, thalaikattu) 
                        VALUES (%s, %s, %s, %s, 'இல்லை (No)')
                        ON CONFLICT (mobile) DO UPDATE 
                        SET name=EXCLUDED.name, relation=EXCLUDED.relation, address=EXCLUDED.address
                    """, (mobile, name, relation, address))
                    
                    # 2. ரசீது பதிவேட்டில் சேமிக்க (Receipts Table)
                    date_today = datetime.now().strftime("%d-%m-%Y")
                    cur.execute("""
                        INSERT INTO receipts (mobile, amount, purpose, date, pay_mode) 
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING receipt_no
                    """, (mobile, amount, purpose, date_today, pay_mode))
                    
                    new_receipt_no = cur.fetchone()[0]
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ அருமை! {name} அவர்களின் நன்கொடை (Rs.{amount}) சேமிக்கப்பட்டது! (ரசீது எண்: {new_receipt_no})")
                    
                    # டேஷ்போர்டை Refresh செய்ய
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"❌ பிழை ஏற்பட்டது: {e}")

st.caption("Developed for Kangeyan Temple by G.S. Kannan")
