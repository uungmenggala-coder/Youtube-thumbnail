import streamlit as st
import openai
import replicate
import requests
from PIL import Image
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="YouTube Viral Maker", layout="wide", page_icon="🔥")

# --- CSS CUSTOM UNTUK TAMPILAN LEBIH MODERN ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF0000;
        color: white;
        border-radius: 10px;
    }
    .title-box {
        padding: 15px;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #FF0000;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 YouTube Viral Studio")
st.markdown("Generasikan ide konten, pilih judul clickbait, dan buat thumbnail wajah Anda dalam satu alur kerja.")

# --- SIDEBAR: MANAJEMEN KUNCI API ---
with st.sidebar:
    st.header("🔑 Kunci Akses (API Keys)")
    st.info("Untuk menjalankan fitur AI, masukkan kunci di bawah atau atur di Streamlit Secrets.")
    
    # Cek apakah kunci ada di Streamlit Secrets (untuk keamanan saat deploy)
    # Jika tidak ada, minta input manual dari user
    if "OPENAI_API_KEY" in st.secrets:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ OpenAI Key Terdeteksi")
    else:
        openai_api_key = st.text_input("OpenAI API Key (GPT-4)", type="password")

    if "REPLICATE_API_TOKEN" in st.secrets:
        replicate_api_key = st.secrets["REPLICATE_API_TOKEN"]
        st.success("✅ Replicate Key Terdeteksi")
    else:
        replicate_api_key = st.text_input("Replicate API Key (Image/Face)", type="password")
    
    st.markdown("---")
    st.markdown("**Panduan:**")
    st.markdown("1. Masukkan Topik")
    st.markdown("2. Pilih Judul")
    st.markdown("3. Upload Wajah & Generate")

# --- FUNGSI UTAMA ---

def generate_titles_gpt(topic, api_key):
    if not api_key:
        return ["Error: API Key OpenAI belum dimasukkan."]
    
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    Bertindaklah sebagai ahli YouTube profesional.
    Buatlah 20 judul YouTube yang viral, menarik rasa ingin tahu (clickbait tapi jujur), 
    dan emosional untuk topik: '{topic}'.
    Format output: Hanya daftar judul polos dipisahkan baris baru, tanpa nomor.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4", # Bisa diganti gpt-3.5-turbo jika ingin hemat
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        titles = [line.strip() for line in content.split('\n') if line.strip()]
        return titles[:20]
    except Exception as e:
        return [f"Error: {str(e)}"]

def generate_real_thumbnail(title, user_image_bytes, api_key):
    """
    Fungsi ini menggunakan Replicate (InstantID) untuk membuat gambar asli
    dengan wajah user. Membutuhkan biaya kredit di Replicate.
    """
    if not api_key:
        return None, "API Key Replicate tidak ditemukan."

    # Setup client
    client = replicate.Client(api_token=api_key)
    
    # Prompt untuk gambar
    prompt_img = f"Youtube thumbnail for '{title}', hyper-realistic, 8k, detailed face, dramatic lighting, vibrant colors, shallow depth of field, looking at camera, expressive."

    try:
        # Menggunakan model InstantID (bagus untuk face preservation)
        # Note: Model version bisa berubah, ini contoh ID model populer untuk face swap/generation
        output = client.run(
            "wangfuyun/instantid:xxxx_versi_terbaru_xxxx", # Placeholder, biasanya otomatis diambil library jika pakai model slug yang benar
            input={
                "image": user_image_bytes,
                "prompt": prompt_img,
                "negative_prompt": "ugly, deformed, text, watermark, low quality",
                "width": 1280,
                "height": 720
            }
        )
        return output[0], None # Mengembalikan URL gambar hasil
    except Exception as e:
        # Fallback simulasi jika model error/habis kredit
        return None, str(e)

# --- LOGIKA APLIKASI (STATE MANAGEMENT) ---
if 'titles' not in st.session_state:
    st.session_state.titles = []

# --- HALAMAN 1: GENERATOR JUDUL ---
st.subheader("1. Tentukan Topik Video")
col_input, col_btn = st.columns([3, 1])
with col_input:
    topic = st.text_input("Tentang apa video ini?", placeholder="Cth: Cara masak nasi goreng enak, Review iPhone 15...")
with col_btn:
    st.write("") # Spacer
    st.write("") # Spacer
    gen_btn = st.button("🚀 Buat Judul")

if gen_btn and topic:
    with st.spinner("Sedang meracik judul viral..."):
        st.session_state.titles = generate_titles_gpt(topic, openai_api_key)

# --- HALAMAN 2: PEMILIHAN JUDUL ---
selected_title = None
if st.session_state.titles:
    st.divider()
    st.subheader("2. Pilih Judul Pemenang")
    
    # Jika ada error dari OpenAI
    if "Error" in st.session_state.titles[0]:
        st.error(st.session_state.titles[0])
    else:
        selected_title = st.selectbox("Pilih satu judul dari 20 ide:", st.session_state.titles)
        if selected_title:
            st.info(f"Judul Terpilih: **{selected_title}**")

# --- HALAMAN 3: GENERATOR THUMBNAIL (FACE SWAP) ---
if selected_title:
    st.divider()
    st.subheader("3. Buat Thumbnail (Face Swap)")
    st.caption("Upload foto wajah close-up yang jelas untuk hasil terbaik.")

    uploaded_file = st.file_uploader("Upload Foto Wajah Anda", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        col_preview, col_result = st.columns(2)
        
        with col_preview:
            st.image(uploaded_file, caption="Wajah Sumber", width=200)
            generate_thumb = st.button("✨ Generate Thumbnail Ajaib")

        if generate_thumb:
            with col_result:
                # Cek mode: Jika ada Replicate Key jalankan Real AI, jika tidak jalankan Mockup
                if replicate_api_key:
                    with st.spinner("Sedang menggambar ulang wajah Anda ke dalam thumbnail (Proses ~30 detik)..."):
                        # Karena ini kode demo, saya akan men-bypass pemanggilan API asli agar tidak crash
                        # jika Anda belum punya model ID yang spesifik.
                        # Di kode asli, Anda uncomment baris di bawah ini:
                        
                        # image_url, error = generate_real_thumbnail(selected_title, uploaded_file, replicate_api_key)
                        
                        # --- UNTUK DEMO, KITA PAKAI LOGIKA MOCKUP TAPI SEOLAH-OLAH ASLI ---
                        st.warning("⚠️ Mode Demo (Tanpa GPU): Menampilkan konsep.")
                        st.image("https://via.placeholder.com/1280x720.png?text=AI+Thumbnail+Generated", caption="Hasil (Mockup)")
                        st.success("Untuk hasil wajah asli, sambungkan ke model 'InstantID' di Replicate.")
                else:
                    # Mode Simulasi Total
                    st.warning("Anda belum memasukkan Replicate API Key. Menampilkan gambar contoh.")
                    st.image("https://via.placeholder.com/1280x720.png?text=Thumbnail+Preview", caption="Thumbnail Placeholder")
                    st.markdown(f"**Prompt Gambar:** Thumbnail YouTube untuk '{selected_title}', wajah ekspresif, 4K.")

st.markdown("---")
st.caption("Dibuat dengan Streamlit & OpenAI.")