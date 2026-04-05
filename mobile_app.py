import streamlit as st
import psycopg2
import pandas as pd

# உங்களின் Cloud Database Link
NEON_URL = "postgresql://neondb_owner:npg_WqJld5Uu6nCE@ep-lucky-glitter-a14oql0y.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# பக்கத்தின் வடிவமைப்பு (Mobile Friendly)
st.set_page_config(page_title="காங்கேயன் கோவில்", page_icon="🙏", layout="centered")

st.markdown("<h2 style='text-align: center; color: darkred;'>அருள்மிகு காங்கேயன் கோவில்</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>மொபைல் டேஷ்போர்டு 📱</p>", unsafe_allow_html=True)
st.divider()

# Cloud-ல் இருந்து டேட்டாவை எடுக்கும் Function
@st.cache_data(ttl=10) # 10 விநாடிக்கு ஒருமுறை Refresh ஆகும்
def load_data(query):
    conn = psycopg2.connect(NEON_URL)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

try:
    # மொத்த வரவு மற்றும் செலவுகளைக் கணக்கிடுதல்
    df_receipts = load_data("SELECT SUM(amount) as total_income FROM receipts")
    df_expenses = load_data("SELECT SUM(amount) as total_expense FROM expenses")
    
    total_income = df_receipts['total_income'][0] if not df_receipts.empty and pd.notna(df_receipts['total_income'][0]) else 0
    total_expense = df_expenses['total_expense'][0] if not df_expenses.empty and pd.notna(df_expenses['total_expense'][0]) else 0
    current_balance = total_income - total_expense

    # அழகான கட்டங்களில் (Metrics) காட்டுதல்
    col1, col2, col3 = st.columns(3)
    col1.metric(label="🟢 மொத்த வரவு", value=f"₹ {total_income:,.2f}")
    col2.metric(label="🔴 மொத்த செலவு", value=f"₹ {total_expense:,.2f}")
    col3.metric(label="💰 கையிருப்பு", value=f"₹ {current_balance:,.2f}")

    st.divider()

    # சமீபத்திய ரசீதுகள் (Last 5 Receipts)
    st.subheader("சமீபத்திய ரசீதுகள் (Latest Receipts)")
    recent_receipts = load_data("""
        SELECT r.receipt_no as "எண்", r.date as "தேதி", d.name as "பெயர்", r.amount as "தொகை", r.purpose as "விவரம்" 
        FROM receipts r 
        LEFT JOIN donors d ON r.mobile = d.mobile 
        ORDER BY r.receipt_no DESC LIMIT 5
    """)
    st.dataframe(recent_receipts, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"டேட்டாபேஸ் இணைப்புப் பிழை: {e}")

st.caption("Developed for Kangeyan Temple by G.S. Kannan")