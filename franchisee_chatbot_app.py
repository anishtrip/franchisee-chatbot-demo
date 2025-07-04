import streamlit as st
import pandas as pd
import datetime

# Load datasets
@st.cache_data
def load_data():
    store_df = pd.read_csv("store_metadata.csv")
    pnl_df = pd.read_csv("monthly_pnl_data.csv", parse_dates=['Month'])
    purchase_df = pd.read_csv("weekly_purchase_data.csv", parse_dates=['Week'])
    menu_mix_df = pd.read_csv("monthly_menu_mix.csv", parse_dates=['Month'])
    daypart_sales_df = pd.read_csv("monthly_daypart_sales.csv", parse_dates=['Month'])
    return store_df, pnl_df, purchase_df, menu_mix_df, daypart_sales_df

store_df, pnl_df, purchase_df, menu_mix_df, daypart_sales_df = load_data()

# UI: Sidebar
st.sidebar.title("Store Selection")
selected_brand = st.sidebar.selectbox("Select Brand", store_df['Brand'].unique())
filtered_stores = store_df[store_df['Brand'] == selected_brand]
selected_store = st.sidebar.selectbox("Select Store", filtered_stores['Store_Name'])
store_id = filtered_stores[filtered_stores['Store_Name'] == selected_store]['Store_ID'].values[0]

# Chat UI
st.title("Franchisee Financial Advisor Chatbot")
st.markdown("Ask questions about your store's financials, costs, or sales trends.")
user_input = st.text_input("You:", "Why is my food cost high this month?")

# Simulate Chatbot Response
def generate_response(question, store_id):
    recent_month = pnl_df[pnl_df['Store_ID'] == store_id]['Month'].max()
    pnl = pnl_df[(pnl_df['Store_ID'] == store_id) & (pnl_df['Month'] == recent_month)].iloc[0]
    
    if "food cost" in question.lower():
        benchmark = 30.0
        variance = pnl['Food_Cost_%'] - benchmark
        if variance > 0:
            return f"Your food cost for {recent_month.strftime('%B %Y')} was {pnl['Food_Cost_%']}%, which is {variance:.1f} pts above the brand benchmark of {benchmark}%. Review high-usage items and variance in weekly purchases."
        else:
            return f"Your food cost is under control at {pnl['Food_Cost_%']}%. Keep it up!"

    elif "compare" in question.lower():
        brand_avg = pnl_df[(pnl_df['Brand'] == pnl['Brand']) & (pnl_df['Month'] == recent_month)]['Net_Sales'].mean()
        return f"Your sales in {recent_month.strftime('%B %Y')} were ${pnl['Net_Sales']:,}. The average for your brand was ${brand_avg:,.0f}."

    elif "average check" in question.lower():
        return f"Your average check in {recent_month.strftime('%B %Y')} was ${pnl['Avg_Check']:.2f} across {pnl['Transactions']} transactions."

    else:
        return "I'm still learning to answer that question. Try asking about food cost, average check, or sales comparisons."

if user_input:
    response = generate_response(user_input, store_id)
    st.markdown(f"**Bot:** {response}")
