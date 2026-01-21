from flask import Flask, render_template, request # <-- JANGAN LUPA IMPORT request
from model import run_simulation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run')
def run():
    # 1. AMBIL INPUT DARI USER (Browser)
    # Jika user tidak isi, default-nya 147
    kapasitas_user = request.args.get('kapasitas', default=147, type=int)

    # 2. Kirim angka tersebut ke Model SimPy
    summary, df_results = run_simulation(kapasitas_user)
    
    if summary is None:
        return "Error: Dataset tidak ditemukan!"

    # 3. Buat Grafik (Sama seperti sebelumnya)
    fig, ax = plt.subplots(figsize=(6, 4))
    scenarios = ['Manual', 'Smart']
    values = [summary['manual_avg_search'], summary['smart_avg_search']]
    colors = ['tomato', 'teal']
    
    ax.bar(scenarios, values, color=colors)
    ax.set_title(f'Waktu Cari Parkir (Kapasitas: {kapasitas_user})') # Judul dinamis
    ax.set_ylabel('Menit')
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template('index.html', 
                           result=summary, 
                           plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)