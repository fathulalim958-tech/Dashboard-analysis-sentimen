import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard PKKMB", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("Sentimen_Cleaned.csv") 
    if 'Submitted on' in df.columns:
        df['Submitted on'] = pd.to_datetime(df['Submitted on'])
        df['tanggal'] = df['Submitted on'].dt.date
    return df

def get_top_keywords(data, num=5):
    if not data.empty:
        words = " ".join(data.astype(str)).lower().split()
        return Counter(words).most_common(num)
    return []

def generate_wordcloud(data, title, color):
    if not data.empty and data.str.strip().any():
        text = " ".join(review for review in data.astype(str))
        wordcloud = WordCloud(width=800, height=400, background_color='white', 
                            colormap=color, max_words=100).generate(text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

try:
    df = load_data()
    
    # --- SIDEBAR: KONTROL ---
    st.sidebar.header("Pusat Analisis")
    st.sidebar.subheader("Filter Data")
    min_date = df['tanggal'].min()
    max_date = df['tanggal'].max()
    start_date, end_date = st.sidebar.date_input("Rentang Tanggal", value=(min_date, max_date))
    
    all_sentiments = df['Sentimen'].unique().tolist()
    selected_sentiments = st.sidebar.multiselect("Kategori Sentimen", options=all_sentiments, default=all_sentiments)
    
    mask = (df['tanggal'] >= start_date) & (df['tanggal'] <= end_date) & (df['Sentimen'].isin(selected_sentiments))
    df_filtered = df.loc[mask].copy()

    # --- MAIN PAGE: JUDUL & METRIK ---
    st.title("Dashboard Analisis Sentimen Terhadap Layanan PKKMB")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    counts = df_filtered['Sentimen'].value_counts()
    
    col_m1.metric("Total Responden", len(df_filtered))
    col_m2.metric("Sentimen Positif", counts.get('positif', 0))
    col_m3.metric("Sentimen Netral", counts.get('netral', 0))
    col_m4.metric("Sentimen Negatif", counts.get('negatif', 0))

    st.divider()

    # --- BAGIAN 2: TREN FEEDBACK ---
    st.subheader("Tren Feedback Pengisian PKKMB")
    trend_total = df_filtered.groupby('tanggal').size().reset_index(name='jumlah')
    fig_tt, ax_tt = plt.subplots(figsize=(12, 4))
    sns.lineplot(data=trend_total, x='tanggal', y='jumlah', marker='o', ax=ax_tt)
    plt.xticks(rotation=45)
    st.pyplot(fig_tt)

    st.divider()

    # --- BAGIAN 3: DISTRIBUSI SENTIMEN ---
    st.subheader("Visualisasi Distribusi Sentimen") 
    c1, c2 = st.columns(2)
    color_map = {'positif': '#2ecc71', 'netral': '#f1c40f', 'negatif': '#e74c3c'}

    with c1:
        st.write("**Persentase Sentimen (Pie Chart)**")
        if not df_filtered.empty:
            pie_data = df_filtered['Sentimen'].value_counts()
            colors_pie = [color_map.get(label, '#333') for label in pie_data.index]
            fig_p, ax_p = plt.subplots(figsize=(7, 5))
            ax_p.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140, colors=colors_pie, textprops={'fontweight': 'bold'})
            ax_p.axis('equal') 
            st.pyplot(fig_p)

    with c2:
        st.write("**Jumlah Sentimen (Bar Chart)**")
        if not df_filtered.empty:
            fig_b, ax_b = plt.subplots(figsize=(7, 5))
            sns.countplot(data=df_filtered, x='Sentimen', palette=color_map, order=['positif', 'netral', 'negatif'], ax=ax_b)
            plt.ylabel("Jumlah")
            st.pyplot(fig_b)

    # --- BAGIAN 4: ANALISIS KATA KUNCI UTAMA ---
    st.divider()
    st.subheader("Analisis Kata Kunci Utama")
    tab1, tab2, tab3 = st.tabs(["Positif", "Netral", "Negatif"])
    
    with tab1:
        data_pos = df_filtered[df_filtered['Sentimen'] == 'positif']['Kritik dan saran']
        generate_wordcloud(data_pos, "Positif", "summer")
        st.markdown("**Top 5 Kata Kunci Positif:**")
        cols = st.columns(5)
        for i, (word, count) in enumerate(get_top_keywords(data_pos)):
            cols[i].success(f"**{word}** ({count})")

    with tab2:
        data_net = df_filtered[df_filtered['Sentimen'] == 'netral']['Kritik dan saran']
        generate_wordcloud(data_net, "Netral", "Wistia")
        st.markdown("**Top 5 Kata Kunci Netral:**")
        cols = st.columns(5)
        for i, (word, count) in enumerate(get_top_keywords(data_net)):
            cols[i].warning(f"**{word}** ({count})")

    with tab3:
        data_neg = df_filtered[df_filtered['Sentimen'] == 'negatif']['Kritik dan saran']
        generate_wordcloud(data_neg, "Negatif", "autumn")
        st.markdown("**Top 5 Kata Kunci Negatif:**")
        cols = st.columns(5)
        for i, (word, count) in enumerate(get_top_keywords(data_neg)):
            cols[i].error(f"**{word}** ({count})")

    # --- BAGIAN 5: A/B TESTING ---
    st.divider()
    st.subheader("🧪 A/B Testing: Persentase Positif Berdasarkan Panjang Komentar")
    
    rate_a, rate_b = 0, 0
    if not df_filtered.empty:
        df_filtered['jumlah_kata'] = df_filtered['Kritik dan saran'].astype(str).apply(lambda x: len(x.split()))
        threshold = 10
        df_a = df_filtered[df_filtered['jumlah_kata'] <= threshold]
        df_b = df_filtered[df_filtered['jumlah_kata'] > threshold]

        if len(df_a) > 0 and len(df_b) > 0:
            rate_a = (len(df_a[df_a['Sentimen'] == 'positif']) / len(df_a)) * 100
            rate_b = (len(df_b[df_b['Sentimen'] == 'positif']) / len(df_b)) * 100
            
            fig_ab, ax_ab = plt.subplots(figsize=(10, 4))
            bars = ax_ab.bar(['Komentar Pendek', 'Komentar Panjang'], [rate_a, rate_b], color=['#3498db', '#9b59b6'])
            ax_ab.set_ylabel('Persentase Positif (%)')
            ax_ab.set_ylim(0, 115)
            for bar in bars:
                yval = bar.get_height()
                ax_ab.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.1f}%', ha='center', fontweight='bold')
            st.pyplot(fig_ab)

    # --- BAGIAN 6: GLOBAL INSIGHTS (EKSEKUTIF SUMMARY) ---
    st.divider()
    st.header("Kesimpulan Strategis (Executive Summary)")
    if not df_filtered.empty:
        ins_col1, ins_col2 = st.columns(2)
        with ins_col1:
            dom_sent = df_filtered['Sentimen'].value_counts().idxmax()
            st.info(f"**Ringkasan Performa:**\nSentimen dominan adalah **{dom_sent.upper()}**. Hal ini mencerminkan persepsi umum mahasiswa terhadap pelaksanaan PKKMB pada periode yang dipilih.")
        with ins_col2:
            status_ab = "mendukung" if rate_b > rate_a else "tidak mendukung"
            st.success(f"**Analisis Perilaku:**\nKomentar panjang memiliki tingkat positif **{rate_b:.1f}%**. Hasil ini {status_ab} hipotesis bisnis nomor 2 pada penelitian Anda.")

    # --- BAGIAN 7: DETAIL TABEL & DOWNLOAD ---
    st.divider()
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("Detail Kritik dan Saran")
    with col_t2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Data CSV", data=csv_data, file_name='data_pkkmb_cleaned.csv', mime='text/csv')

    search = st.text_input("🔍 Cari kata kunci di tabel:", "")
    df_t = df_filtered.copy()
    if search:
        df_t = df_t[df_t['Kritik dan saran'].str.contains(search, case=False, na=False)]
    st.dataframe(df_t[['Submitted on', 'Kritik dan saran', 'Sentimen']], use_container_width=True)

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")