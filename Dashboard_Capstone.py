from tracemalloc import Filter

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# SETUP HALAMAN
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("Dashboard Keuangan & Penjualan UMKM")

# LOAD DATASET
@st.cache_data
def load_data():
    df = pd.read_csv("synthetic_umkm_clean.csv")
    df['waktu'] = pd.to_datetime(df['waktu'])
    return df

df = load_data()

# CHART BOX RINGKASAN KESELURUHAN (Tidak Terpengaruh Sidebar)
st.markdown("### Performa Keseluruhan UMKM")

# Perhitungan nilai  dari dataframe asli
total_omset_global = df[df['type'] == 'pemasukan']['nominal'].sum()
total_pengeluaran_global = df[df['type'] == 'pengeluaran']['nominal'].sum()
net_profit_global = total_omset_global - total_pengeluaran_global

# Membuat susunan 3 kotak ke samping
col_global1, col_global2, col_global3 = st.columns(3)

with col_global1:
    with st.container(border=True): 
        st.metric(label="Total Omset Keseluruhan", value=f"Rp {total_omset_global:,.0f}")

with col_global2:
    with st.container(border=True): 
        st.metric(label="Total Pengeluaran Keseluruhan", value=f"Rp {total_pengeluaran_global:,.0f}")

with col_global3:
    with st.container(border=True): 
        st.metric(
            label="Total Net Profit Keseluruhan", 
            value=f"Rp {net_profit_global:,.0f}",
            # delta=f"Rp {net_profit_global:,.0f}"
        )

st.divider()

# KONFIGURASI SIDEBAR 
st.sidebar.header("Filter Rentang Waktu")

# Pilihan tipe rentang waktu
tipe_rentang = st.sidebar.selectbox(
    "Pilih Rentang Analisis:",
    options=["Harian", "Bulanan", "Tahunan"]
)

hari_ini = datetime.date.today()

# Filter Kalender Berdasarkan Tipe Rentang yang Dipilih
if tipe_rentang == "Harian":
    default_range = [hari_ini - datetime.timedelta(days=7), hari_ini]
    rentang_tanggal = st.sidebar.date_input("Pilih Rentang Hari:", default_range)
    
    if isinstance(rentang_tanggal, (list, tuple)) and len(rentang_tanggal) == 2:
        start_date, end_date = rentang_tanggal
        df_filtered = df[(df['waktu'].dt.date >= start_date) & (df['waktu'].dt.date <= end_date)]
    else:
        df_filtered = df[df['waktu'].dt.date == rentang_tanggal[0]]

elif tipe_rentang == "Bulanan":
    awal_tahun = datetime.date(hari_ini.year, 1, 1)
    rentang_bulan = st.sidebar.date_input("Pilih Rentang Bulan (Klik bulan mulai & selesai):", [awal_tahun, hari_ini])
    
    if isinstance(rentang_bulan, (list, tuple)) and len(rentang_bulan) == 2:
        start_month, end_month = rentang_bulan
        df_filtered = df[
            (df['waktu'].dt.to_period('M') >= pd.Period(start_month, freq='M')) & 
            (df['waktu'].dt.to_period('M') <= pd.Period(end_month, freq='M'))
        ]
    else:
        df_filtered = df[df['waktu'].dt.to_period('M') == pd.Period(rentang_bulan[0], freq='M')]

elif tipe_rentang == "Tahunan":
    tahun_sekarang = hari_ini.year
    tahun_minimal = tahun_sekarang - 5
    
    # Slider interaktif untuk memilih rentang tahun (misal: 2024 - 2026)
    rentang_tahun = st.sidebar.slider(
        "Pilih Rentang Tahun:",
        min_value=tahun_minimal,
        max_value=tahun_sekarang,
        value=(tahun_sekarang - 1, tahun_sekarang),
        step=1
    )
    tahun_mulai, tahun_selesai = rentang_tahun
    df_filtered = df[(df['waktu'].dt.year >= tahun_mulai) & (df['waktu'].dt.year <= tahun_selesai)]

# Dropdown Filter Kategori
st.sidebar.markdown("---")
st.sidebar.header("Filter Kategori")
list_kategori = ["Semua Kategori"] + list(df['kategori'].unique())
kategori_terpilih = st.sidebar.selectbox("Pilih Kategori Produk:", options=list_kategori)

if kategori_terpilih != "Semua Kategori":
    df_filtered = df_filtered[df_filtered['kategori'] == kategori_terpilih]

# LOGIKAL GRAFIK & VISUALISASI 
st.subheader(f"Analisis Filtered Data ({tipe_rentang} - Kategori: {kategori_terpilih})")

if df_filtered.empty:
    st.warning("Tidak ada transaksi pada filter yang dipilih.")
else:
    st.markdown("""
        <style>
        .card-container {
            background-color: #ffffff;
            border: 1px solid #e6e8eb;
            border-radius: 8px;
            padding: 0px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .card-header {
            background-color: #2b2d3c;
            color: #ffffff;
            padding: 8px 15px;
            font-size: 14px;
            font-weight: bold;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .card-body {
            padding: 15px;
            color: #2b2d3c;
        }
        </style>
    """, unsafe_allow_html=True)

    # Penyiapan Data Tren Sumbu X Berdasarkan Tipe Rentang Waktu
    df_chart = df_filtered.copy()
    if tipe_rentang == "Harian":
        df_chart['Periode'] = df_chart['waktu'].dt.strftime('%Y-%m-%d')
    elif tipe_rentang == "Bulanan":
        df_chart['Periode'] = df_chart['waktu'].dt.strftime('%Y-%m')
    elif tipe_rentang == "Tahunan":
        df_chart['Periode'] = df_chart['waktu'].dt.strftime('%Y')
        
    df_chart['Pemasukan'] = df_chart.apply(lambda r: r['nominal'] if r['type'] == 'pemasukan' else 0, axis=1)
    df_chart['Pengeluaran'] = df_chart.apply(lambda r: r['nominal'] if r['type'] == 'pengeluaran' else 0, axis=1)
    
    df_trend = df_chart.groupby('Periode')[['Pemasukan', 'Pengeluaran']].sum().reset_index()
    df_trend['Net_Profit'] = df_trend['Pemasukan'] - df_trend['Pengeluaran']

    # BARIS 1: KOTAK METRIK 
    m1, m2, m3, m4 = st.columns(4)
    
    pemasukan_curr = df_filtered[df_filtered['type'] == 'pemasukan']['nominal'].sum()
    pengeluaran_curr = df_filtered[df_filtered['type'] == 'pengeluaran']['nominal'].sum()
    net_profit_curr = pemasukan_curr - pengeluaran_curr
    total_transaksi = len(df_filtered)

    with m1:
        st.markdown(f'<div class="card-container"><div class="card-header">Total Pemasukan</div><div class="card-body"><h2 style="margin:0;">Rp {pemasukan_curr:,.0f}</h2><span style="color:green; font-size:12px;">▲ Active Filter</span></div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="card-container"><div class="card-header">Total Pengeluaran</div><div class="card-body"><h2 style="margin:0;">Rp {pengeluaran_curr:,.0f}</h2><span style="color:red; font-size:12px;">▼ Active Filter</span></div></div>', unsafe_allow_html=True)
    with m3:
        warna_teks = "green" if net_profit_curr >= 0 else "red"
        st.markdown(f'<div class="card-container"><div class="card-header">Net Profit Rentang</div><div class="card-body"><h2 style="color:{warna_teks}; margin:0;">Rp {net_profit_curr:,.0f}</h2><span style="font-size:12px;">Pemasukan - Pengeluaran</span></div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="card-container"><div class="card-header">Jumlah Transaksi</div><div class="card-body"><h2 style="margin:0;">{total_transaksi} </h2><span style="color:blue; font-size:12px;">Volume Data</span></div></div>', unsafe_allow_html=True)

    # --- BARIS 2: RATIO 1:3 
    row2_col1, row2_col2 = st.columns([1, 3])
    
    with row2_col1:
        with st.container(border=True):
            st.markdown("##### Info Filter")
            st.caption(f"Rentang: {tipe_rentang}")
            st.caption(f"Kategori: {kategori_terpilih}")
        with st.container(border=True):
            st.markdown("##### Status")
            st.success("Data Sinkron")
            
    with row2_col2:
        with st.container(border=True):
            st.markdown("##### Net Profit ")
            
            # Menggunakan px.area untuk grafik garis trendline estetik
            fig_net_profit = px.area(
                df_trend, x='Periode', y='Net_Profit',
                labels={'Net_Profit': 'Net Profit (Rp)', 'Periode': 'Waktu'},
                markers=True
            )
            fig_net_profit.update_traces(line_color='#00d2ff', fillcolor='rgba(0, 210, 255, 0.15)')
            fig_net_profit.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_net_profit, use_container_width=True)

    # BARIS 3
    st.markdown("---")
# BARIS 1
    col_r1_1, col_r1_2 = st.columns(2)

#Kotak Grafik 2: Pemasukan vs Pengeluaran
    with col_r1_1:
        with st.container(border=True):
            st.markdown("##### Pemasukan vs Pengeluaran")
            df_ratio_trend = pd.melt(df_trend, id_vars=['Periode'], value_vars=['Pemasukan', 'Pengeluaran'], var_name='Tipe', value_name='Nominal')
            fig_ratio = px.bar(
                df_ratio_trend, x='Periode', y='Nominal', color='Tipe', barmode='group',
                color_discrete_map={'Pemasukan': '#2ecc71', 'Pengeluaran': '#e74c3c'},
                labels={'Nominal': 'Total (Rp)', 'Periode': 'Waktu'}
            )
            fig_ratio.update_layout(height=250, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_ratio, use_container_width=True)
    
    # Kotak Grafik 3: Pie Chart Kategori Produk
    with col_r1_2:
        with st.container(border=True):
            st.markdown("##### Kategori Produk Terlaku")
            df_kat_count = df_filtered.groupby('kategori').size().reset_index(name='banyak_transaksi')
            fig_kat = px.pie(df_kat_count, values='banyak_transaksi', names='kategori')
            fig_kat.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_kat, use_container_width=True)
    
    # BARIS 2: Produk Terlaku & Kurang Laku 
    col_r2_1, col_r2_2 = st.columns(2)
    
    # Pra-pemrosesan Data Produk 
    df_pemasukan = df_filtered[df_filtered['type'] == 'pemasukan']
    biru_jenuh_custom = ["#2362A1","#2E71B3","#4C8ECB","#579EE0","#7BB9F2"]
    oranye_jenuh_custom = ["#B54F00", "#D66200", "#FF7B00", "#FF9D3B", "#FFB76B"]
    # ["FF7B00","#FF8D21", "#FFA652","#FFB76B", "#FFCD90"]
    
    if df_pemasukan.empty:
        with col_r2_1:
            with st.container(border=True):
                st.markdown("##### Top 5 Produk Terlaku")
                st.caption("Tidak ada data pemasukan")
        with col_r2_2:
            with st.container(border=True):
                st.markdown("##### 5 Produk Kurang Laku")
                st.caption("Tidak ada data pemasukan")
    else:
        # Grouping data produk berdasarkan total terjual
        df_prod_count = df_pemasukan.groupby('Nama_Produk').size().reset_index(name='jumlah_terjual')
        
        # Kotak Grafik 4: Top 5 Produk Terlaku 
        with col_r2_1:
            with st.container(border=True):
                st.markdown("##### Top 5 Produk Terlaku")
                df_top5 = df_prod_count.nlargest(5, 'jumlah_terjual').sort_values(by='jumlah_terjual', ascending=True)
                
                fig_prod = px.bar(
                    df_top5, x='jumlah_terjual', y='Nama_Produk', orientation='h',
                    labels={'jumlah_terjual': 'Total Terjual', 'Nama_Produk': 'Nama Produk'},
                    color='jumlah_terjual', color_continuous_scale=biru_jenuh_custom,
                )
                fig_prod.update_layout(height=250, showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_prod, use_container_width=True)
    
        # Kotak Grafik 5: Bottom 5 Produk Terlaku 
        with col_r2_2:
            with st.container(border=True):
                st.markdown("##### 5 Produk Kurang Laku")
                # Menggunakan nsmallest untuk mencari 5 produk paling sedikit terjual
                # Di-sort ascending=False supaya produk yang paling sedikit berada di posisi bawah chart horizontal
                df_bottom5 = df_prod_count.nsmallest(5, 'jumlah_terjual').sort_values(by='jumlah_terjual', ascending=False)
                
                fig_bottom = px.bar(
                    df_bottom5, x='jumlah_terjual', y='Nama_Produk', orientation='h',
                    labels={'jumlah_terjual': 'Total Terjual', 'Nama_Produk': 'Nama Produk'},
                    color='jumlah_terjual',color_continuous_scale=oranye_jenuh_custom
                )
                fig_bottom.update_layout(height=250, showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_bottom, use_container_width=True)

    # --- BARIS 4: ANALISIS JAM SIBUK (PEAK HOURS) 
    st.markdown("---")
    st.markdown("##### Analisis Waktu Transaksi Pemasukan Tertinggi")
    
    df_pemasukan_jam = df_filtered[df_filtered['type'] == 'pemasukan'].copy()
    
    if df_pemasukan_jam.empty:
        st.info("Tidak ada data pemasukan untuk dianalisis jam tertingginya.")
    else:
        df_pemasukan_jam['Jam'] = df_pemasukan_jam['waktu'].dt.hour
        df_hourly = df_pemasukan_jam.groupby('Jam')['nominal'].sum().reset_index()
        
        # Merge agar visualisasi runut dari jam 0 - 23 secara penuh
        all_hours = pd.DataFrame({'Jam': list(range(0, 24))})
        df_hourly = pd.merge(all_hours, df_hourly, on='Jam', how='left').fillna(0)
        
        jam_tertinggi = df_hourly.loc[df_hourly['nominal'].idxmax()]['Jam']
        pemasukan_maks = df_hourly['nominal'].max()
        
        col_jam_teks, col_jam_grafik = st.columns([1, 2])
        
        with col_jam_teks:
            with st.container(border=True):
                st.write("**Insight Jam Sibuk:**")
                st.write(f"Berdasarkan filter aktif, pemasukan tertinggi UMKM berada pada **Jam {int(jam_tertinggi):02d}:00**.")
                st.write(f"Total omset terkumpul pada jam tersebut mencapai **Rp {pemasukan_maks:,.0f}**.")
                
        with col_jam_grafik:
            fig_hourly = px.line(
                df_hourly, x='Jam', y='nominal',
                labels={'nominal': 'Total Pemasukan (Rp)', 'Jam': 'Jam Operasional'},
                markers=True
            )
            fig_hourly.update_traces(line_color="#644a6e", line_width=3)
            fig_hourly.update_layout(
                height=220, 
                xaxis=dict(tickmode='linear', tick0=0, dtick=2),
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

# Menampilkan Dataframe Terfilter di bagian paling bawah
    # st.markdown("---")
    st.divider()
    st.subheader(" Detail Transaksi Terfilter")
    
    #RENAME KOLOM UNTUK TAMPILAN TABEL ---
    df_tampilan = df_filtered.rename(columns={
        'id_transaksi': 'ID Transaksi',
        'waktu': 'Tanggal & Waktu',
        'Nama_Produk': 'Nama Produk',
        'kategori': 'Kategori',
        'type': 'Jenis Transaksi',
        'nominal': 'Nominal (Rp)'
    })
    
    # Tampilkan dataframe yang sudah di-rename kolomnya
    st.dataframe(df_tampilan, use_container_width=True)
