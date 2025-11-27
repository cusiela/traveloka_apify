import os
import pickle
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer

# Konfigurasi Path
RAW_HTML_DIR = "../../data/raw_html"
PROCESSED_DIR = "../../data/processed"

def extract_dom_features(html_content):
    """
    Mengubah HTML menjadi string representasi struktur.
    Kita mengambil nama tag dan class-nya, mengabaikan teks konten.
    Contoh: "html body div.container div.header ul li a ..."
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Hapus script dan style karena sering berubah dinamis dan mengganggu clustering
        for script in soup(["script", "style"]):
            script.extract()

        dom_tokens = []
        for tag in soup.find_all():
            # Ambil nama tag (misal: div, a, span)
            token = tag.name
            
            # Ambil class jika ada (sebagai pembeda struktur spesifik)
            if tag.get('class'):
                classes = ".".join(tag.get('class'))
                token += f".{classes}"
            
            dom_tokens.append(token)
            
        return " ".join(dom_tokens)
    except Exception as e:
        return ""

def run_vectorization():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    data = []
    files = [f for f in os.listdir(RAW_HTML_DIR) if f.endswith(".html")]
    
    print(f"[*] Memulai ekstraksi fitur dari {len(files)} file...")

    for filename in files:
        filepath = os.path.join(RAW_HTML_DIR, filename)
        with open(filepath, 'rb') as f:
            content = f.read()
            features = extract_dom_features(content)
            if features:
                data.append({
                    "filename": filename,
                    "features": features
                })

    df = pd.DataFrame(data)
    
    # Vektorisasi menggunakan TF-IDF
    # Ini mengubah string "div div span" menjadi matriks angka
    vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    vectors = vectorizer.fit_transform(df['features'])

    # Simpan hasil untuk tahap clustering
    output_path = os.path.join(PROCESSED_DIR, "dom_vectors.pkl")
    with open(output_path, 'wb') as f:
        pickle.dump((df['filename'], vectors), f)
    
    print(f"[+] Vektorisasi selesai. Disimpan di {output_path}")

if __name__ == "__main__":
    run_vectorization()