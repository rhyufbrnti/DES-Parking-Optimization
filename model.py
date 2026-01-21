import simpy
import pandas as pd
import random

# --- KONFIGURASI FILE ---
# Pastikan file ini ada di folder yang sama
FILE_DATASET = 'dataset_final_compressed.csv'

# --- 1. LOGIKA PENCARIAN PARKIR (ALGORITMA) ---
def calculate_search_time(env, parking_lot, scenario):
    """
    Menghitung durasi 'Cruising' berdasarkan okupansi saat itu.
    """
    # Safety check: Hindari pembagian dengan nol jika user input 0
    if parking_lot.capacity == 0:
        return 100 # Hukuman waktu sangat lama jika kapasitas 0
        
    occupancy = parking_lot.count / parking_lot.capacity
    
    if scenario == 'MANUAL':
        # BLIND SEARCH: Semakin penuh, waktu cari naik drastis (Eksponensial/Random)
        base_search = 1.0
        # Jika penuh, tambah waktu acak antara 5-15 menit dikali tingkat kepenuhan
        confusion_factor = random.uniform(5, 15) 
        return base_search + (occupancy * confusion_factor)
        
    elif scenario == 'SMART':
        # GUIDED SEARCH: Waktu cari stabil karena dipandu sensor
        base_search = 1.0
        # Hanya butuh waktu tempuh fisik (0.5 - 2 menit)
        travel_distance = random.uniform(0.5, 2.0)
        return base_search + travel_distance

# --- 2. PROSES MOBIL (AGEN) ---
def car_process(env, name, parking_lot, duration_park, stats, scenario):
    
    arrival_time = env.now
    
    # A. Request Masuk (Antri di Gate)
    with parking_lot.request() as request:
        yield request # Menunggu sampai ada slot kosong
        
        # B. Masuk Gate
        enter_gate_time = env.now
        queue_time = enter_gate_time - arrival_time
        
        # C. Mencari Parkir (Searching)
        search_duration = calculate_search_time(env, parking_lot, scenario)
        yield env.timeout(search_duration)
        
        # D. Parkir (Parking)
        yield env.timeout(duration_park)
        
        # E. Catat Data Statistik
        stats.append({
            'Scenario': scenario,
            'Car_ID': name,
            'Arrival_Time': arrival_time,
            'Queue_Time': queue_time,
            'Search_Time': search_duration,
            'Total_Time': env.now - arrival_time
        })

# --- 3. HELPER: PENUNDAAN KEDATANGAN ---
def delayed_car(env, delay, name, parking_lot, duration, stats, scenario):
    yield env.timeout(delay) # Tunggu sampai jadwal kedatangan tiba
    yield env.process(car_process(env, name, parking_lot, duration, stats, scenario))

# --- 4. FUNGSI UTAMA (DIPANGGIL OLEH FLASK) ---
def run_simulation(input_kapasitas):
    """
    Menjalankan simulasi berdasarkan kapasitas yang diinput user.
    """
    # A. Load Data
    try:
        df = pd.read_csv(FILE_DATASET)
        df['Start Time'] = pd.to_datetime(df['Start Time'])
    except FileNotFoundError:
        return None, "Error: File CSV dataset tidak ditemukan."

    all_stats = []

    # B. Loop untuk menjalankan skenario MANUAL dan SMART secara bergantian
    for scenario_name in ['MANUAL', 'SMART']:
        # Reset Environment untuk setiap skenario
        env = simpy.Environment()
        
        # PENTING: Kapasitas menggunakan input dari User (Flask)
        parking_lot = simpy.Resource(env, capacity=input_kapasitas)
        
        stats = []
        start_simulation = df['Start Time'].min()
        
        # Jadwalkan mobil
        for i, row in df.iterrows():
            # Hitung kapan mobil muncul (menit ke-berapa sejak awal)
            arrival_offset = (row['Start Time'] - start_simulation).total_seconds() / 60
            duration = row['Duration in Minutes']
            
            # Masukkan ke antrean proses SimPy
            env.process(delayed_car(env, arrival_offset, f"Car_{i}", parking_lot, duration, stats, scenario_name))
        
        # Jalankan sampai selesai + buffer waktu
        last_arrival = (df['Start Time'].max() - start_simulation).total_seconds() / 60
        env.run(until=last_arrival + 200)
        
        # Gabungkan hasil
        all_stats.extend(stats)

    # C. Olah Hasil (Summarize)
    df_res = pd.DataFrame(all_stats)
    
    if df_res.empty:
        return None, "Error: Simulasi tidak menghasilkan data."

    summary = {
        'manual_avg_search': round(df_res[df_res['Scenario']=='MANUAL']['Search_Time'].mean(), 2),
        'smart_avg_search': round(df_res[df_res['Scenario']=='SMART']['Search_Time'].mean(), 2),
        'manual_avg_queue': round(df_res[df_res['Scenario']=='MANUAL']['Queue_Time'].mean(), 2),
        'smart_avg_queue': round(df_res[df_res['Scenario']=='SMART']['Queue_Time'].mean(), 2),
        'total_cars': len(df),
        'kapasitas_dipakai': input_kapasitas # Info ini dikirim balik ke Web untuk ditampilkan
    }
    
    return summary, df_res