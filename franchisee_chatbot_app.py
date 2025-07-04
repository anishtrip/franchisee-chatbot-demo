import streamlit as st
import pandas as pd
import datetime
import re

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
question_options = [
    "Why is my food cost high this month?",
    "How do I compare to other stores in my brand?",
    "What’s my average check this month?",
    "Are my beverage sales too low?",
    "What if I increase my average check by $1?",
    "What was my total sales last month?",
    "How many transactions did I have last month?",
    "Which daypart is underperforming?",
    "Am I overstaffed on weekdays?",
    "Am I overordering anything?"
]
user_input = st.selectbox("Choose a question:", question_options)

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

    elif "average check" in question.lower() and "increase" not in question.lower():
        return f"Your average check in {recent_month.strftime('%B %Y')} was ${pnl['Avg_Check']:.2f} across {pnl['Transactions']} transactions."

    elif "increase my average check" in question.lower():
        try:
            increase_amount = 1.00
            match = re.search(r'increase my average check by \$?([0-9]+\.?[0-9]*)', question.lower())
            if match:
                increase_amount = float(match.group(1))

            new_sales = (pnl['Avg_Check'] + increase_amount) * pnl['Transactions']
            sales_gain = new_sales - pnl['Net_Sales']
            ebitda_estimate = sales_gain * 0.4

            return (
                f"If you increase your average check by ${increase_amount:.2f}, your monthly sales could rise by approximately ${sales_gain:,.0f}.\n"
                f"Assuming a 40% profit margin, your EBITDA could increase by about ${ebitda_estimate:,.0f}."
            )
        except:
            return "I'm unable to calculate this scenario right now. Please check your data or try again later."

    elif "beverage" in question.lower():
        recent_month = menu_mix_df[menu_mix_df['Store_ID'] == store_id]['Month'].max()
        store_data = menu_mix_df[
            (menu_mix_df['Store_ID'] == store_id) &
            (menu_mix_df['Month'] == recent_month) &
            (menu_mix_df['Menu_Category'].str.lower().str.contains("beverage"))
        ]

        if not store_data.empty:
            store_sales = store_data['Sales'].sum()
            total_sales = menu_mix_df[
                (menu_mix_df['Store_ID'] == store_id) &
                (menu_mix_df['Month'] == recent_month)
            ]['Sales'].sum()
            beverage_pct = store_sales / total_sales * 100

            brand = store_df[store_df['Store_ID'] == store_id]['Brand'].values[0]
            brand_avg = menu_mix_df[
                (menu_mix_df['Brand'] == brand) &
                (menu_mix_df['Month'] == recent_month) &
                (menu_mix_df['Menu_Category'].str.lower().str.contains("beverage"))
            ].groupby('Store_ID')['Sales'].sum().mean()

            brand_total_avg = menu_mix_df[
                (menu_mix_df['Brand'] == brand) &
                (menu_mix_df['Month'] == recent_month)
            ].groupby('Store_ID')['Sales'].sum().mean()

            brand_bev_pct = brand_avg / brand_total_avg * 100

            diff = beverage_pct - brand_bev_pct
            if diff < -1:
                return f"Your beverage sales make up {beverage_pct:.1f}% of your sales in {recent_month.strftime('%B %Y')}, which is below the brand average of {brand_bev_pct:.1f}%. Consider bundling beverages with mains to improve this."
            else:
                return f"Your beverage sales contribution is {beverage_pct:.1f}%, in line with the brand average of {brand_bev_pct:.1f}%. Looks good!"
        else:
            return "No beverage sales were recorded for this store in the latest month."

    elif "total sales" in question.lower():
        return f"Your total sales in {recent_month.strftime('%B %Y')} were ${pnl['Net_Sales']:,.0f}."

    elif "transactions" in question.lower():
        return f"You had {pnl['Transactions']} transactions in {recent_month.strftime('%B %Y')}."

    elif "daypart" in question.lower() or "breakfast" in question.lower() or "lunch" in question.lower() or "dinner" in question.lower():
        daypart = daypart_sales_df[
            (daypart_sales_df['Store_ID'] == store_id) &
            (daypart_sales_df['Month'] == recent_month)
        ].iloc[0]
        return (
            f"In {recent_month.strftime('%B %Y')}, your daypart sales were:\n"
            f"- Breakfast: ${daypart['Breakfast_Sales']:,.0f}\n"
            f"- Lunch: ${daypart['Lunch_Sales']:,.0f}\n"
            f"- Dinner: ${daypart['Dinner_Sales']:,.0f}\n"
            f"- Late Night: ${daypart['Late_Night_Sales']:,.0f}"
        )

    elif "overstaffed" in question.lower() or "labor" in question.lower():
        benchmark = 28.0
        labor_pct = pnl['Labor_Cost_%']
        if labor_pct > benchmark:
            return f"Your labor cost was {labor_pct:.1f}% in {recent_month.strftime('%B %Y')}, which is above the brand benchmark of {benchmark}%. Consider reviewing your weekday staffing plan."
        else:
            return f"Your labor cost was {labor_pct:.1f}% — within benchmark."

    elif "overordering" in question.lower() or "purchase variance" in question.lower():
        recent_weeks = purchase_df[(purchase_df['Store_ID'] == store_id)].sort_values(by='Week', ascending=False).head(4)
        flagged = recent_weeks[recent_weeks['Variance'] > 10]
        if not flagged.empty:
            item_summary = flagged.groupby('Item')['Variance'].sum().sort_values(ascending=False).head(3)
            response = "You are potentially overordering the following items:\n"
            for item, var in item_summary.items():
                response += f"- {item}: {int(var)} units over ideal in recent weeks\n"
            return response
        else:
            return "No major overordering detected in the past month."

    else:
        return "I'm still learning to answer that question. Try asking about food cost, average check, or sales comparisons."

if user_input:
    response = generate_response(user_input, store_id)
    st.markdown(f"**Bot:** {response}")
