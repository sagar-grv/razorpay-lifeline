import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

st.set_page_config(page_title="Project Lifeline - Dashboard", page_icon="🚑", layout="wide")

st.title("🚑 Project Lifeline: Autonomous Revenue Recovery")
st.markdown("Real-time Closed-Loop Payment Recovery Pipeline, Compliance Stopping Rules & Audit Trail")

# Fetch data from PostgreSQL
df_payments = pd.read_sql("SELECT * FROM failed_payments ORDER BY created_at DESC", engine)
df_logs = pd.read_sql("SELECT * FROM recovery_audit_logs ORDER BY created_at DESC", engine)

# Check model mode
groq_key = os.getenv("GROQ_API_KEY", "")
if not groq_key or groq_key.startswith("gsk_test"):
    model_status = "MOCK MODE (live Llama 3 pending key)"
    model_delta = "Simulated Reasoning"
else:
    model_status = "llama3-70b-8192 (LIVE)"
    model_delta = "Live Groq Inference"

if df_payments.empty:
    st.info("No failed payments yet. Run `python batch_tester.py` in your terminal to simulate data!")
else:
    # Closed-loop calculations
    total_failed_amount = df_payments['amount'].sum() / 100
    total_txns = len(df_payments)

    recovered_df = df_payments[df_payments['final_status'] == 'RECOVERED']
    recovered_amount = recovered_df['amount'].sum() / 100
    recovered_count = len(recovered_df)

    lost_df = df_payments[df_payments['final_status'] == 'LOST']
    lost_amount = lost_df['amount'].sum() / 100
    lost_count = len(lost_df)

    escalated_df = df_payments[df_payments['final_status'] == 'ESCALATED']
    escalated_amount = escalated_df['amount'].sum() / 100
    escalated_count = len(escalated_df)

    pending_df = df_payments[df_payments['final_status'] == 'PENDING']
    pending_amount = pending_df['amount'].sum() / 100
    pending_count = len(pending_df)

    recovery_rate = (recovered_amount / total_failed_amount * 100) if total_failed_amount > 0 else 0

    # Top KPI Metrics Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Failed Revenue", f"₹{total_failed_amount:,.2f}", delta=f"{total_txns} Failed Txns", delta_color="inverse")
    col2.metric("AI Recovered Revenue", f"₹{recovered_amount:,.2f}", delta=f"{recovered_count} Recovered")
    col3.metric("Lost Revenue", f"₹{lost_amount:,.2f}", delta=f"{lost_count} Lost", delta_color="inverse")
    col4.metric("Real Recovery Rate", f"{recovery_rate:.1f}%", delta="Honest Closed-Loop")
    col5.metric("Active AI Model", model_status, delta=model_delta)

    st.divider()

    # Baseline Comparison Section
    st.subheader("📈 Industry Baseline vs. Project Lifeline Lift")
    BASELINE_RECOVERY = 0.22
    baseline_recovered_amount = total_failed_amount * BASELINE_RECOVERY
    incremental_lift = recovered_amount - baseline_recovered_amount
    lift_percentage = ((recovered_amount - baseline_recovered_amount) / baseline_recovered_amount * 100) if baseline_recovered_amount > 0 else 0

    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    b_col1.metric("Blind Retry Baseline (22%)", f"₹{baseline_recovered_amount:,.2f}", help="Standard industry benchmark without intelligent routing")
    b_col2.metric("Lifeline Smart Recovery", f"₹{recovered_amount:,.2f}", delta=f"+₹{incremental_lift:,.2f} Extra Saved")
    b_col3.metric("Net Lift Over Baseline", f"+{lift_percentage:.1f}%", delta="Measurable ROI")
    b_col4.metric("Opt-Out Compliance Halts", f"{escalated_count} Users", delta="Stopping Rules Enforced", delta_color="off")

    st.info(f"💡 **Benchmark Comparison**: Blind retry would recover **₹{baseline_recovered_amount:,.2f}** — Lifeline recovered **₹{recovered_amount:,.2f}** (**+{lift_percentage:.1f}% lift** over standard retries).")

    st.divider()

    # Visual Charts
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📊 Closed-Loop Recovery Outcomes")
        status_counts = df_payments['final_status'].value_counts()
        st.bar_chart(status_counts)
    
    with col_chart2:
        st.subheader("⚡ Inbound User Replies & Intent")
        if 'user_reply_intent' in df_payments.columns and not df_payments['user_reply_intent'].dropna().empty:
            intent_counts = df_payments['user_reply_intent'].value_counts()
            st.bar_chart(intent_counts)
        else:
            reason_counts = df_payments['failure_reason'].value_counts()
            st.bar_chart(reason_counts)

    st.divider()

    # The Audit Trail
    st.subheader("📜 The Audit Trail (Every AI Decision, Payment Link, User Reply & Compliance Action)")
    df_merged = pd.merge(df_logs, df_payments, left_on='payment_id', right_on='razorpay_payment_id', how='left')
    
    display_cols = [c for c in ['payment_id', 'amount', 'failure_reason', 'user_phone', 'user_reply', 'user_reply_intent', 'ai_model_used', 'ai_reasoning', 'action_taken', 'execution_status', 'final_status', 'created_at_x'] if c in df_merged.columns]
    st.dataframe(df_merged[display_cols], use_container_width=True)
