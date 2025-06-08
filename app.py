import streamlit as st
import math
import pandas as pd # Although not directly used for display, can be useful for debugging/future tables

# --- App Configuration ---
st.set_page_config(layout="wide", page_title="住宅ローン比較アプリ")
st.title("🏡 住宅ローン比較アプリ")
st.markdown("異なる条件で住宅ローンを比較し、月々の支払い額と総支払額を計算しましょう。")

# --- Custom CSS ---
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
    .stNumberInput, .stSlider, .stRadio {
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
    /* Sidebar styling */
    .css-1d391kg { /* Target sidebar background */
        background-color: #e0e7ed !important;
    }
    .sidebar-header {
        font-size: 1.3em;
        color: #2c3e50;
        margin-bottom: 15px;
        border-bottom: 1px solid #ccc;
        padding-bottom: 10px;
    }
    .st-emotion-cache-16txt4v p { /* Adjust specific streamlit text color */
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

# --- Loan Calculation Function (now more comprehensive) ---
def calculate_loan(loan_amount, annual_interest_rate, loan_term_years, repayment_type, down_payment=0,
                   early_repayments=None, rate_changes=None):
    """
    住宅ローンの月々の支払い額と総支払額を計算します。
    繰り上げ返済や金利変動も考慮します。

    Args:
        loan_amount (int): 借入希望額
        annual_interest_rate (float): 年利 (%)
        loan_term_years (int): 返済期間 (年)
        repayment_type (str): 返済方法 ("元利均等返済" or "元金均等返済")
        down_payment (int): 頭金
        early_repayments (list): 繰り上げ返済のリスト [(月, 金額), ...]
        rate_changes (list): 金利変更のリスト [(月, 新年利), ...]

    Returns:
        tuple: (最初の月々の支払い額, 総支払額, 最終残高)
    """
    principal = loan_amount - down_payment
    if principal <= 0:
        return 0, 0, 0 # 頭金がローン額以上の場合

    number_of_payments_total = loan_term_years * 12

    current_principal = principal
    total_payment = 0
    first_month_payment = 0 # 最初の月々の支払い額を格納
    payments_made = 0

    # 金利変更と繰り上げ返済を月でソート
    if rate_changes:
        rate_changes_sorted = sorted([rc for rc in rate_changes if rc['month'] > 0], key=lambda x: x['month'])
    else:
        rate_changes_sorted = []

    if early_repayments:
        early_repayments_sorted = sorted([er for er in early_repayments if er['month'] > 0 and er['amount'] > 0], key=lambda x: x['month'])
    else:
        early_repayments_sorted = []


    # 現在の金利を初期化
    current_annual_rate = annual_interest_rate
    current_monthly_rate = current_annual_rate / 100 / 12

    # 毎月シミュレーションを実行
    for month in range(1, int(number_of_payments_total) + 1):
        if current_principal <= 0: # ローンが完済された場合
            break

        # 金利変更の適用
        for rc in rate_changes_sorted:
            if month == rc['month']:
                current_annual_rate = rc['new_rate']
                current_monthly_rate = current_annual_rate / 100 / 12
                # st.sidebar.write(f"月 {month}: 金利が {rc['new_rate']}% に変更されました。") # デバッグ/情報表示

        # 返済方法と現在の金利、元金に基づいて月々の支払い額を計算
        if repayment_type == "元利均等返済":
            remaining_payments = number_of_payments_total - payments_made

            if remaining_payments <= 0:
                monthly_payment = current_principal # 最終残高を支払う
            elif current_monthly_rate == 0:
                monthly_payment = current_principal / remaining_payments
            else:
                try:
                    # 残りの元金と期間で月々の支払い額を再計算
                    monthly_payment = current_principal * (current_monthly_rate * (1 + current_monthly_rate)**remaining_payments) / \
                                      ((1 + current_monthly_rate)**remaining_payments - 1)
                except ZeroDivisionError:
                    # 非常に低い金利や長い期間で分母が0になる場合
                    monthly_payment = current_principal / remaining_payments
                except OverflowError:
                    st.error("計算中にオーバーフローエラーが発生しました。期間または金利を見直してください。")
                    return 0, 0, current_principal

            interest_component = current_principal * current_monthly_rate
            principal_component = monthly_payment - interest_component

            # 元金がマイナスにならないように調整
            if principal_component < 0:
                principal_component = 0 # 利息のみで元金が減らない場合
            if principal_component > current_principal:
                principal_component = current_principal # 残元金を超えないように調整

            # 最終支払い額が残元金+利息を超える場合
            if current_principal - principal_component < 0:
                principal_component = current_principal
                monthly_payment = current_principal + interest_component

        elif repayment_type == "元金均等返済":
            # 元金部分の月々の返済額は固定
            monthly_principal_payment = principal / number_of_payments_total
            interest_component = current_principal * current_monthly_rate
            monthly_payment = monthly_principal_payment + interest_component

            principal_component = monthly_principal_payment

            # 最終支払い額で元金が残らないように調整
            if principal_component > current_principal:
                 principal_component = current_principal
                 monthly_payment = current_principal + interest_component # 最終支払い額は残元金＋利息

        total_payment += monthly_payment
        current_principal -= principal_component
        payments_made += 1

        if month == 1:
            first_month_payment = monthly_payment

        # 繰り上げ返済の適用
        for er_idx, er in enumerate(early_repayments_sorted):
            if month == er['month'] and er['amount'] > 0:
                # st.sidebar.write(f"月 {month}: 繰り上げ返済 {er['amount']:,}円が適用されました。") # デバッグ/情報表示
                current_principal -= er['amount']
                early_repayments_sorted[er_idx]['amount'] = 0 # 適用済みとしてマーク

                if current_principal <= 0:
                    break # ローンが繰り上げ返済により完済された場合

    return first_month_payment, total_payment, max(0, current_principal) # 最終残高が負にならないようにする

# --- Sidebar for Formulas ---
st.sidebar.markdown('<div class="sidebar-header">シミュレーションに使った数式</div>', unsafe_allow_html=True)

st.sidebar.subheader("元利均等返済 (Equal Principal and Interest Repayment)")
st.sidebar.markdown(r"""
月々の支払い額 $M$:
$M = P \left[ \frac{r(1+r)^n}{(1+r)^n - 1} \right]$

ここで、
- $P$: 借入元金
- $r$: 月利 (年利 / 1200)
- $n$: 返済回数 (返済期間(年) $\times$ 12)
""")

st.sidebar.subheader("元金均等返済 (Principal Equal Repayment)")
st.sidebar.markdown(r"""
月々の元金返済額 $M_P$:
$M_P = \frac{P}{n}$

$k$回目の月々の利息額 $I_k$:
$I_k = (P - (k-1)M_P) \times r$

$k$回目の月々の支払い額 $M_k$:
$M_k = M_P + I_k$

ここで、
- $P$: 借入元金
- $r$: 月利 (年利 / 1200)
- $n$: 返済回数 (返済期間(年) $\times$ 12)
- $k$: 返済回 (1, 2, ..., n)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("※繰り上げ返済や金利変動は、上記数式に基づいて毎月再計算されます。")

# --- Loan Input Sections ---
col1, col2 = st.columns(2)

# Session state initialization for dynamic rate changes
if 'num_rate_changes_a' not in st.session_state:
    st.session_state.num_rate_changes_a = 0
if 'rate_changes_a_inputs' not in st.session_state:
    st.session_state.rate_changes_a_inputs = []

if 'num_rate_changes_b' not in st.session_state:
    st.session_state.num_rate_changes_b = 0
if 'rate_changes_b_inputs' not in st.session_state:
    st.session_state.rate_changes_b_inputs = []

# Loan A Inputs
with col1:
    st.subheader("ローンAの条件")
    st.markdown('<div class="loan-section">', unsafe_allow_html=True)
    loan_amount_a = st.number_input("ローンAの借入希望額 (円)", min_value=1000000, max_value=500000000, value=30000000, step=100000, key='la_amt')
    down_payment_a = st.number_input("ローンAの頭金 (円)", min_value=0, max_value=loan_amount_a, value=0, step=100000, key='la_dp')
    loan_term_years_a = st.slider("ローンAの返済期間 (年)", min_value=1, max_value=50, value=35, step=1, key='la_term')
    annual_interest_rate_a_initial = st.slider("ローンAの初期年利 (%)", min_value=0.1, max_value=10.0, value=1.5, step=0.01, key='la_rate_init')
    repayment_type_a = st.radio("ローンAの返済方法", ["元利均等返済", "元金均等返済"], key='la_type', help="元利均等返済は毎月の支払い額が一定、元金均等返済は元金部分が一定で支払い額が徐々に減少します。")

    st.markdown("---")
    st.subheader("ローンAの繰り上げ返済")
    early_repayment_amount_a = st.number_input("繰り上げ返済額 (円)", min_value=0, value=0, step=100000, key='la_er_amt', help="一度に繰り上げ返済する金額です。")
    early_repayment_month_a = st.number_input(f"繰り上げ返済を行う月 (1-{loan_term_years_a * 12})",
                                              min_value=0, max_value=loan_term_years_a * 12, value=0, step=1, key='la_er_month', help="ローン開始から何ヶ月目に繰り上げ返済を行うか指定します。")
    early_repayments_a = []
    if early_repayment_amount_a > 0 and early_repayment_month_a > 0:
        early_repayments_a.append({'month': early_repayment_month_a, 'amount': early_repayment_amount_a})

    st.markdown("---")
    st.subheader("ローンAの金利変動 (変動金利の場合)")
    st.info("最大10回まで金利変更を追加できます。")

    # Display and get inputs for existing rate changes
    rate_changes_a_temp_inputs = []
    for i in range(st.session_state.num_rate_changes_a):
        st.write(f"金利変動 {i+1}")
        col_rc_a1, col_rc_a2 = st.columns(2)
        with col_rc_a1:
            month = st.number_input(f"変更月 (1-{loan_term_years_a * 12})", min_value=1, max_value=loan_term_years_a * 12, value=12*(i+1) if 12*(i+1) <= loan_term_years_a*12 else loan_term_years_a*12, step=1, key=f'la_rc_month_{i}')
        with col_rc_a2:
            rate = st.number_input(f"新金利 (%)", min_value=0.01, max_value=10.0, value=max(0.01, annual_interest_rate_a_initial - 0.1*(i+1)), step=0.01, key=f'la_rc_rate_{i}')
        rate_changes_a_temp_inputs.append({'month': month, 'new_rate': rate})
    st.session_state.rate_changes_a_inputs = rate_changes_a_temp_inputs # Update session state after inputs

    add_rc_a_button = st.button("ローンAの金利変動を追加", key='add_rc_a')
    if add_rc_a_button:
        if st.session_state.num_rate_changes_a < 10:
            st.session_state.num_rate_changes_a += 1
            # Add a default new input row. This will cause a rerun and show a new field.
            st.session_state.rate_changes_a_inputs.append({'month': 1, 'new_rate': annual_interest_rate_a_initial})
        else:
            st.warning("金利変動は最大10回まで追加できます。")

    reset_rc_a_button = st.button("ローンAの金利変動をリセット", key='reset_rc_a')
    if reset_rc_a_button:
        st.session_state.num_rate_changes_a = 0
        st.session_state.rate_changes_a_inputs = []

    st.markdown('</div>', unsafe_allow_html=True)


# Loan B Inputs
with col2:
    st.subheader("ローンBの条件")
    st.markdown('<div class="loan-section">', unsafe_allow_html=True)
    loan_amount_b = st.number_input("ローンBの借入希望額 (円)", min_value=1000000, max_value=500000000, value=30000000, step=100000, key='lb_amt')
    down_payment_b = st.number_input("ローンBの頭金 (円)", min_value=0, max_value=loan_amount_b, value=0, step=100000, key='lb_dp')
    loan_term_years_b = st.slider("ローンBの返済期間 (年)", min_value=1, max_value=50, value=30, step=1, key='lb_term')
    annual_interest_rate_b_initial = st.slider("ローンBの初期年利 (%)", min_value=0.1, max_value=10.0, value=1.8, step=0.01, key='lb_rate_init')
    repayment_type_b = st.radio("ローンBの返済方法", ["元利均等返済", "元金均等返済"], key='lb_type', help="元利均等返済は毎月の支払い額が一定、元金均等返済は元金部分が一定で支払い額が徐々に減少します。")

    st.markdown("---")
    st.subheader("ローンBの繰り上げ返済")
    early_repayment_amount_b = st.number_input("繰り上げ返済額 (円)", min_value=0, value=0, step=100000, key='lb_er_amt', help="一度に繰り上げ返済する金額です。")
    early_repayment_month_b = st.number_input(f"繰り上げ返済を行う月 (1-{loan_term_years_b * 12})",
                                              min_value=0, max_value=loan_term_years_b * 12, value=0, step=1, key='lb_er_month', help="ローン開始から何ヶ月目に繰り上げ返済を行うか指定します。")
    early_repayments_b = []
    if early_repayment_amount_b > 0 and early_repayment_month_b > 0:
        early_repayments_b.append({'month': early_repayment_month_b, 'amount': early_repayment_amount_b})

    st.markdown("---")
    st.subheader("ローンBの金利変動 (変動金利の場合)")
    st.info("最大10回まで金利変更を追加できます。")

    # Display and get inputs for existing rate changes
    rate_changes_b_temp_inputs = []
    for i in range(st.session_state.num_rate_changes_b):
        st.write(f"金利変動 {i+1}")
        col_rc_b1, col_rc_b2 = st.columns(2)
        with col_rc_b1:
            month = st.number_input(f"変更月 (1-{loan_term_years_b * 12})", min_value=1, max_value=loan_term_years_b * 12, value=12*(i+1) if 12*(i+1) <= loan_term_years_b*12 else loan_term_years_b*12, step=1, key=f'lb_rc_month_{i}')
        with col_rc_b2:
            rate = st.number_input(f"新金利 (%)", min_value=0.01, max_value=10.0, value=max(0.01, annual_interest_rate_b_initial - 0.1*(i+1)), step=0.01, key=f'lb_rc_rate_{i}')
        rate_changes_b_temp_inputs.append({'month': month, 'new_rate': rate})
    st.session_state.rate_changes_b_inputs = rate_changes_b_temp_inputs # Update session state after inputs

    add_rc_b_button = st.button("ローンBの金利変動を追加", key='add_rc_b')
    if add_rc_b_button:
        if st.session_state.num_rate_changes_b < 10:
            st.session_state.num_rate_changes_b += 1
            # Add a default new input row. This will cause a rerun and show a new field.
            st.session_state.rate_changes_b_inputs.append({'month': 1, 'new_rate': annual_interest_rate_b_initial})
        else:
            st.warning("金利変動は最大10回まで追加できます。")

    reset_rc_b_button = st.button("ローンBの金利変動をリセット", key='reset_rc_b')
    if reset_rc_b_button:
        st.session_state.num_rate_changes_b = 0
        st.session_state.rate_changes_b_inputs = []

    st.markdown('</div>', unsafe_allow_html=True)


# --- Calculation and Results Display ---
st.header("計算結果")
results_col1, results_col2 = st.columns(2)

# Calculate Loan A
with results_col1:
    st.subheader("ローンAの計算結果")
    if loan_amount_a - down_payment_a <= 0:
        st.error("ローンAの借入希望額が頭金以下です。")
        monthly_payment_a, total_payment_a = 0, 0
    else:
        monthly_payment_a, total_payment_a, final_balance_a = calculate_loan(
            loan_amount_a, annual_interest_rate_a_initial, loan_term_years_a, repayment_type_a, down_payment_a,
            early_repayments_a, st.session_state.rate_changes_a_inputs
        )
        st.markdown(f'<div class="metric-card"><h3>最初の月々の支払い額</h3><p>¥ {int(monthly_payment_a):,}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><h3>総支払額</h3><p>¥ {int(total_payment_a):,}</p></div>', unsafe_allow_html=True)
        if final_balance_a > 0:
            st.warning(f"注: ローンAの残高が残っています: ¥ {int(final_balance_a):,}")

# Calculate Loan B
with results_col2:
    st.subheader("ローンBの計算結果")
    if loan_amount_b - down_payment_b <= 0:
        st.error("ローンBの借入希望額が頭金以下です。")
        monthly_payment_b, total_payment_b = 0, 0
    else:
        monthly_payment_b, total_payment_b, final_balance_b = calculate_loan(
            loan_amount_b, annual_interest_rate_b_initial, loan_term_years_b, repayment_type_b, down_payment_b,
            early_repayments_b, st.session_state.rate_changes_b_inputs
        )
        st.markdown(f'<div class="metric-card"><h3>最初の月々の支払い額</h3><p>¥ {int(monthly_payment_b):,}</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><h3>総支払額</h3><p>¥ {int(total_payment_b):,}</p></div>', unsafe_allow_html=True)
        if final_balance_b > 0:
            st.warning(f"注: ローンBの残高が残っています: ¥ {int(final_balance_b):,}")

# --- Comparison Result ---
st.header("比較")
# 比較のために両方のローンが有効な計算値を持つことを確認
valid_loan_a_calc = (loan_amount_a - down_payment_a > 0) and (total_payment_a > 0)
valid_loan_b_calc = (loan_amount_b - down_payment_b > 0) and (total_payment_b > 0)

if valid_loan_a_calc and valid_loan_b_calc:
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
