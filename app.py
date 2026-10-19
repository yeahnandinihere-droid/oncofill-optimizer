import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from src.config import DRUG_CATALOG
from src.core.knapsack_solver import solve_pooled_batch
from src.core.sterility_tracker import generate_compounding_schedule

# Page Configuration
st.set_page_config(
    page_title="OncoFill-Optimizer | Cleanroom Vial Optimizer",
    page_icon="🧪",
    layout="wide"
)

# App Title & Subtitle
st.title("🧪 OncoFill-Optimizer")
st.markdown("### Automated Antineoplastic Vial Sharing & Cleanroom Compounding Engine")
st.caption("Minimizing discarded mAb volume under USP <797> and NABH sterility guidelines.")

# --- SIDEBAR: COMPOUNDING & DRUG CONTROLS ---
with st.sidebar:
    st.header("⚙️ Compounding Settings")
    selected_drug = st.selectbox("Select Antineoplastic Agent", list(DRUG_CATALOG.keys()))
    use_cstd = st.toggle("Equipped with CSTD (Closed-System Transfer Device)", value=True)
    
    drug_meta = DRUG_CATALOG[selected_drug]
    max_shelf_hrs = drug_meta["stability_hours_cstd"] if use_cstd else drug_meta["stability_hours_punctured"]
    
    st.info(
        f"**Target Molecule:** {selected_drug}\n\n"
        f"**Available Vials:** {', '.join(f'{v} mg' for v in drug_meta['vial_options_mg'])}\n\n"
        f"**USP <797> Sterility Window:** {max_shelf_hrs} hours under ISO Class 5 Hood"
    )
    st.divider()
    
    st.markdown("### Cohort Input Selection")
    input_mode = st.radio(
        "Choose Data Source:",
        ["Pre-loaded Clinical Cohort", "Manual / Custom Entry"],
        index=0
    )

# --- COHORT DATA INITIALIZATION ---
default_cohorts = {
    "Pembrolizumab (Keytruda)": [
        {"Patient ID": "PT-101", "Weight (kg)": 68.0, "dose_mg": 140.0},
        {"Patient ID": "PT-102", "Weight (kg)": 52.0, "dose_mg": 105.0},
        {"Patient ID": "PT-103", "Weight (kg)": 75.0, "dose_mg": 150.0},
        {"Patient ID": "PT-104", "Weight (kg)": 60.0, "dose_mg": 120.0},
        {"Patient ID": "PT-105", "Weight (kg)": 82.0, "dose_mg": 165.0},
    ],
    "Nivolumab (Opdivo)": [
        {"Patient ID": "PT-201", "Weight (kg)": 70.0, "dose_mg": 210.0},
        {"Patient ID": "PT-202", "Weight (kg)": 55.0, "dose_mg": 165.0},
        {"Patient ID": "PT-203", "Weight (kg)": 80.0, "dose_mg": 240.0},
    ],
    "Trastuzumab (Herceptin)": [
        {"Patient ID": "PT-301", "Weight (kg)": 62.0, "dose_mg": 372.0},
        {"Patient ID": "PT-302", "Weight (kg)": 74.0, "dose_mg": 444.0},
        {"Patient ID": "PT-303", "Weight (kg)": 50.0, "dose_mg": 300.0},
    ],
    "Rituximab (MabThera)": [
        {"Patient ID": "PT-401", "Weight (kg)": 65.0, "dose_mg": 600.0},
        {"Patient ID": "PT-402", "Weight (kg)": 78.0, "dose_mg": 675.0},
        {"Patient ID": "PT-403", "Weight (kg)": 58.0, "dose_mg": 560.0},
    ]
}

if input_mode == "Pre-loaded Clinical Cohort":
    base_data = default_cohorts.get(selected_drug, default_cohorts["Pembrolizumab (Keytruda)"])
    st.info("💡 **Pre-loaded Mode Active:** Showing verified clinical day-care orders. You can still tweak numbers in the table below.")
else:
    base_data = [
        {"Patient ID": "PT-CUSTOM-01", "Weight (kg)": 65.0, "dose_mg": 130.0},
        {"Patient ID": "PT-CUSTOM-02", "Weight (kg)": 55.0, "dose_mg": 70.0},
        {"Patient ID": "PT-CUSTOM-03", "Weight (kg)": 72.0, "dose_mg": 140.0},
    ]
    st.info("✍️ **Manual Entry Mode Active:** Add, delete, or change rows directly in the table below.")

# --- INTERACTIVE DATA EDITOR ---
col_table, col_summary = st.columns([3, 2])

with col_table:
    st.subheader("📋 Inpatient / Day-Care Infusion Queue")
    edited_df = st.data_editor(
        pd.DataFrame(base_data),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Patient ID": st.column_config.TextColumn("Patient Identifier", required=True),
            "Weight (kg)": st.column_config.NumberColumn("Weight (kg)", min_value=20.0, max_value=200.0, step=0.5),
            "dose_mg": st.column_config.NumberColumn("Prescribed Dose (mg)", min_value=1.0, max_value=5000.0, step=1.0, required=True),
        }
    )

# Filter out empty or zero rows
valid_records = [
    r for r in edited_df.to_dict(orient="records")
    if pd.notna(r.get("dose_mg")) and r.get("dose_mg", 0) > 0
]

with col_summary:
    st.subheader("💊 Formulation Demand")
    total_mg_demand = sum(r["dose_mg"] for r in valid_records)
    st.metric("Total Prescribed Dose", f"{total_mg_demand:,.1f} mg")
    st.metric("Active Infusions Scheduled", f"{len(valid_records)} Patients")
    st.metric("Cleanroom Stability Window", f"{max_shelf_hrs} Hours")

# --- GUARD: EMPTY QUEUE ---
if len(valid_records) == 0:
    st.warning("⚠️ Please enter at least one patient record with a valid prescribed dose (mg) to run the solver.")
    st.stop()

# --- RUN SOLVER ---
results = solve_pooled_batch(selected_drug, valid_records, use_cstd=use_cstd)

st.markdown("---")

# --- RESULTS & KPIS ---
st.subheader("📊 Financial & Drug Wastage Arbitrage")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Unpooled Procurement Cost", f"₹{results['baseline']['cost_inr']:,.0f}")
kpi2.metric("Optimized Batch Cost", f"₹{results['optimized']['cost_inr']:,.0f}")
kpi3.metric(
    "Net Daily Cost Savings",
    f"₹{results['delta']['savings_inr']:,.0f}",
    f"{results['delta']['savings_pct']}% Saved"
)
kpi4.metric(
    "Residual Wasted Drug",
    f"{results['optimized']['waste_mg']:.1f} mg",
    f"-{results['delta']['waste_eliminated_mg']:.1f} mg Eliminated",
    delta_color="inverse"
)

# --- VISUALIZATION & COMPOUNDING SCHEDULE ---
col_chart, col_schedule = st.columns([3, 2])

with col_chart:
    st.subheader("Comparative Procurement vs Discard")
    fig = go.Figure()
    
    # Baseline Bar
    fig.add_trace(go.Bar(
        name="Current Standard Practice (Isolated)",
        x=["Total Cost (₹)", "Discarded Drug (mg)"],
        y=[results["baseline"]["cost_inr"], results["baseline"]["waste_mg"]],
        marker_color="#ef4444",
        text=[f"₹{results['baseline']['cost_inr']:,.0f}", f"{results['baseline']['waste_mg']:.1f} mg"],
        textposition="auto"
    ))
    
    # Optimized Bar
    fig.add_trace(go.Bar(
        name="OncoFill-Optimized (Cleanroom Pooled)",
        x=["Total Cost (₹)", "Discarded Drug (mg)"],
        y=[results["optimized"]["cost_inr"], results["optimized"]["waste_mg"]],
        marker_color="#10b981",
        text=[f"₹{results['optimized']['cost_inr']:,.0f}", f"{results['optimized']['waste_mg']:.1f} mg"],
        textposition="auto"
    ))
    
    fig.update_layout(
        barmode="group",
        template="plotly_white",
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_schedule:
    st.subheader("⏱️ Cleanroom Protocol Schedule")
    schedule = generate_compounding_schedule(results, datetime.now())
    for item in schedule:
        with st.container():
            st.markdown(f"**`{item['timestamp']}` — {item['action']}**")
            st.caption(item["detail"])

# --- CLEANROOM DISPENSING ORDER ---
st.subheader("📑 Cleanroom Pharmacist Dispense Queue")
vial_details = ", ".join(
    [f"**{cnt}x {size} mg**" for size, cnt in results["optimized"]["vials"].items() if cnt > 0]
)
st.success(
    f"**Laminar Flow Hood Instruction:** Open exactly {sum(results['optimized']['vials'].values())} vial(s): "
    f"{vial_details}. Total drug available: **{sum(s * c for s, c in results['optimized']['vials'].items())} mg** "
    f"for **{results['total_prescribed_mg']} mg** prescribed demand across **{results['patient_count']} patients**."
)