// Created by Atul Phadke in April 2025
// Belongs to capgenie package and USES parallel processing

#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <thread>
#include <mutex>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <edlib.h>
#include <algorithm>

namespace py = pybind11;

/**
 * hamming_distance: std::string, std::string --> int
-- Calculates the hamming distance between two strings
-- in the fastest way possible.
 * @param [in] s1 (std::string) - First string to compare
 * @param [in] s2 (std::string) - Second string to compare
 * @param [out] distance (int) - Hamming distance between the strings
** Simple Hamming distance calculate
*/
int hamming_distance(const std::string& s1, const std::string& s2) {
    if (s1.length() != s2.length()) {
        throw std::invalid_argument("Strings must be the same length");
    }
    int distance = 0;
    for (size_t i = 0; i < s1.length(); i++) {
        if (s1[i] != s2[i]) {
            distance++;
        }
    }
    return distance;
}

/**
 * peptide_levenshtein_distance: std::string, std::string --> int
-- Calculates the Levenshtein distance between two strings using
-- dynamic programming approach for reference implementation.
 * @param [in] s1 (std::string) - First string to compare
 * @param [in] s2 (std::string) - Second string to compare
 * @param [out] distance (int) - Levenshtein distance between the strings
** Native Levenshtein distance calculation without EDLIB
*/
int peptide_levenshtein_distance(const std::string& s1, const std::string& s2) {
    size_t len1 = s1.size();
    size_t len2 = s2.size();

    std::vector<std::vector<int>> dp(len1 + 1, std::vector<int>(len2 + 1));

    for (size_t i = 0; i <= len1; ++i) {
        for (size_t j = 0; j <= len2; ++j) {
            if (i == 0) {
                dp[i][j] = j; // insert all of s2
            } else if (j == 0) {
                dp[i][j] = i; // remove all of s1
            } else if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1]; // no operation
            } else {
                dp[i][j] = 1 + std::min({
                    dp[i - 1][j],     // deletion
                    dp[i][j - 1],     // insertion
                    dp[i - 1][j - 1]  // substitution
                });
            }
        }
    }

    return dp[len1][len2];
}

/**
 * count_hamming_matches: std::string, std::string, int --> int
-- Counts all fuzzy matches (only substitutions) in the dna_seq string
-- and returns the number of matches where it is <= max_mismatches.
 * @param [in] query (std::string) - Query sequence to search for
 * @param [in] dna_seq (std::string) - DNA sequence to search in
 * @param [in] max_mismatches (int) - Maximum number of allowed mismatches
 * @param [out] match_count (int) - Number of matches found
** This is for only substitutions
*/
int count_hamming_matches(const std::string& query, const std::string& dna_seq, int max_mismatches) {
    const size_t qlen = query.length();
    const size_t dlen = dna_seq.length();
    if (qlen > dlen) return 0;

    int match_count = 0;
    std::mutex mtx;
    size_t num_threads = std::thread::hardware_concurrency();
    std::vector<std::thread> threads;

    auto worker = [&](size_t start, size_t end) {
        int local_count = 0;
        for (size_t i = start; i < end; ++i) {
            int mismatches = 0;
            for (size_t j = 0; j < qlen; ++j) {
                if (dna_seq[i + j] != query[j]) {
                    ++mismatches;
                    if (mismatches > max_mismatches) break;
                }
            }
            if (mismatches <= max_mismatches)
                ++local_count;
        }
        std::lock_guard<std::mutex> lock(mtx);
        match_count += local_count;
    };

    size_t total = dlen - qlen + 1;
    size_t chunk = (total + num_threads - 1) / num_threads;

    for (size_t t = 0; t < num_threads; ++t) {
        size_t start = t * chunk;
        size_t end = std::min(start + chunk, total);
        if (start >= end) break;
        threads.emplace_back(worker, start, end);
    }

    for (auto& th : threads) th.join();
    return match_count;
}

/**
 * levenshtein_match_count_thread: std::string, std::string, int, size_t, size_t --> int
-- Returns the total number of levenshtein matches where it has less than
max_mismatches. Uses EDLIB and is a thread helper for count_levenshtein_matches.
counts for only a part of the string.
 * @param [in] query (std::string) - Query sequence to search for
 * @param [in] dna (std::string) - DNA sequence to search in
 * @param [in] max_distance (int) - Maximum allowed edit distance
 * @param [in] start (size_t) - Starting position in the DNA sequence
 * @param [in] end (size_t) - Ending position in the DNA sequence
 * @param [out] count (int) - Number of matches found in this chunk
** Forked from EDLIB docs
*/
int levenshtein_match_count_thread(const std::string& query, const std::string& dna, int max_distance, size_t start, size_t end) {
    int count = 0;
    int qlen = query.size();
    for (size_t i = start; i <= end - qlen; ++i) {
        const char* window = dna.data() + i;
        EdlibAlignResult result = edlibAlign(
            query.c_str(), qlen,
            window, qlen,
            edlibNewAlignConfig(max_distance, EDLIB_MODE_NW, EDLIB_TASK_DISTANCE, nullptr, 0)
        );

        if (result.editDistance != -1 && result.editDistance <= max_distance) {
            ++count;
        }

        edlibFreeAlignResult(result);
    }
    return count;
}
/**
 * count_levenstein_matches: std::string, std::string, int --> int
-- Parent function for levenshtein_match_count_thread that splits dna_seq into
chunks and parallel processes levenshtein_match_count_thread.
 * @param [in] query (std::string) - Query sequence to search for
 * @param [in] dna_seq (std::string) - DNA sequence to search in
 * @param [in] max_distance (int) - Maximum allowed edit distance
 * @param [out] total_count (int) - Total number of matches found across all chunks
** This is for substitutions + indels.
*/
int count_levenstein_matches(const std::string& query, const std::string& dna_seq, int max_distance) {
    int total_count = 0;
    std::vector<std::thread> threads;
    int num_threads = 5;
    std::vector<int> thread_counts(num_threads, 0);

    size_t qlen = query.size();
    size_t dlen = dna_seq.size();
    size_t chunk_size = (dlen - qlen + 1) / num_threads;

    for (int t = 0; t < num_threads; ++t) {
        size_t start = t * chunk_size;
        size_t end = (t == num_threads - 1) ? (dlen - qlen) : (start + chunk_size - 1);

        threads.emplace_back([&, t, start, end]() {
            thread_counts[t] = levenshtein_match_count_thread(query, dna_seq, max_distance, start, end);
        });
    }

    for (auto& th : threads) {
        th.join();
    }

    for (int c : thread_counts) {
        total_count += c;
    }

    return total_count;
}
/**
 * fuzzy_match: std::vector<std::string>, std::string, int, bool --> std::unordered_map<std::string, int>
-- Finds all the fuzzy matches of all queries in dna_seq. Has two modes,
substitutions w/o indels, that are dictated by the boolean subOnly.
 * @param [in] queries (std::vector<std::string>&) - Vector of query sequences to search for
 * @param [in] dna_seq (std::string) - DNA sequence to search in
 * @param [in] max_mismatch (int) - Maximum number of allowed mismatches
 * @param [in] subOnly (bool) - If true, only allow substitutions; if false, allow indels too
 * @param [out] counts (std::unordered_map<std::string, int>) - Map of query sequences to their match counts
** Function that is exported to PYBIND11
*/
std::unordered_map<std::string, int> fuzzy_match(std::vector<std::string>& queries, const std::string& dna_seq, int max_mismatch, bool subOnly) {
    std::unordered_map<std::string, int> counts;

    for (const auto& query : queries) {
        if (subOnly) {
            counts[query] = count_hamming_matches(query, dna_seq, max_mismatch);
        } else {
            counts[query] = count_levenstein_matches(query, dna_seq, max_mismatch);
        }
    }
    return counts;
}

PYBIND11_MODULE(fuzzy_match, m) {
    m.doc() = "FASTQ fuzzy matching using C++";
    m.def("fuzzy_match", &fuzzy_match, "Fuzzy matches with sub/sub+indels",
        py::arg("queries"), py::arg("dna_seq"), py::arg("max_mismatch"), py::arg("subOnly"));
    m.def("peptide_levenshtein_distance", &peptide_levenshtein_distance, "Native Levenshtein",
    py::arg("s1"), py::arg("s2"));
}