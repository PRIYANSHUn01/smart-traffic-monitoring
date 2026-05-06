# dashboard/app.py  —  Streamlit real-time dashboard
# Run with: streamlit run dashboard/app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
import sys
import time
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, CSV_LOG_PATH, DASHBOARD_TITLE, SNAPSHOTS_DIR
from utils.database import TrafficDB

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=DASHBOARD_TITLE,
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #185FA5;
        margin-bottom: 12px;
    }
    .violation-card {
        background: #fff5f5;
        border-radius: 8px;
        padding: 10px;
        border-left: 4px solid #E24B4A;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .header-title { font-size: 26px; font-weight: 600; }
    .section-title { font-size: 15px; font-weight: 500; color: #555; margin: 16px 0 8px; }
</style>
""", unsafe_allow_html=True)


# ── Database helper ───────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    return TrafficDB()

def load_violations_df():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM violations ORDER BY id DESC LIMIT 200",
        conn
    )
    conn.close()
    return df

def load_vehicle_counts_df():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM vehicle_counts ORDER BY id DESC LIMIT 1000",
        conn
    )
    conn.close()
    return df


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=TrafficAI", width=200)
    st.markdown("### Settings")

    auto_refresh = st.checkbox("Auto refresh (3s)", value=True)
    show_snapshots = st.checkbox("Show violation snapshots", value=True)

    st.markdown("---")
    st.markdown("### Filter Violations")
    viol_filter = st.selectbox(
        "Violation type",
        ["All", "NO_HELMET", "TRIPLE_RIDING", "DOUBLE_RIDING"]
    )
    plate_search = st.text_input("Search by plate number", "")

    st.markdown("---")
    st.markdown("### Export")
    if os.path.exists(CSV_LOG_PATH):
        with open(CSV_LOG_PATH, "rb") as f:
            st.download_button(
                label="📥 Download Violations CSV",
                data=f,
                file_name="violations_export.csv",
                mime="text/csv"
            )

    st.markdown("---")
    st.caption("Traffic Monitoring System v1.0")


# ── Main content ──────────────────────────────────────────────────────────────
st.markdown('<div class="header-title">🚦 Traffic Monitoring Dashboard</div>',
            unsafe_allow_html=True)
st.caption(f"Database: {DB_PATH}")

# Load data
viol_df   = load_violations_df()
count_df  = load_vehicle_counts_df()

# Apply filters
if not viol_df.empty:
    if viol_filter != "All":
        viol_df = viol_df[viol_df["violation_type"] == viol_filter]
    if plate_search:
        viol_df = viol_df[viol_df["plate_number"].str.contains(
            plate_search.upper(), na=False)]


# ── Row 1: Summary metrics ────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

total_vehicles  = len(count_df) if not count_df.empty else 0
total_viol      = len(viol_df)  if not viol_df.empty else 0
no_helmet_count = len(viol_df[viol_df["violation_type"] == "NO_HELMET"]) \
                  if not viol_df.empty else 0
triple_count    = len(viol_df[viol_df["violation_type"] == "TRIPLE_RIDING"]) \
                  if not viol_df.empty else 0
viol_rate = f"{(total_viol/total_vehicles*100):.1f}%" if total_vehicles > 0 else "0%"

c1.metric("🚗 Total Vehicles",   total_vehicles)
c2.metric("⚠️ Total Violations",  total_viol)
c3.metric("⛑️ No Helmet",         no_helmet_count)
c4.metric("👥 Triple Riding",     triple_count)
c5.metric("📊 Violation Rate",    viol_rate)

st.markdown("---")

# ── Row 2: Charts ─────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<div class="section-title">Vehicle Type Breakdown</div>',
                unsafe_allow_html=True)
    if not count_df.empty and "vehicle_type" in count_df.columns:
        type_counts = count_df["vehicle_type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        fig = px.pie(type_counts, values="Count", names="Type",
                     color_discrete_sequence=["#185FA5","#0F6E56","#854F0B"])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=260)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No vehicle data yet. Start the pipeline to see data here.")

with ch2:
    st.markdown('<div class="section-title">Violation Types</div>',
                unsafe_allow_html=True)
    if not viol_df.empty and "violation_type" in viol_df.columns:
        v_counts = viol_df["violation_type"].value_counts().reset_index()
        v_counts.columns = ["Violation", "Count"]
        fig2 = px.bar(v_counts, x="Violation", y="Count",
                      color="Violation",
                      color_discrete_map={
                          "NO_HELMET":    "#E24B4A",
                          "TRIPLE_RIDING":"#854F0B",
                          "DOUBLE_RIDING":"#BA7517"
                      })
        fig2.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0),
                           height=260)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No violations recorded yet.")


# ── Row 2b: Helmet status + Rider count ──────────────────────────────────────
st.markdown("---")
hc1, hc2, hc3 = st.columns(3)

with hc1:
    st.markdown('<div class="section-title">🪖 Helmet Status (All Detections)</div>',
                unsafe_allow_html=True)
    if not viol_df.empty and "helmet_status" in viol_df.columns:
        helmet_counts = (
            viol_df["helmet_status"]
            .replace("", "unknown")
            .fillna("unknown")
            .value_counts()
            .reset_index()
        )
        helmet_counts.columns = ["Status", "Count"]
        color_map = {
            "with_helmet":    "#0F6E56",
            "without_helmet": "#E24B4A",
            "unknown":        "#aaaaaa",
        }
        fig_h = px.pie(
            helmet_counts, values="Count", names="Status",
            color="Status", color_discrete_map=color_map,
            hole=0.45,
        )
        fig_h.update_traces(textinfo="percent+label")
        fig_h.update_layout(margin=dict(t=10,b=0,l=0,r=0), height=270,
                            showlegend=True)
        st.plotly_chart(fig_h, use_container_width=True)

        with_h    = int((viol_df["helmet_status"] == "with_helmet").sum())
        without_h = int((viol_df["helmet_status"] == "without_helmet").sum())
        st.caption(f"✅ With helmet: **{with_h}** &nbsp;|&nbsp; ❌ Without helmet: **{without_h}**")
    else:
        st.info("No helmet data yet.")

with hc2:
    st.markdown('<div class="section-title">🏍️ Riders per Bike Distribution</div>',
                unsafe_allow_html=True)
    if not viol_df.empty and "rider_count" in viol_df.columns:
        rider_data = (
            viol_df["rider_count"]
            .fillna(1).astype(int)
            .value_counts()
            .sort_index()
            .reset_index()
        )
        rider_data.columns = ["Riders", "Count"]
        rider_data["Label"] = rider_data["Riders"].map(
            {1: "Solo (1)", 2: "Double (2)", 3: "Triple (3+)"}
        ).fillna(rider_data["Riders"].astype(str))
        color_map_r = {"Solo (1)": "#0F6E56", "Double (2)": "#BA7517", "Triple (3+)": "#E24B4A"}
        fig_r = px.bar(
            rider_data, x="Label", y="Count",
            color="Label", color_discrete_map=color_map_r,
            labels={"Label": "Rider Count", "Count": "Violations"},
        )
        fig_r.update_layout(showlegend=False, margin=dict(t=10,b=0,l=0,r=0),
                            height=270)
        st.plotly_chart(fig_r, use_container_width=True)

        solo   = int((viol_df["rider_count"].fillna(1).astype(int) == 1).sum())
        double = int((viol_df["rider_count"].fillna(1).astype(int) == 2).sum())
        triple = int((viol_df["rider_count"].fillna(1).astype(int) >= 3).sum())
        st.caption(f"Solo: **{solo}** &nbsp;|&nbsp; Double: **{double}** &nbsp;|&nbsp; Triple+: **{triple}**")
    else:
        st.info("No rider count data yet.")

with hc3:
    st.markdown('<div class="section-title">🔢 Recent Number Plates Detected</div>',
                unsafe_allow_html=True)
    if not viol_df.empty and "plate_number" in viol_df.columns:
        plates = (
            viol_df[viol_df["plate_number"].notna() &
                    (viol_df["plate_number"] != "UNKNOWN") &
                    (viol_df["plate_number"] != "")]
            [["timestamp", "plate_number", "violation_type"]]
            .head(10)
        )
        if not plates.empty:
            plates.columns = ["Time", "Plate", "Violation"]
            plates["Time"] = pd.to_datetime(
                plates["Time"], errors="coerce"
            ).dt.strftime("%H:%M:%S")
            st.dataframe(plates, use_container_width=True, height=270,
                         hide_index=True)
        else:
            st.info("No plates read yet.\nPlates appear once OCR detects them.")

        total_plates = int(
            viol_df["plate_number"].notna()
            .sum() if not viol_df.empty else 0
        )
        unknown = int(
            (viol_df["plate_number"] == "UNKNOWN").sum()
            if not viol_df.empty else 0
        )
        st.caption(f"Total records: **{total_plates}** &nbsp;|&nbsp; UNKNOWN: **{unknown}**")
    else:
        st.info("No plate data yet.")


# ── Row 3: Hourly chart ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">Hourly Vehicle Count (Today)</div>',
            unsafe_allow_html=True)
if not count_df.empty and "timestamp" in count_df.columns:
    count_df["hour"] = pd.to_datetime(
        count_df["timestamp"], errors="coerce"
    ).dt.strftime("%H:00")
    hourly = count_df.groupby("hour").size().reset_index(name="count")
    fig3 = px.bar(hourly, x="hour", y="count",
                  labels={"hour": "Hour", "count": "Vehicles"},
                  color_discrete_sequence=["#185FA5"])
    fig3.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=220)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No hourly data yet.")


# ── Row 4: Violation log table ────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Recent Violations Log</div>',
            unsafe_allow_html=True)

if not viol_df.empty:
    display_cols = [c for c in [
        "timestamp", "plate_number", "violation_type",
        "rider_count", "helmet_status", "vehicle_type"
    ] if c in viol_df.columns]

    st.dataframe(
        viol_df[display_cols].head(50),
        use_container_width=True,
        height=300,
    )

    # Snapshot viewer
    if show_snapshots and "snapshot_path" in viol_df.columns:
        st.markdown('<div class="section-title">Violation Snapshots</div>',
                    unsafe_allow_html=True)
        snap_paths = viol_df["snapshot_path"].dropna().tolist()
        snap_paths = [p for p in snap_paths if os.path.exists(p)][:8]

        if snap_paths:
            cols = st.columns(min(4, len(snap_paths)))
            for i, path in enumerate(snap_paths):
                with cols[i % 4]:
                    img = Image.open(path)
                    st.image(img, caption=os.path.basename(path),
                             use_column_width=True)
        else:
            st.info("Snapshot images will appear here when violations are recorded.")
else:
    st.info("No violations match the current filter.")


# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(3)
    st.rerun()
