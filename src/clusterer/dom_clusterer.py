import os
import pickle
import shutil
from sklearn.cluster import KMeans

PROCESSED_DIR = "../../data/processed"
RAW_HTML_DIR = "../../data/raw_html"
CLUSTERED_OUTPUT_DIR = "../../data/clustered_pages"

# Jumlah cluster yang kita tebak (Homepage, List Artikel, Detail Artikel, Page Lain)
# Anda bisa mengubah angka ini jika hasil belum rapi
N_CLUSTERS = 4 

def run_clustering():
    # Load vectors
    vector_path = os.path.join(PROCESSED_DIR, "dom_vectors.pkl")
    if not os.path.exists(vector_path):
        print("[-] File vektor tidak ditemukan. Jalankan vectorizer dulu.")
        return

    with open(vector_path, 'rb') as f:
        filenames, vectors = pickle.load(f)

    print(f"[*] Melakukan clustering K-Means dengan {N_CLUSTERS} cluster...")
    
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    kmeans.fit(vectors)
    labels = kmeans.labels_
    # Simpan label cluster untuk visualisasi
    labels_path = os.path.join(PROCESSED_DIR, "cluster_labels.pkl")
    with open(labels_path, "wb") as f:
        pickle.dump(labels.tolist(), f)


    # Organisir file hasil cluster ke folder
    if os.path.exists(CLUSTERED_OUTPUT_DIR):
        shutil.rmtree(CLUSTERED_OUTPUT_DIR)
    os.makedirs(CLUSTERED_OUTPUT_DIR)

    print("[*] Mengelompokkan file...")
    
    # Menyimpan mapping untuk referensi nanti
    cluster_map = {}

    for filename, label in zip(filenames, labels):
        cluster_folder = os.path.join(CLUSTERED_OUTPUT_DIR, f"cluster_{label}")
        
        if not os.path.exists(cluster_folder):
            os.makedirs(cluster_folder)
        
        # Copy file asli ke folder cluster (agar user bisa inspect visual)
        src = os.path.join(RAW_HTML_DIR, filename)
        dst = os.path.join(cluster_folder, filename)
        shutil.copy2(src, dst)
        
        if label not in cluster_map:
            cluster_map[label] = 0
        cluster_map[label] += 1

    print("\n[+] Clustering Selesai! Statistik:")
    for label, count in sorted(cluster_map.items()):
        print(f"    Cluster {label}: {count} file")
    
    print(f"\nSilakan buka folder '{CLUSTERED_OUTPUT_DIR}' untuk melihat tipe halaman yang sudah dikelompokkan.")

if __name__ == "__main__":
    run_clustering()