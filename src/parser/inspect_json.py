import os
import json
import yaml
from bs4 import BeautifulSoup
from glob import glob

# --- KONFIGURASI ---
CLUSTERED_DIR = "../../data/clustered_pages"
CLUSTERS_TO_CHECK = ["cluster_0", "cluster_1"]

def print_keys(data, indent=0, max_depth=3):
    """Mencetak struktur dictionary secara rekursif"""
    if indent > max_depth:
        return

    spacing = "  " * indent
    if isinstance(data, dict):
        for key in data.keys():
            print(f"{spacing}- {key}")
            # Drill down ke kunci-kunci penting
            if key in ['props', 'pageProps', 'initialData', 'hotel', 'property', 'seoViewSearchList']:
                print_keys(data[key], indent + 1, max_depth)
    elif isinstance(data, list):
        if len(data) > 0:
            print(f"{spacing}- [List of {len(data)} items]")
            # Cek item pertama saja
            print_keys(data[0], indent + 1, max_depth)

def inspect_cluster():
    for cluster in CLUSTERS_TO_CHECK:
        print(f"\n{'='*40}")
        print(f"MEMERIKSA: {cluster}")
        print(f"{'='*40}")
        
        path = os.path.join(CLUSTERED_DIR, cluster)
        if not os.path.exists(path):
            print("Folder tidak ditemukan.")
            continue
            
        files = glob(os.path.join(path, "*.html"))
        if not files:
            print("Folder kosong.")
            continue
            
        # Ambil 1 file sampel
        sample_file = files[10]
        print(f"File Sampel: {os.path.basename(sample_file)}")
        
        try:
            with open(sample_file, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
                
            script = soup.find("script", {"id": "__NEXT_DATA__"})
            if not script:
                print("[-] Tag <script id='__NEXT_DATA__'> TIDAK DITEMUKAN!")
                continue
                
            json_data = json.loads(script.string)
            
            print("\n[STRUKTUR JSON UTAMA]:")
            print_keys(json_data)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    inspect_cluster()