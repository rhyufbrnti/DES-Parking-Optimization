import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from model import run_simulation

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Simulasi Parkir Mall",
    page_icon="🚗",
    layout="wide"
)

# --- 2. CUSTOM CSS (FIX: MEMAKSA TEKS JADI HITAM) ---
custom_css = """
<style>
    /* 1. Paksa Background Putih Bersih */
    .stApp {
        background-color: #ffffff;
    }
    
    /* 2. Paksa Sidebar Putih */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    
    /* 3. SUPER PENTING: Paksa Semua Teks Jadi Hitam/Gelap */
    h1, h2, h3, h4, h5, h6, p, li, span, div {
        color: #212529 !important;
    }
    
    /* 4. Fix Angka Hasil (Metric) yang Tadi Hilang */
    [data-testid="stMetricValue"] {
        color: #000000 !important; /* Hitam Pekat */
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6c757d !important; /* Abu-abu utk label kecil */
    }
    
    /* 5. Fix Tulisan di Tab (Perbandingan/Trend) yang Tadi Hilang */
    button[data-baseweb="tab"] {
        color: #000000 !important; /* Teks Tab Hitam */
        font-weight: 600 !important;
    }
    
    /* Tab yang sedang aktif (Selected) */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #e3f2fd !important;
        color: #0d47a1 !important;
        border-bottom: 2px solid #0d47a1 !important;
    }

    /* 6. Tombol Jalankan (Biru) */
    div.stButton > button {
        background-color: #2563eb;
        color: white !important; /* Khusus tombol teksnya putih */
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. JUDUL & SIDEBAR ---
st.title("🚗 Smart Parking Simulator")
st.markdown("### Analisis Perbandingan Efisiensi: **Manual vs Smart**")
st.markdown("---")

# Input Sidebar
st.sidebar.header("⚙️ Konfigurasi")
kapasitas_input = st.sidebar.number_input(
    "Kapasitas Slot Parkir", 
    min_value=10, max_value=1000, value=147, step=10
)
st.sidebar.info("Klik tombol di kanan untuk memulai.")

# --- 4. LOGIKA UTAMA ---
if st.button("▶️ JALANKAN SIMULASI"):
    with st.spinner('Sedang memproses...'):
        summary, df_results = run_simulation(kapasitas_input)

    if summary is None:
        st.error("Error: Dataset CSV tidak ditemukan!")
    else:
        st.success(f"✅ Selesai! Data: {summary['total_cars']} mobil.")
        
        # --- METRICS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔴 Sistem Manual")
            st.metric(
                label="Rata-rata Waktu Cari", 
                value=f"{summary['manual_avg_search']} min",
                delta=f"-{summary['manual_avg_queue']} min antre",
                delta_color="inverse"
            )
        
        with col2:
            st.markdown("#### 🟢 Sistem Smart")
            st.metric(
                label="Rata-rata Waktu Cari", 
                value=f"{summary['smart_avg_search']} min",
                delta="Efisien",
            )

        # --- GRAFIK ---
        st.markdown("### 📊 Visualisasi Data")
        tab1, tab2 = st.tabs(["Perbandingan Rata-rata", "Trend Antrean"])
        
        # Setup Grafik agar teksnya HITAM (bukan transparan/putih)
        plt.rcParams.update({
            'axes.facecolor': 'white',
            'figure.facecolor': 'white',
            'text.color': 'black',
            'axes.labelcolor': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black'
        })
        
        color_manual, color_smart = '#ef233c', '#2ec4b6'
        
        with tab1:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            scenarios = ['Manual', 'Smart']
            vals = [summary['manual_avg_search'], summary['smart_avg_search']]
            bars = ax.bar(scenarios, vals, color=[color_manual, color_smart])
            
            ax.set_ylabel("Menit")
            ax.set_title("Waktu Cari Parkir")
            ax.bar_label(bars, fmt='%.2f', padding=3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            st.pyplot(fig)
            
        with tab2:
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            data = df_results.pivot_table(index='Arrival_Time', columns='Scenario', values='Queue_Time', aggfunc='mean').fillna(0).head(200)
            
            ax2.plot(data.index, data['MANUAL'], label='Manual', color=color_manual)
            ax2.plot(data.index, data['SMART'], label='Smart', color=color_smart)
            
            ax2.set_title("Fluktuasi Antrean")
            ax2.legend()
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            st.pyplot(fig2)