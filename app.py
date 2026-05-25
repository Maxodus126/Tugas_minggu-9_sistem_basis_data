"""
SC-DATA Minggu 9 — Event Monitor Dashboard
Simulasi streaming data dan near real-time dashboard
"""

import os
from datetime import datetime
import duckdb
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────
# KONFIGURASI PATH
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_data_path(filename: str) -> str:
    candidates = [
        os.path.join(BASE_DIR, "data", filename),
        os.path.join(os.path.dirname(BASE_DIR), "data", filename),
        os.path.join(os.path.dirname(BASE_DIR), "sc_data_minggu9", "data", filename),
        os.path.join(os.path.dirname(BASE_DIR), "sc_data_minggu9", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]

DATA_PATH = find_data_path("kehadiran_event.csv")
DB_PATH = os.path.join(BASE_DIR, "sc_data.duckdb")

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="SC-DATA | Event Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CSS — Tampilan cerah & terstruktur
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Background utama */
.stApp {
    background: linear-gradient(135deg, #EEF2FF 0%, #F0FDF4 50%, #FFF7ED 100%);
}

/* Header banner */
.main-header {
    background: linear-gradient(135deg, #1E40AF 0%, #0369A1 50%, #0F766E 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(30,64,175,0.25);
}
.main-header h1 { font-size: 1.8rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
.main-header p  { font-size: 0.9rem; opacity: 0.85; margin: 0.25rem 0 0; }

/* Metric cards */
.metric-card {
    background: white;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 4px solid #3B82F6;
    text-align: center;
}
.metric-card.green  { border-top-color: #10B981; }
.metric-card.yellow { border-top-color: #F59E0B; }
.metric-card.red    { border-top-color: #EF4444; }
.metric-card.blue   { border-top-color: #3B82F6; }
.metric-val  { font-size: 2.2rem; font-weight: 700; margin: 0; line-height: 1; }
.metric-lbl  { font-size: 0.8rem; color: #6B7280; margin-top: 0.35rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.green-val   { color: #059669; }
.yellow-val  { color: #D97706; }
.red-val     { color: #DC2626; }
.blue-val    { color: #2563EB; }

/* Section cards */
.section-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}
.section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.badge-hadir  { background:#D1FAE5; color:#065F46; }
.badge-izin   { background:#DBEAFE; color:#1E40AF; }
.badge-sakit  { background:#FEF3C7; color:#92400E; }
.badge-alfa   { background:#FEE2E2; color:#991B1B; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E3A8A 0%, #1E40AF 100%) !important;
}
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: white !important;
    color: #1E40AF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    padding: 0.7rem !important;
    font-size: 0.9rem !important;
    margin-bottom: 0.5rem !important;
    transition: all .2s !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}

/* Timestamp chip */
.ts-chip {
    display: inline-block;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1D4ED8;
    padding: 4px 14px;
    border-radius: 99px;
    font-size: 0.82rem;
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
}

/* Info / konsep box */
.concept-box {
    background: linear-gradient(135deg, #EFF6FF, #F0FDF4);
    border: 1px solid #BFDBFE;
    border-left: 4px solid #3B82F6;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    font-size: 0.88rem;
    color: #1E3A8A;
    line-height: 1.6;
}

/* Footer */
.footer {
    text-align: center;
    font-size: 0.78rem;
    color: #9CA3AF;
    padding: 1.5rem 0 0.5rem;
    border-top: 1px solid #E5E7EB;
    margin-top: 2rem;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# FUNGSI DATABASE
# ──────────────────────────────────────────────
@st.cache_data
def load_all_events():
    if not os.path.exists(DATA_PATH):
        st.error(
            f"❌ File data tidak ditemukan: {DATA_PATH}\n"
            "Pastikan file `kehadiran_event.csv` ada di folder `data/` atau di folder `sc_data_minggu9/data/`.")
        st.markdown("`Dicari di: `" + "<br>".join([
            os.path.join(BASE_DIR, "data", "kehadiran_event.csv"),
            os.path.join(os.path.dirname(BASE_DIR), "data", "kehadiran_event.csv"),
            os.path.join(os.path.dirname(BASE_DIR), "sc_data_minggu9", "data", "kehadiran_event.csv"),
        ]), unsafe_allow_html=True)
        st.stop()

    df = pd.read_csv(DATA_PATH, parse_dates=["waktu_event"])
    required = {"event_id", "nim", "kode_mk", "waktu_event", "status_hadir"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"❌ Kolom wajib tidak ditemukan: {missing}")
        st.stop()
    df["status_hadir"] = df["status_hadir"].str.lower().str.strip()
    return df.sort_values("waktu_event").reset_index(drop=True)


def init_db():
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS event_log (
            log_id       INTEGER,
            event_id     VARCHAR,
            nim          VARCHAR,
            kode_mk      VARCHAR,
            waktu_event  TIMESTAMP,
            status_hadir VARCHAR,
            loaded_at    TIMESTAMP
        )
    """)
    return con


def get_loaded_ids(con):
    try:
        return set(con.execute("SELECT event_id FROM event_log").fetchdf()["event_id"].tolist())
    except Exception:
        return set()


def append_events(con, rows):
    current_count = con.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
    rows = rows.copy()
    rows["loaded_at"] = datetime.now()
    rows.insert(0, "log_id", range(current_count + 1, current_count + 1 + len(rows)))
    con.register("new_rows", rows)
    con.execute("INSERT INTO event_log SELECT * FROM new_rows")


def get_event_log(con):
    return con.execute("SELECT * FROM event_log ORDER BY waktu_event DESC").fetchdf()


def status_badge(status):
    return f'<span class="badge badge-{status}">{status}</span>'


# ──────────────────────────────────────────────
# INISIALISASI
# ──────────────────────────────────────────────
all_events = load_all_events()
con        = init_db()
loaded_ids = get_loaded_ids(con)
remaining  = all_events[~all_events["event_id"].isin(loaded_ids)]

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 SC-DATA")
    st.markdown("**Modul 9** — Event Monitor")
    st.markdown("---")

    st.markdown("### ⚙️ Kontrol Simulasi")
    batch_size = st.slider("Event per klik", 1, 10, 5, help="Jumlah event dimuat setiap klik 'Load Event Baru'")

    st.markdown("---")
    st.markdown(f"📁 **Total sumber:** {len(all_events)} event")
    st.markdown(f"✅ **Sudah dimuat:** {len(loaded_ids)} event")
    st.markdown(f"⏳ **Sisa antrian:** {len(remaining)} event")

    progress_pct = len(loaded_ids) / len(all_events) if len(all_events) > 0 else 0
    st.progress(progress_pct, text=f"{int(progress_pct*100)}% dimuat")

    st.markdown("---")

    if st.button("🔄 Load Event Baru", type="primary"):
        if remaining.empty:
            st.warning("✅ Semua event sudah dimuat!")
        else:
            batch = remaining.head(batch_size)
            append_events(con, batch)
            st.success(f"✓ {len(batch)} event berhasil dimuat")
            st.cache_data.clear()
            st.rerun()

    if st.button("🗑️ Reset event_log"):
        con.execute("DELETE FROM event_log")
        st.info("Event log dikosongkan.")
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; opacity:0.7; line-height:1.6;'>
    <b>Konsep near real-time:</b><br>
    Data CSV dimuat bertahap simulasikan streaming event kehadiran kampus.
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# MAIN CONTENT
# ──────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Event Monitor Dashboard</h1>
    <p>SC-DATA Minggu 9 · Simulasi Near Real-Time · Smart Campus Data & AI Assistant</p>
</div>
""", unsafe_allow_html=True)

# Ambil data log
event_log = get_event_log(con)

# ── KOSONG STATE ──
if event_log.empty:
    st.markdown("""
    <div class="concept-box">
        <b>🚀 Dashboard siap.</b> Belum ada event yang dimuat.<br>
        Klik <b>"Load Event Baru"</b> di sidebar untuk memulai simulasi near real-time kehadiran mahasiswa.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📖 Konsep: Batch vs Streaming vs Near Real-Time")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">🗂️ Batch</div>
            <p style='font-size:.85rem;color:#374151;'>Data diproses dalam satu kelompok besar. Biasanya terjadwal (malam/minggu). Latensi tinggi.</p>
            <code style='font-size:.78rem;background:#F3F4F6;padding:4px 8px;border-radius:6px;'>Contoh: laporan rekap bulanan</code>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">⚡ Streaming</div>
            <p style='font-size:.85rem;color:#374151;'>Data diproses satu per satu saat event terjadi. Latensi milidetik. Butuh Kafka/Flink.</p>
            <code style='font-size:.78rem;background:#F3F4F6;padding:4px 8px;border-radius:6px;'>Contoh: deteksi fraud real-time</code>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">🔄 Near Real-Time</div>
            <p style='font-size:.85rem;color:#374151;'>Simulasi: CSV di-refresh bertahap, latensi detik. Dipakai pada modul ini.</p>
            <code style='font-size:.78rem;background:#F3F4F6;padding:4px 8px;border-radius:6px;'>Contoh: dashboard kehadiran ini</code>
        </div>
        """, unsafe_allow_html=True)

else:
    latest_update = event_log["loaded_at"].max()

    # ── TIMESTAMP ──
    st.markdown(f"""
    <div style='margin-bottom:1rem;'>
        <span class='ts-chip'>🕐 Update terakhir: {latest_update.strftime('%d %b %Y, %H:%M:%S')}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── METRIC CARDS ──
    status_counts = event_log["status_hadir"].value_counts().to_dict()
    total = len(event_log)
    n_hadir = status_counts.get("hadir", 0)
    n_izin  = status_counts.get("izin", 0)
    n_sakit = status_counts.get("sakit", 0)
    n_alfa  = status_counts.get("alfa", 0)

    pct_hadir = int(n_hadir / total * 100) if total > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(f"""<div class="metric-card blue"><div class="metric-val blue-val">{total}</div><div class="metric-lbl">Total Event</div></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class="metric-card green"><div class="metric-val green-val">{n_hadir}</div><div class="metric-lbl">✅ Hadir</div></div>""", unsafe_allow_html=True)
    col3.markdown(f"""<div class="metric-card blue"><div class="metric-val blue-val">{n_izin}</div><div class="metric-lbl">📋 Izin</div></div>""", unsafe_allow_html=True)
    col4.markdown(f"""<div class="metric-card yellow"><div class="metric-val yellow-val">{n_sakit}</div><div class="metric-lbl">🤒 Sakit</div></div>""", unsafe_allow_html=True)
    col5.markdown(f"""<div class="metric-card red"><div class="metric-val red-val">{n_alfa}</div><div class="metric-lbl">❌ Alfa</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABEL 10 EVENT TERBARU ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 10 Event Terbaru</div>', unsafe_allow_html=True)

    top10 = event_log.head(10).copy()
    top10["waktu_event"] = pd.to_datetime(top10["waktu_event"]).dt.strftime("%d %b %Y %H:%M:%S")
    top10["loaded_at"]   = pd.to_datetime(top10["loaded_at"]).dt.strftime("%d %b %Y %H:%M:%S")
    top10 = top10.rename(columns={
        "log_id": "No", "event_id": "Event ID", "nim": "NIM",
        "kode_mk": "Mata Kuliah", "waktu_event": "Waktu Event",
        "status_hadir": "Status", "loaded_at": "Dimuat Pada"
    })
    st.dataframe(top10, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── GRAFIK ──
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Rekap Status Kehadiran</div>', unsafe_allow_html=True)
        status_df = event_log.groupby("status_hadir").size().reset_index(name="Jumlah")
        status_df.columns = ["Status", "Jumlah"]
        status_df = status_df.sort_values("Jumlah", ascending=False)
        st.bar_chart(status_df.set_index("Status"), color="#3B82F6", height=280)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏫 Kehadiran per Mata Kuliah</div>', unsafe_allow_html=True)
        mk_status = event_log.groupby(["kode_mk", "status_hadir"]).size().reset_index(name="jumlah")
        pivot = mk_status.pivot(index="kode_mk", columns="status_hadir", values="jumlah").fillna(0)
        pivot.index.name = "Mata Kuliah"
        st.bar_chart(pivot, height=280)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── PERSENTASE KEHADIRAN ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Tingkat Kehadiran</div>', unsafe_allow_html=True)

    kehadiran_mk = event_log.groupby("kode_mk").apply(
        lambda x: round(len(x[x["status_hadir"]=="hadir"]) / len(x) * 100, 1)
    ).reset_index(name="Persentase Hadir (%)")
    kehadiran_mk.columns = ["Mata Kuliah", "Persentase Hadir (%)"]

    for _, row in kehadiran_mk.iterrows():
        pct = row["Persentase Hadir (%)"]
        color = "#10B981" if pct >= 75 else ("#F59E0B" if pct >= 50 else "#EF4444")
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>
            <div style='width:90px;font-size:.85rem;font-weight:600;color:#374151;'>{row["Mata Kuliah"]}</div>
            <div style='flex:1;background:#F3F4F6;border-radius:99px;height:16px;overflow:hidden;'>
                <div style='width:{pct}%;height:100%;background:{color};border-radius:99px;transition:width .5s;'></div>
            </div>
            <div style='width:50px;text-align:right;font-size:.85rem;font-weight:700;color:{color};'>{pct}%</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── EVENT LOG ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗃️ Tabel event_log (Lengkap)</div>', unsafe_allow_html=True)
    display_log = event_log.copy()
    display_log["waktu_event"] = pd.to_datetime(display_log["waktu_event"]).dt.strftime("%d %b %Y %H:%M:%S")
    display_log["loaded_at"]   = pd.to_datetime(display_log["loaded_at"]).dt.strftime("%d %b %Y %H:%M:%S")
    st.dataframe(display_log, use_container_width=True, hide_index=True, height=300)
    st.caption(f"Total {len(event_log)} record tersimpan di DuckDB (sc_data.duckdb)")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── EXPORT ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💾 Export & Screenshot</div>', unsafe_allow_html=True)

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        csv_data = event_log.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download event_log.csv",
            data=csv_data,
            file_name=f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_e2:
        st.info("📸 Untuk screenshot: tekan **F12** → Ctrl+Shift+P → 'Screenshot' ATAU gunakan Snipping Tool (Windows) / Cmd+Shift+4 (Mac)")
    st.markdown('</div>', unsafe_allow_html=True)

# ── KONSEP BOX (selalu tampil) ──
st.markdown("""
<div class="concept-box">
    <b>📖 Catatan Konsep Near Real-Time:</b>
    Dashboard ini mensimulasikan near real-time dengan memuat event dari CSV secara bertahap setiap klik tombol.
    Data sumber tetap berupa file batch, namun proses load bertahap + timestamp + event_log DuckDB
    membuat perilakunya menyerupai streaming sederhana — cukup untuk skala proyek capstone kampus.
    <br><br>
    <b>Alur Event:</b> CSV → Ingest (DuckDB) → Transform (rekap status) → Visualisasi (grafik) → Log (event_log)
</div>
""", unsafe_allow_html=True)

# ── FOOTER ──
st.markdown("""
<div class="footer">
    SC-DATA · Minggu 9 — Event Monitor Dashboard · Sistem Basis Data Modern dan Arsitektur Data SIAP AI
    <br>Dosen: Oni Bibin Bintoro / Ashari Abidin · ISTN
</div>
""", unsafe_allow_html=True)
