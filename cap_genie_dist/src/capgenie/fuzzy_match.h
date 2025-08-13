#ifndef FUZZY_MATCH_H
#define FUZZY_MATCH_H

float hamming_distance(const std::string& s1, const std::string& s2);
int count_hamming_matches(const std::string& query, const std::string& dna_seq, int max_mismatches);
int peptide_levenshtein_distance(const std::string& s1, const std::string& s2);

#endif