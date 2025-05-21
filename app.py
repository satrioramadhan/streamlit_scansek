import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from collections import Counter
import re
import nltk

# Unduh stopwords
nltk.download('stopwords')

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard ScanSek", layout="wide")

# Koneksi ke MongoDB
client = MongoClient('mongodb://streamlit:beritakita123@164.92.109.4:27017/scrap?authSource=scrap')
db = client['scrap']
collection = db['daftar_berita']

# Ambil data dari MongoDB
data = list(collection.find())
df = pd.DataFrame(data)

# Pastikan kolom 'category' ada, jika belum isi dengan NaN
if 'category' not in df.columns:
    df['category'] = None

# Judul Aplikasi
st.markdown("""
    <h1 style='text-align: center; color: #007acc;'>📊 Dashboard Berita Kesehatan</h1>
    <p style='text-align: center;'>Visualisasi hasil scraping dari berbagai sumber berita bertema kesehatan.</p>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔍 Filter & Info")
    st.markdown(f"Total Artikel: **{len(df)}**")

    # Filter berdasarkan sumber berita
    sumber_unik = df['source'].dropna().unique()
    sumber_filter = st.multiselect("Pilih sumber berita:", sumber_unik, default=sumber_unik)

    # Search judul
    search_query = st.text_input("Cari judul artikel...")

    # Filter berdasarkan kategori (jika tersedia)
    kategori_unik = df['category'].dropna().unique()
    kategori_filter = st.multiselect("Pilih kategori:", kategori_unik, default=kategori_unik)

# Filter data berdasarkan pilihan
filtered_df = df[df['source'].isin(sumber_filter)]

if search_query:
    filtered_df = filtered_df[filtered_df['judul'].str.contains(search_query, case=False, na=False)]

if kategori_filter:
    filtered_df = filtered_df[filtered_df['category'].isin(kategori_filter)]

# Visualisasi 1: Jumlah Artikel per Sumber
st.subheader("📈 Jumlah Artikel per Sumber Berita")
fig1, ax1 = plt.subplots(figsize=(10, 5))
filtered_df['source'].value_counts().plot(kind='bar', ax=ax1, color='#4da6ff')
ax1.set_xlabel('Sumber Berita')
ax1.set_ylabel('Jumlah Artikel')
plt.xticks(rotation=45)
st.pyplot(fig1)

# Visualisasi 2: Word Cloud dari Judul Artikel
st.subheader("☁️ Word Cloud dari Judul Artikel")

text = ' '.join(filtered_df['judul'].fillna('').tolist()).lower()

custom_stopwords = set(STOPWORDS)
custom_stopwords.update([
    'apa', 'cara', 'bikin', 'kenali', 'gejala', 'lagi', 'foto', 'ajak', 'tidak',
    'bareng', 'dalam', 'setelah', 'sering', 'tips', 'kamu', 'kota', 'jam',
    'banyak', 'turis', 'viral', 'potret', 'untuk', 'dari', 'yang', 'dan',
    'dengan', 'pada', 'akan', 'juga', 'saat', 'itu', 'ini', 'sebagai', 'tak',
    'oleh', 'di', 'ke', 'ada', 'karena', 'agar', 'jadi', 'lebih', 'mari', 'anak', 'hari', 'bisa', 'tahun', 'hingga', 'muda', 'tua',
    'robby', 'purba', 'miss', 'dedi', 'mulyadi', 'rcti', 'eps', 'ala',
    'dunia', 'daftar', 'kisah', 'serial', 'series', 'ungkap', 'fakta', 'tapi',
    'mana', 'melihat', 'netizen', 'video', 'cukup', 'paling', 'langsung',
    'perlu', 'masih', 'muncul', 'indonesia', 'bulan', 'orang', 'sehat', 'diri', 'negara', 'rumah',
    'bayar', 'dokter', 'rambut', 'cantik', 'penumpang', 'pesawat',
    'ayam', 'jakarta', 'bandung', 'saudi', 'china', 'juta', 'meil', 'mei',
    'pagi', 'kembali', 'alami', 'selama', 'ikut', 'perempuan', 'pria', 'beli',
    'baru', 'lama', 'cepat', 'terus', 'guna', 'buat', 'salah', 'cuma', 'terbaik',
    'pentingnya', 'vision', 'langit', 'terjadi', 'naik', 'masa', 'hanya'
])

wordcloud = WordCloud(
    width=1000, height=400, background_color='white', stopwords=custom_stopwords
).generate(text)

fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.imshow(wordcloud, interpolation='bilinear')
ax2.axis('off')
st.pyplot(fig2)

# Visualisasi 3: 5 Kata Trending dari Judul Berita
st.subheader("🔥 5 Kata Trending dari Judul Berita")

words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
filtered_words = [word for word in words if word not in custom_stopwords]

counter = Counter(filtered_words)
top_5 = counter.most_common(5)

if top_5:
    trending_df = pd.DataFrame(top_5, columns=["Kata", "Frekuensi"])
    fig_trend, ax_trend = plt.subplots()
    ax_trend.bar(trending_df["Kata"], trending_df["Frekuensi"], color='salmon')
    ax_trend.set_title("5 Kata Paling Trending")
    st.pyplot(fig_trend)
else:
    st.info("Tidak ada kata trending yang bisa ditampilkan.")

# Visualisasi 4: Daftar Berita dengan Pagination
st.subheader("📰 Daftar Berita Kesehatan")

berita_per_halaman = 9
total_berita = len(filtered_df)
total_halaman = (total_berita - 1) // berita_per_halaman + 1

if 'halaman' not in st.session_state:
    st.session_state.halaman = 1

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Sebelumnya") and st.session_state.halaman > 1:
        st.session_state.halaman -= 1
with col3:
    if st.button("➡️ Selanjutnya") and st.session_state.halaman < total_halaman:
        st.session_state.halaman += 1

start_idx = (st.session_state.halaman - 1) * berita_per_halaman
end_idx = start_idx + berita_per_halaman
page_data = filtered_df.iloc[start_idx:end_idx]

cols = st.columns(3)
for idx, (_, row) in enumerate(page_data.iterrows()):
    with cols[idx % 3]:
        st.markdown(f"""
        <div style='border: 1px solid #ccc; border-radius: 12px; padding: 15px; margin-bottom: 15px; background-color: #f9f9f9;'>
            <h4 style='margin-bottom: 10px;'>{row.get('judul', '-')}</h4>
            <p style='font-size: 14px; color: #555;'>{row.get('description', '-')[:100]}...</p>
            <a href='{row.get('link', '#')}' target='_blank'>🔗 Baca selengkapnya</a>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center;'>Halaman {st.session_state.halaman} dari {total_halaman}</p>", unsafe_allow_html=True)
