import numpy as np
from sklearn.cluster import DBSCAN
import umap.umap_ as umap
from collections import defaultdict, Counter
import math
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import logomaker
from dataclasses import dataclass
import os
import json

## JUST FOR TEMPLATE
@dataclass
class MotifScore:
    position: int
    aa: str
    freq: float
    score: float

class Motif:
    def __init__(self, seqs, isProtein=True):
        self.seqs = seqs # List of any sequences
        self.isProtein = isProtein
        if self.isProtein:
            self.aa_list = 'ACDEFGHIKLMNPQRSTVWY'
        else:
            self.aa_list = 'ACGT'
        self.aa_to_index = {aa: i for i, aa in enumerate(self.aa_list)}

    """
    one_hot_encode: str --> np.ndarray
    -- Converts a sequence to one-hot encoded representation
    * @param [in] seq (str) - Input sequence to encode
    * @param [out] one_hot (np.ndarray) - One-hot encoded sequence
    ** Converts sequence to flattened one-hot encoding
    """
    def one_hot_encode(self, seq):
        length = len(seq)
        depth = len(self.aa_list)
        one_hot = np.zeros((length, depth))
        for i, aa in enumerate(seq):
            if aa in self.aa_to_index:
                one_hot[i, self.aa_to_index[aa]] = 1
        return one_hot.flatten()

    """
    cluster_motifs: None --> defaultdict
    -- Clusters sequences using UMAP dimensionality reduction and DBSCAN
    * @param [out] clusters (defaultdict) - Dictionary of cluster labels to sequences
    ** Uses UMAP and DBSCAN to cluster similar sequences
    """
    def cluster_motifs(self):
        #if self.isProtein:
        encoded_seqs = np.array([self.one_hot_encode(seq) for seq in self.seqs])
        reducer = umap.UMAP(n_neighbors=5, min_dist=0.3, random_state=42)
        reduced = reducer.fit_transform(encoded_seqs)

        db = DBSCAN(eps=0.5, min_samples=2)
        labels = db.fit_predict(reduced)

        clusters = defaultdict(list)
        for seq, label in zip(self.seqs, labels):
            print(type(seq), type(label))
            if label != -1:  # skip noise
                clusters[label].append(seq)

        return clusters
    
    """
    extract_wildcard_motifs: list, int, int, int, int --> dict
    -- Extracts wildcard motifs from cluster sequences
    * @param [in] cluster_seqs (list) - List of sequences in cluster
    * @param [in] min_len (int) - Minimum motif length
    * @param [in] max_len (int) - Maximum motif length
    * @param [in] max_wildcards (int) - Maximum number of wildcards
    * @param [in] min_count (int) - Minimum count threshold
    * @param [out] motifs (dict) - Dictionary of motifs to counts
    ** Extracts motifs with wildcards from sequence clusters
    """
    def extract_wildcard_motifs(self, cluster_seqs, min_len=3, max_len=7, max_wildcards=2, min_count=2):
        motif_counter = Counter()
        for seq in cluster_seqs:
            for length in range(min_len, max_len + 1):
                for i in range(len(seq) - length + 1):
                    window = seq[i:i+length]
                    
                    wildcard_positions = [
                        format(idx, f"0{length}b")
                        for idx in range(2**length)
                        if 0 < bin(idx).count('1') <= max_wildcards
                    ]

                    for pattern in wildcard_positions:
                        motif = ''.join(
                            window[j] if pattern[j] == '0' else 'X'
                            for j in range(length)
                        )
                        motif_counter[motif] += 1

                    motif_counter[window] += 1
        return {str(motif): int(count) for motif, count in motif_counter.items() if count >= min_count}
    
    """
    get_motifs: str --> None
    -- Gets motifs from clustered sequences and saves to JSON
    * @param [in] file_path (str) - Path to save motifs JSON file
    * @param [out] None - Saves motifs to motifs.json file
    ** Processes clusters and saves motifs to file
    """
    def get_motifs(self, file_path):
        clusters = self.cluster_motifs()
        motifClusters = {}
        for label, cluster_seqs in clusters.items():
            motifs = self.extract_wildcard_motifs(cluster_seqs)
            sorted_motifs = sorted(motifs.items(), key=lambda x: -x[1])
            motifClusters[int(label)] = sorted_motifs

        with open(os.path.join(file_path, "motifs.json"), 'w') as f:
            json.dump(motifClusters, f, indent=4)

    """
    compute_frequencies: None --> list
    -- Computes frequency of each character at each position
    * @param [out] freqs (list) - List of frequency dictionaries for each position
    ** Calculates position-wise character frequencies
    """
    def compute_frequencies(self):
        L = len(self.seqs[0])
        freqs = [defaultdict(float) for _ in range(L)]
        for seq in self.seqs:
            for i in range(L):
                freqs[i][seq[i]] += 1.0

        for pos_freq in freqs:
            for k in pos_freq:
                pos_freq[k] /= len(self.seqs)
        return freqs

    """
    compute_info_content: list --> list
    -- Computes information content at each position
    * @param [in] freqs (list) - List of frequency dictionaries
    * @param [out] info (list) - List of information content scores
    ** Calculates information content using entropy
    """
    def compute_info_content(self, freqs):
        info = []
        alphabet_size = len(self.aa_list)
        max_entropy = math.log2(alphabet_size)
        for pos_freq in freqs:
            entropy = 0.0
            for p in pos_freq.values():
                if p > 0:
                    entropy -= p * math.log2(p)
            info.append(max_entropy - entropy)
        return info

    """
    createMotifLogo: str --> None
    -- Creates and saves a motif logo visualization
    * @param [in] file_path (str) - Path to save the motif logo
    * @param [out] None - Saves motif logo plot to file
    ** Creates sequence logo visualization using logomaker
    """
    def createMotifLogo(self, file_path):
        freqs = self.compute_frequencies()
        infoScores = self.compute_info_content(freqs)

        AMINO_ACIDS = self.aa_list

        scores = []

        for idx, val in enumerate(freqs):
            for aa in AMINO_ACIDS:
                f = val.get(aa, 0.0)
                s = f * infoScores[idx]
                
                if s > 0.001:
                    scores.append([idx, aa, f, s])

        logo_df = pd.DataFrame(scores, columns=["position", "aa", "freq", "score"])

        print(logo_df)

        logo_df = logo_df.pivot_table(index='position', columns='aa', values='score', fill_value=0.0)
        logo_df = logo_df.sort_index()

        # COLOR SCHEME FROM CHATGPT
        if self.isProtein:
            color_scheme = {
                'A': 'gray', 'V': 'gray', 'L': 'gray', 'I': 'gray', 'M': 'gray',  # hydrophobic
                'F': 'green', 'Y': 'green', 'W': 'green',  # aromatic
                'S': 'blue', 'T': 'blue', 'N': 'blue', 'Q': 'blue',  # polar
                'D': 'red', 'E': 'red',  # acidic
                'K': 'purple', 'R': 'purple', 'H': 'purple',  # basic
                'C': 'gold', 'G': 'orange', 'P': 'pink'  # special cases
            }
        else:
            color_scheme = {
                'A': 'green',
                'C': 'blue',
                'G': 'orange',
                'T': 'red'
            }

        fig, ax = plt.subplots(figsize=(10, 6))

        logo = logomaker.Logo(
            logo_df,
            color_scheme=color_scheme,
            font_name='Arial Rounded MT Bold',
            ax=ax
        )

        ax.set_xlabel("Position")
        ax.set_ylabel("Motif Score")
        plt.tight_layout()
        plt.savefig(os.path.join(file_path, "motif_logo.png"), dpi=300)