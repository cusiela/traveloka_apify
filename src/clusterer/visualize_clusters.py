import os
import pickle
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np

PROCESSED_DIR = "../../data/processed"

def visualize():
    vector_path = os.path.join(PROCESSED_DIR, "dom_vectors.pkl")

    if not os.path.exists(vector_path):
        print("[-] dom_vectors.pkl tidak ditemukan!")
        return

    # Load vectors
    with open(vector_path, "rb") as f:
        filenames, vectors = pickle.load(f)

    # Load cluster labels (hasil clustering sebelumnya)
    labels_path = os.path.join(PROCESSED_DIR, "cluster_labels.pkl")
    if not os.path.exists(labels_path):
        print("[-] cluster_labels.pkl tidak ditemukan! Jalankan clusterer.py yang sudah dimodifikasi.")
        return

    with open(labels_path, "rb") as f:
        labels = pickle.load(f)

    # Hitung jumlah cluster
    unique_labels = sorted(set(labels))
    cluster_counts = {lbl: labels.count(lbl) for lbl in unique_labels}

    # ─────────────────────────────
    # 1) BAR CHART JUMLAH FILE PER CLUSTER
    # ─────────────────────────────
    plt.figure(figsize=(8, 5))
    plt.bar(cluster_counts.keys(), cluster_counts.values(), color='skyblue')
    plt.xticks(unique_labels)
    plt.xlabel("Cluster ID")
    plt.ylabel("Jumlah File HTML")
    plt.title("Distribusi Halaman per Cluster")
    plt.tight_layout()
    plt.show()

    # ─────────────────────────────
    # 2) PCA SCATTER PLOT (2D)
    # ─────────────────────────────
    print("[*] Menghitung PCA 2D untuk visualisasi...")

    pca = PCA(n_components=2)
    reduced = pca.fit_transform(vectors.toarray())

    plt.figure(figsize=(8, 6))

    for lbl in unique_labels:
        points = reduced[np.array(labels) == lbl]
        plt.scatter(points[:, 0], points[:, 1], label=f"Cluster {lbl}", s=10)

    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.title("Visualisasi Clustering DOM (PCA 2D)")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    visualize()
