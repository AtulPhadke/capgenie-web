// Created by Atul Phadke on March 11th, 2025
// Code is confidential and can't be shared with anyone outside of the author's discretion.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <fstream>
#include <iostream>
#include "platform_compat.h"

namespace py = pybind11;

struct FilterResult {
    std::vector<std::string> forward_reads;
    std::vector<std::string> reverse_reads;
    std::vector<std::string> junk_reads;
    std::vector<std::string> null_reads;
    std::vector<std::string> aav9_reads;
    std::string dircheck = "fwd";
    int total_reads = 0;
    int reverse_count = 0;
    int null_count = 0;
};

FilterResult result;


/**
 * makeTranslationMap: std::string, std::string --> std::unordered_map<char, char>
-- Makes a map of two strings with each other character by character.
 * @param [in] from (const std::string&) - Source string for translation mapping
 * @param [in] to (const std::string&) - Target string for translation mapping
 * @param [out] translationMap (std::unordered_map<char, char>) - Character-by-character mapping
** Creates a translation map between two strings
*/
std::unordered_map<char, char> makeTranslationMap(const std::string& from, const std::string& to) {
    std::unordered_map<char, char> translationMap;
    
    // Assuming the from and to strings have the same length
    for (size_t i = 0; i < from.size(); ++i) {
        translationMap[from[i]] = to[i];
    }
    
    return translationMap;
}

// Function to translate a string (similar to translate method in Python)
std::string translateString(const std::string& input, const std::unordered_map<char, char>& translationMap) {
    std::string translated = input;
    
    for (char& c : translated) {
        if (translationMap.find(c) != translationMap.end()) {
            c = translationMap.at(c);
        }
    }
    
    return translated;
}

/**
 * safe_substring: std::string, size_t, size_t --> std::string
-- Wrapper for std::string.substr that checks bounds and avoids
segmentation faults
 * @param [in] str (const std::string&) - The input string
 * @param [in] start (size_t) - The starting index
 * @param [in] end (size_t) - The ending index
 * @param [out] substring (std::string) - The extracted substring
** Safe substring extraction with bounds checking
*/
std::string safe_substring(const std::string& str, size_t start, size_t end) {
    if (start >= str.size()) {
        return "";  // Return an empty string if start is out of bounds
    }

    if (end > str.size()) {
        end = str.size();
    }

    if (start > end) {
        return "";  // Return an empty string if the start is greater than end
    }

    return str.substr(start, end - start);
}

std::unordered_map<char, char> translationMap = makeTranslationMap("ACGT", "TGCA"); // reverse complement


/** 
process_line: std::string, std::string --> void
-- Processes a line in the file and grabs AAV9 forward and reverse reads
and saves it to the FilterCount result.
 * @param [in] line (std::string) - The current line from the file
 * @param [in] ref_seq (std::string) - The reference sequence
*/
void process_line(std::string line, std::string ref_seq) {
    result.dircheck = "fwd";
    if (line.find("GTGCTTCATTCCAAACCCTC") != std::string::npos) {
        result.reverse_count++;
    }

    if (line.find("TGCCCAA") != std::string::npos) {

    } else if (line.find("CCTGTG") != std::string::npos) {
        std::reverse(line.begin(), line.end());
        line = translateString(line, translationMap);
        result.dircheck = "rev";
    } else {
        result.null_reads.push_back(line);
        result.null_count++;
        result.junk_reads.push_back(line);
        return;
    }

    if (line.find("CCAAGCAC") != std::string::npos || line.find("GTGCTTGG") != std::string::npos) {
        result.aav9_reads.push_back(line);
        return;
    }

    auto mer = [&line](int x) -> int {
        return line.find("TGCCCAA") + x;
    };
    auto ref_mer = [&ref_seq](int x) -> int {
        return ref_seq.find("TGCCCAA") + x;
    };

    if ((safe_substring(line, mer(28), mer(32))) == "GCAC") {
        
        int upstream_mismatches = 0;
        int downstream_mismatches = 0;

        for (int i = 0; i < mer(-1); i++) {
            size_t line_pos = mer(-1 * i);
            size_t ref_pos = ref_mer(-1 * i);
            if (line_pos != std::string::npos && ref_pos != std::string::npos) {
                if (line[line_pos] != ref_seq[ref_pos]) {
                    upstream_mismatches++;
                }
            } else {
                break; // Stop if indices are invalid
            }
        }

        // Prevent out-of-bounds access when calculating downstream mismatches
        for (int i = 28; i < -1*mer(0 - line.length()); i++) {
            size_t line_pos = mer(i);
            size_t ref_pos = ref_mer(i - 21);
            if (line_pos != std::string::npos && ref_pos != std::string::npos) {
                if (line[line_pos] != ref_seq[ref_pos]) {
                    downstream_mismatches++;
                }
            } else {
                break; // Stop if indices are invalid
            }
        }

        if (upstream_mismatches <= 4) {
            try {
                if (downstream_mismatches <= 4) {
                    if (result.dircheck == "fwd") {
                        result.forward_reads.push_back(safe_substring(line, mer(7), mer(28)));
                    } else {
                        result.reverse_reads.push_back(safe_substring(line, mer(7), mer(28)));
                    }
                }
            } catch (...) {
                std::cerr << "Error in processing line." << std::endl;
            }
        } else {
            result.junk_reads.push_back(line);
        }
    }
    return;
}

/**
reset_result: FilterResult --> void
-- Resets all result pointers after file 
has been processed
 * @param [in] result (FilterResult&) - The result struct to reset
*/
void reset_result(FilterResult& result) {
    result.forward_reads.clear();
    result.reverse_reads.clear();
    result.junk_reads.clear();
    result.null_reads.clear();
    result.aav9_reads.clear();
    result.dircheck = "fwd";
    result.total_reads = 0;
    result.reverse_count = 0;
    result.null_count = 0;
}


/**
reset_pointers: char*&, char*& --> void
-- Resets all pointers after file has been processed
 * @param [in] mapped_data (char*&) - The mapped data pointer
 * @param [in] line_start (char*&) - The start of the current line
 * @param [in] current_pos (char*&) - The current position in the file
*/
void reset_pointers(char*& mapped_data, char*& line_start, char*& current_pos) {
    mapped_data = nullptr;
    line_start = nullptr;
    current_pos = nullptr;
}

/**
filter_count: char*, char* --> FilterResult
-- Runs process_line over the FastQ file and returns FilterResult
 * @param [in] file (const char*) - The path to the FastQ file
 * @param [in] refseq (char*) - The reference sequence
 * @param [out] result (FilterResult) - The result struct to populate
*/
FilterResult filter_count(const char* file, char* refseq) {
    reset_result(result);

    int fd = open(file, O_RDONLY);
    if (fd == -1) {
        std::cerr << "Error opening file." << std::endl;
        return result;
    }

    stat_t file_stat;
    if (fstat(fd, &file_stat) == -1) {
        std::cerr << "Error getting file size." << std::endl;
        fd_close(fd);
        return result;
    }
    size_t file_size = file_stat.st_size;

    char* mapped_data = (char*)mmap(nullptr, file_size, PROT_READ, MAP_PRIVATE, fd, 0);
    fd_close(fd); // File descriptor can be closed after mmap

    if (mapped_data == MAP_FAILED) {
        std::cerr << "Error mapping file." << std::endl;
        return result;
    }

    char* current_pos = mapped_data;
    char* line_start = mapped_data;
    char* end_pos = mapped_data + file_size;

    int line_number = 0;

    while (current_pos < end_pos) {
        if (*current_pos == '\n') {
            if ((line_number + 3) % 4 == 0) {
                result.total_reads++;
                std::string line(line_start, current_pos - line_start);
                process_line(line, refseq);
            }
            line_start = current_pos + 1;
            if ((line_number) % 1000000 == 0) {
                std::cout << line_number << std::endl;
            }
            line_number++;
        }
        current_pos++;
    }
        // Handle the last line if it doesn't end with a newline
    if (current_pos == end_pos && *line_start != '\n') {
        if ((line_number + 3) % 4 == 0) {
            std::string line(line_start, end_pos - line_start);
            process_line(line, refseq);
        }
        return result;
    }

    if (munmap(mapped_data, file_size) == -1) {
        std::cerr << "Error unmapping file." << std::endl;
        return result;
    }

    std::cout << result.forward_reads.size() << std::endl;
    std::cout << result.reverse_reads.size() << std::endl;
    std::cout << result.junk_reads.size() << std::endl;
    std::cout << result.aav9_reads.size() << std::endl;

    reset_pointers(mapped_data, line_start, current_pos);

    return result;
}

//implementation of PYBIND_11 module for filter_module
PYBIND11_MODULE(filter_module, m) {
    py::class_<FilterResult>(m, "FilterResult")
        .def(py::init<>())
        .def_readwrite("forward_reads", &FilterResult::forward_reads)
        .def_readwrite("reverse_reads", &FilterResult::reverse_reads)
        .def_readwrite("junk_reads", &FilterResult::junk_reads)
        .def_readwrite("null_reads", &FilterResult::null_reads)
        .def_readwrite("aav9_reads", &FilterResult::aav9_reads)
        .def_readwrite("dircheck", &FilterResult::dircheck)
        .def_readwrite("total_reads", &FilterResult::total_reads)
        .def_readwrite("reverse_count", &FilterResult::reverse_count)
        .def_readwrite("null_count", &FilterResult::null_count);

    m.def("filter_count", &filter_count, "Filter reads from file",
          py::arg("file"), py::arg("refseq"));
}