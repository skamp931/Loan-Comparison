import streamlit as st
import math
import pandas as pd
import altair as alt

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
        margin-bottom: 10px; /* Slightly reduced margin for compactness */
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
    /* Specific styling for delete buttons to make them smaller */
    .stButton button[key*='delete_la_rc_'],
    .stButton button[key*='delete_lb_rc_'] {
        padding: 5px 8px; /* Smaller padding */
        font-size: 0.8em; /* Smaller font size */
        border-radius: 5px;
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
        border: 0.5px solid #e0e0e0; /* Changed from 1px to 0.5px */
        border-radius: 10px;
        padding: 15px; /* Reduced padding for thinner appearance */
        margin-bottom: 30px;
        box_shadow: 0 2px 5px rgba(0,0,0,0.08);
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
        color: white; /* Changed to white for black background */
        margin-bottom: 15px;
        border-bottom: 1px solid #ccc;
        padding-bottom: 10px;
        font-weight: bold; /* Make text bold */
        background-color: #2c3e50; /* Darker shade, close to black but still readable */
        padding: 10px; /* Add padding to the header for the background */
        border-radius: 5px; /* Add some rounded corners */
        text-align: center; /* Center the text in the header */
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
        loan_amount (int): 借入希望額 (円)
        annual_interest_rate (float): 年利 (%)
        loan_term_years (int): 返済期間 (年)
        repayment_type (str): 返済方法 ("元利均等返済" or "元金均等返S")
        down_payment (int): 頭金 (円)
        early_repayments (list): 繰り上げ返済のリスト [(月, 金額), ...]
        rate_changes (list): 金利変更のリスト [(月, 新年利), ...]

    Returns:
        tuple: (最初の月々の支払い額, 総支払額, 最終残高, 残高推移リスト, 年間支払額リスト)
    """
    principal = loan_amount - down_payment
    if principal <= 0:
        return 0, 0, 0, [], [] # 頭金がローン額以上の場合

    number_of_payments_total = loan_term_years * 12

    current_principal = principal
    total_payment = 0
    first_month_payment = 0 # 最初の月々の支払い額を格納
    payments_made = 0
    balance_history = [] # 残高推移を保存
    annual_payments = {} # 年間支払額を保存

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
        # 現在の年を計算（1ヶ月目が1年目の開始）
        current_year = math.ceil(month / 12)

        if current_principal <= 0: # ローンが完済された場合
            # 残りの期間も履歴を追加 (残高0として)
            for remaining_month in range(month, int(number_of_payments_total) + 1):
                balance_history.append({'month': remaining_month, 'balance': 0})
                # 完済後は年間支払い額には追加しない
            break

        # 金利変更の適用
        for rc in rate_changes_sorted:
            if month == rc['month']:
                current_annual_rate = rc['new_rate']
                current_monthly_rate = current_annual_rate / 100 / 12

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
                    monthly_payment = current_principal / remaining_payments
                except OverflowError:
                    st.error("計算中にオーバーフローエラーが発生しました。期間または金利を見直してください。")
                    return 0, 0, current_principal, [], []

            interest_component = current_principal * current_monthly_rate
            principal_component = monthly_payment - interest_component

            if principal_component < 0:
                principal_component = 0
            if principal_component > current_principal:
                principal_component = current_principal
                monthly_payment = current_principal + interest_component

        elif repayment_type == "元金均等返済":
            # 月々の元金返済額は固定（初期借入元金に対して計算）
            monthly_principal_payment = principal / number_of_payments_total
            interest_component = current_principal * current_monthly_rate
            monthly_payment = monthly_principal_payment + interest_component

            principal_component = monthly_principal_payment

            # 最終支払い額で元金が残らないように調整
            if principal_component > current_principal:
                 principal_component = current_principal
                 monthly_payment = current_principal + interest_component

        # 年間支払額に加算
        annual_payments[current_year] = annual_payments.get(current_year, 0) + monthly_payment

        total_payment += monthly_payment
        current_principal -= principal_component
        payments_made += 1

        if month == 1:
            first_month_payment = monthly_payment

        # 繰り上げ返済の適用
        for er_idx, er in enumerate(early_repayments_sorted):
            if month == er['month'] and er['amount'] > 0:
                current_principal -= er['amount']
                early_repayments_sorted[er_idx]['amount'] = 0

                if current_principal <= 0:
                    break

        balance_history.append({'month': month, 'balance': max(0, current_principal)})


    # シミュレーション期間が終わる前に完済した場合、残りの期間は残高0とする
    while len(balance_history) < number_of_payments_total:
        balance_history.append({'month': len(balance_history) + 1, 'balance': 0})

    # 年間支払額をリスト形式に変換
    annual_payments_list = [{'year': year, 'total_payment': amount} for year, amount in annual_payments.items()]
    annual_payments_list = sorted(annual_payments_list, key=lambda x: x['year'])

    return first_month_payment, total_payment, max(0, current_principal), balance_history, annual_payments_list

# --- Sidebar Content ---
with st.sidebar:
    # --- シミュレーションに使った数式 ---
    st.markdown('<div class="sidebar-header">シミュレーションに使った数式</div>', unsafe_allow_html=True)
    formulas_data = [
        {
            "q": "元利均等返済 (Equal Principal and Interest Repayment)",
            "a": r"""
            月々の支払い額 $M$:
            $M = P \left[ \frac{r(1+r)^n}{(1+r)^n - 1} \right]$

            ここで、
            - $P$: 借入元金
            - $r$: 月利 (年利 / 1200)
            - $n$: 返済回数 (返済期間(年) $\times$ 12)
            """
        },
        {
            "q": "元金均等返済 (Principal Equal Repayment)",
            "a": r"""
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
            """
        }
    ]
    for i, formula in enumerate(formulas_data):
        with st.expander(f"Q{i+1}. {formula['q']}"):
            st.markdown(formula['a'])
    st.markdown("※繰り上げ返済や金利変動は、上記数式に基づいて毎月再計算されます。")
    st.markdown("---")


    # --- よくある質問 (Q&A) ---
    st.markdown('<div class="sidebar-header">よくある質問 (Q&A)</div>', unsafe_allow_html=True)
    qa_data = [
        {
            "q": "「ローン残高が残っています。」と表示されるのはなぜですか？",
            "a": """
            このメッセージは、設定した返済期間（年数）と月々の返済額では、ローンが完済されずにシミュレーション期間が終了してしまう場合に表示されます。
            例えば、返済期間が**35年**と設定されている場合、35年が経過した時点（ローン終了時）でまだ残高があることを示します。

            考えられる理由としては、以下の点が挙げられます。

            * **繰り上げ返済額が不足している:** 繰り上げ返済を行ったにもかかわらず、返済期間短縮や総支払額の減少効果が期待通りに現れていない場合。
            * **返済期間が短い:** 設定した返済期間（年数）が、借入額に対して短すぎる場合。
            * **金利が高い:** 金利が高く、月々の利息負担が大きくなっている場合。
            * **初期借入額や頭金が不適切:** 借入額に対して頭金が少なすぎるか、初期借入額が大きすぎる場合。

            これらの条件を見直すことで、ローンが完済されるように調整することができます。
            """
        },
    ]

    for i, qa in enumerate(qa_data):
        with st.expander(f"Q{i+1}. {qa['q']}"):
            st.write(qa['a'])

st.markdown("---")


# --- Loan Input Sections ---
col1, col2 = st.columns(2)

# Session state initialization for dynamic rate changes
# Initialize rate_changes_a_inputs if it doesn't exist
if 'rate_changes_a_inputs' not in st.session_state:
    st.session_state.rate_changes_a_inputs = []

# Initialize rate_changes_b_inputs if it doesn't exist
if 'rate_changes_b_inputs' not in st.session_state:
    st.session_state.rate_changes_b_inputs = []

# Loan A Inputs
with col1:
    st.subheader("ローンAの条件")
    st.markdown('<div class="loan-section">', unsafe_allow_html=True)
    # 借入希望額を万円単位で入力
    loan_amount_a_man = st.number_input("ローンAの借入希望額 (万円)", min_value=100, max_value=50000, value=3000, step=100, key='la_amt_man')
    loan_amount_a = loan_amount_a_man * 10000 # 内部計算用に円に戻す

    down_payment_a = st.number_input("ローンAの頭金 (円)", min_value=0, max_value=loan_amount_a, value=0, step=100000, key='la_dp')
    loan_term_years_a = st.slider("ローンAの返済期間 (年)", min_value=1, max_value=50, value=35, step=1, key='la_term')
    annual_interest_rate_a_initial = st.slider("ローンAの初期年利 (%)", min_value=0.1, max_value=10.0, value=1.5, step=0.01, key='la_rate_init')
    repayment_type_a = st.radio("ローンAの返済方法", ["元利均等返済", "元金均等返済"], key='la_type', help="元利均等返済は毎月の支払い額が一定、元金均等返済は元金部分が一定で支払い額が徐々に減少します。")

    st.markdown("---")
    st.subheader("ローンAの繰り上げ返済")
    # 繰り上げ返済額を万円単位で入力
    early_repayment_amount_a_man = st.number_input("繰り上げ返済額 (万円)", min_value=0, value=0, step=10, key='la_er_amt_man', help="一度に繰り上げ返済する金額です。")
    early_repayment_amount_a = early_repayment_amount_a_man * 10000 # 内部計算用に円に戻す

    early_repayment_month_a = st.number_input(f"繰り上げ返済を行う月 (1-{loan_term_years_a * 12})",
                                              min_value=0, max_value=loan_term_years_a * 12, value=0, step=1, key='la_er_month', help="ローン開始から何ヶ月目に繰り上げ返済を行うか指定します。")
    early_repayments_a = []
    if early_repayment_amount_a > 0 and early_repayment_month_a > 0:
        early_repayments_a.append({'month': early_repayment_month_a, 'amount': early_repayment_amount_a})

    st.markdown("---")
    st.subheader("ローンAの金利変動 (変動金利の場合)")
    st.info("最大10回まで金利変更を追加できます。")

    # Display and get inputs for existing rate changes
    # Use a temporary list to collect current inputs
    current_rate_changes_a_inputs = []
    delete_index_a = -1

    for i, rc in enumerate(st.session_state.rate_changes_a_inputs):
        st.write(f"金利変動 {i+1}")
        # Adjust column widths for smaller delete button (e.g., 0.49, 0.49, 0.02)
        col_rc_a1, col_rc_a2, col_rc_a3 = st.columns([0.48, 0.48, 0.04]) # Adjusted column widths
        with col_rc_a1:
            month = st.number_input(f"変更月 (1-{loan_term_years_a * 12})", min_value=1, max_value=loan_term_years_a * 12, value=rc['month'], step=1, key=f'la_rc_month_{i}')
        with col_rc_a2:
            rate = st.number_input(f"新金利 (%)", min_value=0.01, max_value=10.0, value=rc['new_rate'], step=0.01, key=f'la_rc_rate_{i}')
        with col_rc_a3:
            # Use st.button directly without extra div for alignment if possible, rely on column sizing
            if st.button("削除", key=f'delete_la_rc_{i}'):
                delete_index_a = i
        current_rate_changes_a_inputs.append({'month': month, 'new_rate': rate})

    # Update session state after all inputs are collected
    st.session_state.rate_changes_a_inputs = current_rate_changes_a_inputs

    # Apply deletion after the loop
    if delete_index_a != -1:
        del st.session_state.rate_changes_a_inputs[delete_index_a]
        st.rerun() # Rerun to reflect the deletion immediately

    add_rc_a_button = st.button("ローンAの金利変動を追加", key='add_rc_a')
    if add_rc_a_button:
        if len(st.session_state.rate_changes_a_inputs) < 10:
            st.session_state.rate_changes_a_inputs.append({'month': 1, 'new_rate': annual_interest_rate_a_initial})
            st.rerun() # Rerun to show new input immediately
        else:
            st.warning("金利変動は最大10回まで追加できます。")

    reset_rc_a_button = st.button("ローンAの金利変動をリセット", key='reset_rc_a')
    if reset_rc_a_button:
        st.session_state.rate_changes_a_inputs = []
        st.rerun() # Rerun to clear inputs immediately

    st.markdown('</div>', unsafe_allow_html=True)


# Loan B Inputs
with col2:
    st.subheader("ローンBの条件")
    st.markdown('<div class="loan-section">', unsafe_allow_html=True)
    # 借入希望額を万円単位で入力
    loan_amount_b_man = st.number_input("ローンBの借入希望額 (万円)", min_value=100, max_value=50000, value=3000, step=100, key='lb_amt_man')
    loan_amount_b = loan_amount_b_man * 10000 # 内部計算用に円に戻す

    down_payment_b = st.number_input("ローンBの頭金 (円)", min_value=0, max_value=loan_amount_b, value=0, step=100000, key='lb_dp')
    loan_term_years_b = st.slider("ローンBの返済期間 (年)", min_value=1, max_value=50, value=30, step=1, key='lb_term')
    annual_interest_rate_b_initial = st.slider("ローンBの初期年利 (%)", min_value=0.1, max_value=10.0, value=1.8, step=0.01, key='lb_rate_init')
    repayment_type_b = st.radio("ローンBの返済方法", ["元利均等返済", "元金均等返済"], key='lb_type', help="元利均等返済は毎月の支払い額が一定、元金均等返済は元金部分が一定で支払い額が徐々に減少します。")

    st.markdown("---")
    st.subheader("ローンBの繰り上げ返済")
    # 繰り上げ返済額を万円単位で入力
    early_repayment_amount_b_man = st.number_input("繰り上げ返済額 (万円)", min_value=0, value=0, step=10, key='lb_er_amt_man', help="一度に繰り上げ返済する金額です。")
    early_repayment_amount_b = early_repayment_amount_b_man * 10000 # 内部計算用に円に戻す

    early_repayment_month_b = st.number_input(f"繰り上げ返済を行う月 (1-{loan_term_years_b * 12})",
                                              min_value=0, max_value=loan_term_years_b * 12, value=0, step=1, key='lb_er_month', help="ローン開始から何ヶ月目に繰り上げ返済を行うか指定します。")
    early_repayments_b = []
    if early_repayment_amount_b > 0 and early_repayment_month_b > 0:
        early_repayments_b.append({'month': early_repayment_month_b, 'amount': early_repayment_amount_b})

    st.markdown("---")
    st.subheader("ローンBの金利変動 (変動金利の場合)")
    st.info("最大10回まで金利変更を追加できます。")

    # Display and get inputs for existing rate changes
    current_rate_changes_b_inputs = []
    delete_index_b = -1

    for i, rc in enumerate(st.session_state.rate_changes_b_inputs):
        st.write(f"金利変動 {i+1}")
        # Adjust column widths for smaller delete button (e.g., 0.49, 0.49, 0.02)
        col_rc_b1, col_rc_b2, col_rc_b3 = st.columns([0.48, 0.48, 0.04]) # Adjusted column widths
        with col_rc_b1:
            month = st.number_input(f"変更月 (1-{loan_term_years_b * 12})", min_value=1, max_value=loan_term_years_b * 12, value=rc['month'], step=1, key=f'lb_rc_month_{i}')
        with col_rc_b2:
            rate = st.number_input(f"新金利 (%)", min_value=0.01, max_value=10.0, value=rc['new_rate'], step=0.01, key=f'lb_rc_rate_{i}')
        with col_rc_b3:
            # Use st.button directly without extra div for alignment if possible, rely on column sizing
            if st.button("削除", key=f'delete_lb_rc_{i}'):
                delete_index_b = i
        current_rate_changes_b_inputs.append({'month': month, 'new_rate': rate})

    # Update session state after all inputs are collected
    st.session_state.rate_changes_b_inputs = current_rate_changes_b_inputs

    # Apply deletion after the loop
    if delete_index_b != -1:
        del st.session_state.rate_changes_b_inputs[delete_index_b]
        st.rerun() # Rerun to reflect the deletion immediately

    add_rc_b_button = st.button("ローンBの金利変動を追加", key='add_rc_b')
    if add_rc_b_button:
        if len(st.session_state.rate_changes_b_inputs) < 10:
            st.session_state.rate_changes_b_inputs.append({'month': 1, 'new_rate': annual_interest_rate_b_initial})
            st.rerun() # Rerun to show new input immediately
        else:
            st.warning("金利変動は最大10回まで追加できます。")

    reset_rc_b_button = st.button("ローンBの金利変動をリセット", key='reset_rc_b')
    if reset_rc_b_button:
        st.session_state.rate_changes_b_inputs = []
        st.rerun() # Rerun to clear inputs immediately

    st.markdown('</div>', unsafe_allow_html=True)


# --- Calculation and Results Display ---
st.header("計算結果")
results_col1, results_col2 = st.columns(2)

# Calculate Loan A
with results_col1:
    st.subheader("ローンAの計算結果")
    if loan_amount_a - down_payment_a <= 0:
        st.error("ローンAの借入希望額が頭金以下です。")
        monthly_payment_a, total_payment_a, final_balance_a, balance_history_a, annual_payments_a = 0, 0, 0, [], []
    else:
        monthly_payment_a, total_payment_a, final_balance_a, balance_history_a, annual_payments_a = calculate_loan(
            loan_amount_a, annual_interest_rate_a_initial, loan_term_years_a, repayment_type_a, down_payment_a,
            early_repayments_a, st.session_state.rate_changes_a_inputs
        )
        st.markdown(f'<div class="metric-card"><h3>最初の月々の支払い額</h3><p>¥ {int(monthly_payment_a):,} (約{int(monthly_payment_a/10000):,}万円)</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><h3>総支払額</h3><p>¥ {int(total_payment_a):,} (約{int(total_payment_a/10000):,}万円)</p></div>', unsafe_allow_html=True)
        # Check if balance is significantly greater than 0
        if final_balance_a > 0.01: # Use a small threshold to avoid floating point issues
            st.warning(f"注: ローンAの残高が残っています: ¥ {int(final_balance_a):,}")

# Calculate Loan B
with results_col2:
    st.subheader("ローンBの計算結果")
    if loan_amount_b - down_payment_b <= 0:
        st.error("ローンBの借入希望額が頭金以下です。")
        monthly_payment_b, total_payment_b, final_balance_b, balance_history_b, annual_payments_b = 0, 0, 0, [], []
    else:
        monthly_payment_b, total_payment_b, final_balance_b, balance_history_b, annual_payments_b = calculate_loan(
            loan_amount_b, annual_interest_rate_b_initial, loan_term_years_b, repayment_type_b, down_payment_b,
            early_repayments_b, st.session_state.rate_changes_b_inputs
        )
        st.markdown(f'<div class="metric-card"><h3>最初の月々の支払い額</h3><p>¥ {int(monthly_payment_b):,} (約{int(monthly_payment_b/10000):,}万円)</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><h3>総支払額</h3><p>¥ {int(total_payment_b):,} (約{int(total_payment_b/10000):,}万円)</p></div>', unsafe_allow_html=True)
        # Check if balance is significantly greater than 0
        if final_balance_b > 0.01: # Use a small threshold to avoid floating point issues
            st.warning(f"注: ローンBの残高が残っています: ¥ {int(final_balance_b):,}")


# --- Comparison Result ---
st.header("比較")
# 比較のために両方のローンが有効な計算値を持つことを確認
valid_loan_a_calc = (loan_amount_a - down_payment_a > 0) and (total_payment_a > 0)
valid_loan_b_calc = (loan_amount_b - down_payment_b > 0) and (total_payment_b > 0)

if valid_loan_a_calc and valid_loan_b_calc:
    if total_payment_a < total_payment_b:
        st.markdown(f'<div class="comparison-result">ローンAの方が総支払額が**約 ¥ {int((total_payment_b - total_payment_a)/10000):,}万円**少なくなります。</div>', unsafe_allow_html=True)
    elif total_payment_b < total_payment_a:
        st.markdown(f'<div class="comparison-result">ローンBの方が総支払額が**約 ¥ {int((total_payment_a - total_payment_b)/10000):,}万円**少なくなります。</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="comparison-result warning">両ローンの総支払額はほぼ同じです。</div>', unsafe_allow_html=True)
else:
    st.info("比較を行うには、両方のローンで有効な借入額が必要です。")

st.markdown("---")

# --- Loan Balance Graph ---
st.header("ローン残高推移グラフ")

if (loan_amount_a - down_payment_a > 0) or (loan_amount_b - down_payment_b > 0):
    chart_data_balance = []

    # ローンAのデータを追加
    for item in balance_history_a:
        chart_data_balance.append({
            '年数': item['month'] / 12,
            '残高 (万円)': item['balance'] / 10000,
            'ローン': 'ローンA'
        })

    # ローンBのデータを追加
    for item in balance_history_b:
        chart_data_balance.append({
            '年数': item['month'] / 12,
            '残高 (万円)': item['balance'] / 10000,
            'ローン': 'ローンB'
        })

    df_chart_balance = pd.DataFrame(chart_data_balance)

    if not df_chart_balance.empty:
        chart_balance = alt.Chart(df_chart_balance).mark_line().encode(
            x=alt.X('年数', title='年数', axis=alt.Axis(format='d')), # Format as integer
            y=alt.Y('残高 (万円)', title='残高 (万円)'),
            color=alt.Color('ローン', title='ローン'),
            tooltip=[alt.Tooltip('年数', format='.0f'), alt.Tooltip('残高 (万円)', format='.1f'), 'ローン']
        ).properties(
            title='ローン残高の推移'
        ).interactive() # インタラクティブなグラフにする

        st.altair_chart(chart_balance, use_container_width=True)
    else:
        st.warning("残高グラフを表示するには、少なくとも1つのローンで有効な借入額が必要です。")
else:
    st.info("残高グラフを表示するには、両方のローンで有効な借入額が必要です。")

st.markdown("---")

# --- Annual Payment Sum Graph ---
st.header("年間支払額推移グラフ")

if (loan_amount_a - down_payment_a > 0) or (loan_amount_b - down_payment_b > 0):
    chart_data_annual = []

    # ローンAのデータを追加
    for item in annual_payments_a:
        chart_data_annual.append({
            '年数': item['year'],
            '年間支払額 (万円)': item['total_payment'] / 10000,
            'ローン': 'ローンA'
        })

    # ローンBのデータを追加
    for item in annual_payments_b:
        chart_data_annual.append({
            '年数': item['year'],
            '年間支払額 (万円)': item['total_payment'] / 10000,
            'ローン': 'ローンB'
        })

    df_chart_annual = pd.DataFrame(chart_data_annual)

    if not df_chart_annual.empty:
        chart_annual = alt.Chart(df_chart_annual).mark_line().encode( # mark_barからmark_lineへ
            x=alt.X('年数', title='年数', axis=alt.Axis(format='d')), # :O から :Q を意識した記述へ
            y=alt.Y('年間支払額 (万円)', title='年間支払額 (万円)'),
            color=alt.Color('ローン', title='ローン'),
            tooltip=[alt.Tooltip('年数', format='.0f'), alt.Tooltip('年間支払額 (万円)', format='.1f'), 'ローン']
        ).properties(
            title='年間支払額の推移'
        ).interactive() # インタラクティブなグラフにする

        st.altair_chart(chart_annual, use_container_width=True)
    else:
        st.warning("年間支払額グラフを表示するには、少なくとも1つのローンで有効な借入額が必要です。")
else:
    st.info("年間支払額グラフを表示するには、両方のローンで有効な借入額が必要です。")


st.markdown("---")
st.markdown("このアプリは概算計算を提供します。実際のローン条件は金融機関にご確認ください。")
