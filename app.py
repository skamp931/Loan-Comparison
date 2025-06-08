import streamlit as st
import math

# アプリのタイトルと説明
st.set_page_config(layout="wide", page_title="住宅ローン比較アプリ")
st.title("🏡 住宅ローン比較アプリ")
st.markdown("異なる条件で住宅ローンを比較し、月々の支払い額と総支払額を計算しましょう。")

# カスタムCSS
st.markdown("""
<style>
    /* 全体的なフォントと背景 */
    body {
        font-family: 'Inter', sans-serif;
        background-color: #f0f2f6;
    }
    .main {
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        margin-bottom: 20px;
        font-size: 2.5em;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    .stNumberInput, .stSlider {
        margin-bottom: 15px;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 1.1em;
        transition: background-color 0.3s ease;
        border: none;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
    .metric-card {
        background-color: #ecf0f1;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .metric-card h3 {
        color: #2c3e50;
        font-size: 1.5em;
        margin-bottom: 10px;
    }
    .metric-card p {
        color: #3498db;
        font-size: 2em;
        font-weight: bold;
    }
    .loan-section {
        background-color: #fdfdfd;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
    }
    .comparison-result {
        background-color: #e8f5e9; /* Light green for positive comparison */
        border-left: 5px solid #4CAF50;
        padding: 15px;
        margin-top: 20px;
        border-radius: 5px;
        font-size: 1.1em;
        color: #2e7d32;
    }
    .comparison-result.warning {
        background-color: #fff3e0; /* Light orange for warning/less favorable */
        border-left: 5px solid #ff9800;
        color: #ef6c00;
    }
    .st-emotion-cache-16txt4v p { /* Adjust specific streamlit text color */
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

# ローン計算関数
def calculate_loan(loan_amount, annual_interest_rate, loan_term_years, down_payment=0):
    """
    住宅ローンの月々の支払い額と総支払額を計算します。
    """
    principal = loan_amount - down_payment
    if principal <= 0:
        return 0, 0 # 頭金がローン額以上の場合

    monthly_interest_rate = annual_interest_rate / 100 / 12
    number_of_payments = loan_term_years * 12

    if monthly_interest_rate == 0:
        monthly_payment = principal / number_of_payments
    else:
        # 月々の支払い額の計算式
        monthly_payment = principal * (monthly_interest_rate * (1 + monthly_interest_rate)**number_of_payments) / \
                          ((1 + monthly_interest_rate)**number_of_payments - 1)

    total_payment = monthly_payment * number_of_payments
    return monthly_payment, total_payment

# レイアウト用のカラムを作成
col1, col2 = st.columns(2)

# ローン1の入力セクション
with col1:
    st.subheader("ローンAの条件")
    st.markdown('<div class="loan-section">', unsafe_allow_html=True)
    loan_amount_a = st.number_input("ローンAの借入希望額 (円)", min_value=1000000, max_value=500000000, value=30000000, step=100000)
    down_payment_a = st.number_input("ローンAの頭金 (円)", min_value=0, max_value=loan_amount_a, value=0, step=100000)
    annual_interest_rate_a = st.slider("ローンAの年利 (%)", min_value=0.1, max_value=10.0, value=1.5, step=0.01)
    loan_term_years_a = st.slider("ローンAの返済期間 (年)", min_value=1, max_value=50, value=35, step=1)
    st.markdown('</div>', unsafe_allow_html=True)

# ローン2の入力セクション
with col2:
    st.subheader("ローンBの条件")
    st.markdown('<div class="loan-section">', unsafe_allow_html=True)
    loan_amount_b = st.number_input("ローンBの借入希望額 (円)", min_value=1000000, max_value=500000000, value=30000000, step=100000)
    down_payment_b = st.number_input("ローンBの頭金 (円)", min_value=0, max_value=loan_amount_b, value=0, step=100000)
    annual_interest_rate_b = st.slider("ローンBの年利 (%)", min_value=0.1, max_value=10.0, value=1.8, step=0.01)
    loan_term_years_b = st.slider("ローンBの返済期間 (年)", min_value=1, max_value=50, value=30, step=1)
    st.markdown('</div>', unsafe_allow_html=True)

# 計算と結果表示
st.header("計算結果")
results_col1, results_col2 = st.columns(2)

# ローンAの結果
with results_col1:
    st.subheader("ローンAの計算結果")
    if loan_amount_a - down_payment_a <= 0:
        st.error("ローンAの借入希望額が頭金以下です。")
    else:
        monthly_payment_a, total_payment_a = calculate_loan(loan_amount_a, annual_interest_rate_a, loan_term_years_a, down_payment_a)
        st.markdown(f'<div class="metric-card"><h3>月々の支払い額</h3><p>¥ {int(monthly_payment_a):,}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><h3>総支払額</h3><p>¥ {int(total_payment_a):,}</p></div>', unsafe_allow_html=True)

# ローンBの結果
with results_col2:
    st.subheader("ローンBの計算結果")
    if loan_amount_b - down_payment_b <= 0:
        st.error("ローンBの借入希望額が頭金以下です。")
    else:
        monthly_payment_b, total_payment_b = calculate_loan(loan_amount_b, annual_interest_rate_b, loan_term_years_b, down_payment_b)
        st.markdown(f'<div class="metric-card"><h3>月々の支払い額</h3><p>¥ {int(monthly_payment_b):,}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><h3>総支払額</h3><p>¥ {int(total_payment_b):,}</p></div>', unsafe_allow_html=True)

# 比較結果
st.header("比較")
if (loan_amount_a - down_payment_a > 0) and (loan_amount_b - down_payment_b > 0):
    if total_payment_a < total_payment_b:
        st.markdown(f'<div class="comparison-result">ローンAの方が総支払額が**¥ {int(total_payment_b - total_payment_a):,}**少なくなります。</div>', unsafe_allow_html=True)
    elif total_payment_b < total_payment_a:
        st.markdown(f'<div class="comparison-result">ローンBの方が総支払額が**¥ {int(total_payment_a - total_payment_b):,}**少なくなります。</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="comparison-result warning">両ローンの総支払額はほぼ同じです。</div>', unsafe_allow_html=True)
else:
    st.info("比較を行うには、両方のローンで有効な借入額が必要です。")

st.markdown("---")
st.markdown("このアプリは概算計算を提供します。実際のローン条件は金融機関にご確認ください。")

