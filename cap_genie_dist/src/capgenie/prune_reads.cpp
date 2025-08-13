#include <string>
#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <map>
#include <set>
#include <translate.h>
#include <fuzzy_match.h>

namespace py = pybind11;

/**
 * prune_reads: int, std::map<std::string, int> --> std::map<std::string, int>
-- Prunes reads that are very similar with each other.
 * @param [in] THRESHOLD (int) - Hamming distance threshold for pruning
 * @param [in] merlist (std::map<std::string, int>&) - Map of sequences and their counts
 * @param [out] pruned_merlist (std::map<std::string, int>) - Pruned map of sequences
** Hamming distance threshold is 0.2
*/
std::map<std::string, int> prune_reads(const int THRESHOLD, std::map<std::string, int>& merlist) {
    int num_of_mers = merlist.length();

    std::set<string> highfreq_raws;
    std::set<string> highfreq_translated;
    std::string translated_var;
    std::set<string> delset;
    
    std::for_each(merlist.begin(), merlist.end(), [](const auto& pair)){
        if (pair.second / num_of_mers) {
            translated_var = translate(pair.first);
            if (highfreq_translated.find(translated_var) == highfreq_translated.end()) {
                highfreq_raws.add(pair.first);
                highfreq_translated.add(translated_var);
            }
        } else {break;}
    }

    for (std::string x : highfreq_raws) {
        for (std::string y : merlist) {
            if ((y == x) || (highfreq_raws.find(y) != std::string::npos)) {
                continue;
            }
            if (0 < (hamming_distance(x, y) / x.length()) < 0.2) {
                merlist[x] = merlist[x] + merlist[y];
            }
        }
    }
    for (std::string item : delset) {merlist.erase(item);}

    return merlist;
}