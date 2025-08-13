#include <pybind11/pybind11.h>
#include <filesystem>
#include <iostream>
#include <cstdlib>
#include <string>
#include <fstream>
#include <sstream>
#include <iomanip>

namespace py = pybind11;
namespace fs = std::filesystem;

/**
 * get_cache_folder: None --> std::string
-- Gets the path of the cache folder based on the system
 * @param [out] cache_path (std::string) - Path to the cache folder
** Platform-specific cache folder determination
*/
std::string get_cache_folder() {
    fs::path myPath = "";
    #if defined(_WIN32) || defined(_WIN64)
        const char* localAppData = std::getenv("LOCALAPPDATA");
        if (localAppData) {
            myPath = std::string(localAppData) + "\\capgenie\\cache";
        } else {
            myPath = "C:\\Users\\Public\\capgenie\\cache";
        }
    #elif defined(__APPLE__) || defined(__MACH__)
        myPath = "~/Library/Caches/capgenie";
    #else
        // Linux and other Unix systems
        const char* xdg_cache = std::getenv("XDG_CACHE_HOME");
        if (xdg_cache) {
            myPath = std::string(xdg_cache) + "/capgenie";
        } else {
            const char* home = std::getenv("HOME");
            if (home) {
                myPath = std::string(home) + "/.cache/capgenie";
            } else {
                myPath = "/tmp/capgenie";
            }
        }
    #endif
        return myPath.string();
}

/**
 * clear_cache_folder: None --> void
-- Clears all capgenie cache
 * @param [out] None - No return value, clears cache folder contents
** Removes all contents from the cache folder
*/
void clear_cache_folder() {
    std::string cache_folder = get_cache_folder();
    if (fs::exists(cache_folder) && fs::is_directory(cache_folder)) {
        for (fs::directory_iterator it(cache_folder); it != fs::directory_iterator(); ++it) {
            fs::remove_all(it->path());
        }
    } else {
        std::cout << "You don't have any cache!" << std::endl;
    }
}

/**
 * formatBytes: std::streampos --> std::string
-- Takes a number of bytes and formats it into
-- a byte string, such as "10 MB" or "18.3 GB"
 * @param [in] pos (std::streampos) - Number of bytes to format
 * @param [out] formatted_string (std::string) - Formatted byte string with units
** Converts byte count to human-readable format
*/
std::string formatBytes(std::streampos pos) {
    const char* units[] = { "B", "KB", "MB", "GB", "TB"};
    double size = static_cast<double>(pos);
    int order = 0;

    while (size >= 1024 && order < 4) {
        size /= 1024;
        ++order;
    }

    std::ostringstream out;
    out << std::fixed << std::setprecision(order == 0 ? 0 : 2);
    out << size << " " << units[order];
    return out.str();
}

/**
 * fastqFileSize: std::string --> std::string
-- Gets the file size of the fastQ file based on
-- tellg().
 * @param [in] filePath (std::string&) - Path to the FASTQ file
 * @param [out] file_size (std::string) - Formatted file size string
** Returns formatted file size for FASTQ files
*/
std::string fastqFileSize(std::string &filePath) {
    std::ifstream file(filePath, std::ios::binary | std::ios::ate); // open at end
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filePath << std::endl;
        return "";
    }
    return formatBytes(file.tellg());
}

/**
 * fastqLineCount: std::string --> int
-- Gets the number of reads a FastQ file
-- has. (Only gives number of sequence lines)
 * @param [in] filename (const std::string&) - Path to the FASTQ file
 * @param [out] line_count (int) - Number of sequence reads in the file
** Counts the number of sequences in a FASTQ file
*/
int fastqLineCount(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filename << std::endl;
        return -1;
    }
    int lineCount = 0;
    std::string line;
    while (std::getline(file, line)) {
        ++lineCount;
    }
    return lineCount / 4; // For each DNA SEQ
}

/**
 * split_string: std::string_view, char --> std::vector<std::string>
-- Splits a string by a delimiter
 * @param [in] str (std::string_view) - String to split
 * @param [in] delimiter (char) - Delimiter character to split by
 * @param [out] tokens (std::vector<std::string>) - Vector of split substrings
** Splits a string into tokens based on delimiter
*/
std::vector<std::string> split_string(std::string_view str, char delimiter) {
    std::vector<std::string> tokens;
    size_t start = 0;

    while (start < str.size()) {
        size_t end = str.find(delimiter, start);
        if (end == std::string_view::npos) {
            end = str.size();
        }
        tokens.emplace_back(str.substr(start, end - start));
        start = end + 1;
    }

    return tokens;
}

/**
 * format_element: std::string, size_t --> std::string
-- Takes a string and pads it with whitespace to get
-- max_length.
 * @param [in] s (const std::string&) - String to format
 * @param [in] max_length (size_t) - Maximum length for formatting
 * @param [out] formatted_string (std::string) - Centered and padded string
** Centers and pads a string to specified length
*/
std::string format_element(const std::string& s, size_t max_length) {
    int empty_space = max_length - s.length();
    if (empty_space <= 0) {
        return " " + s.substr(0, max_length-3) + "... ";
    } else {
        size_t leftPadding = empty_space / 2;
        size_t rightPadding = empty_space - leftPadding;
        return " " + std::string(leftPadding, ' ') + s + std::string(rightPadding, ' ') + " ";
    }
}

/**
 * getMaxLength: std::vector<std::string> --> size_t
-- Returns the length of the biggest string in the vector.
 * @param [in] strings (const std::vector<std::string>&) - Vector of strings to check
 * @param [out] max_length (size_t) - Length of the longest string
** Finds the maximum length among strings in a vector
*/
size_t getMaxLength(const std::vector<std::string>& strings) {
    size_t maxLen = 0;
    for (const auto& s : strings) {
        if (s.length() > maxLen) {
            maxLen = s.length();
        }
    }
    return maxLen;
}

/**
 * pprint_csv: std::string --> void
-- Pretty prints a capsid csv file so that users can see
-- it in the command line terminal.
 * @param [in] filepath (const std::string&) - Path to the CSV file to print
 * @param [out] None - Prints formatted output to console
** Pretty prints a peptide CSV file in a table format
*/
void pprint_csv(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filepath << std::endl;
        return;
    }

    std::string line;
    std::vector<std::string> splitted_line;

    std::vector<std::string> peptides;
    std::vector<std::string> sequences;

    while (std::getline(file, line)) {
        if (line.empty()) continue;

        splitted_line = split_string(line, ',');
        if (splitted_line.size() < 2) {
            std::cerr << "Malformed line: " << line << std::endl;
            continue;
        }
        peptides.push_back(splitted_line[0]);
        sequences.push_back(splitted_line[1]);

    }

    int MAX_PEPTIDE = (getMaxLength(peptides) > 20) ? 20 : getMaxLength(peptides);
    int MAX_SEQUENCE = (getMaxLength(sequences) > 30) ? 30 : getMaxLength(sequences);

    std::string FIRST_ROW = "|" + format_element("Peptide", MAX_PEPTIDE) + "|" + 
        format_element("Sequence", MAX_SEQUENCE) + "|";

    std::string SEPERATOR(FIRST_ROW.length(), '-');

    std::cout << SEPERATOR << std::endl;
    std::cout << FIRST_ROW << std::endl;
    std::cout << SEPERATOR << std::endl;

    for (size_t i = 0; i < peptides.size(); ++i) {
        if (i > 6) {
            std::cout << "|" + format_element("..", MAX_PEPTIDE) + 
                "|" + format_element("....", MAX_SEQUENCE) + "|" << std::endl;
            break;
        }
        std::cout << "|" + format_element(peptides[i], MAX_PEPTIDE) + 
            "|" + format_element(sequences[i], MAX_SEQUENCE) + "|" << std::endl;
        std::cout << SEPERATOR << std::endl;
    }
}

PYBIND11_MODULE(mani, m) {
    m.doc() = "CapGenie utility functions for cache and file handling";

    m.def("get_cache_folder", &get_cache_folder, "Returns the cache folder path");
    m.def("clear_cache_folder", &clear_cache_folder, "Deletes contents of the cache folder");
    m.def("fastq_file_size", &fastqFileSize, "Returns the size of a FASTQ file in bytes");
    m.def("fastq_line_count", &fastqLineCount, "Returns the number of sequences in a FASTQ file");
    m.def("split_string", &split_string, "Splits a string by a given delimiter");
    m.def("format_element", &format_element, "Formats a string to be centered in a given width");
    m.def("pprint_csv", &pprint_csv, "Pretty prints a peptide CSV file");
}