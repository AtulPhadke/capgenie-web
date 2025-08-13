// Created by Atul Phadke, February 12th, 2025

// Platform-specific definitions
#ifdef __linux__
    #define _GNU_SOURCE
#endif
#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <fstream>
#include <mutex>
#include <filesystem>
#include <cstring>
#include <cstdint>
#include <pybind11/pybind11.h>
#include "platform_compat.h"

namespace py = pybind11;

#define NUM_THREADS 10  // Adjust based on CPU cores
int QUALITY_THRESHOLD = 30;  // Min average quality score to keep

std::mutex output_mutex;
std::atomic<long long> total_quality_sum(0);
std::atomic<size_t> total_chars(0);
std::atomic<size_t> low_quality_reads(0);
std::atomic<size_t> num_reads(0);
// Variables for storing read quality data

/**
 * joinPaths: const char*, const char* --> std::string
-- Joins two file paths and creates a new filename with "denoise_" prefix
 * @param [in] path1 (const char*) - First path component
 * @param [in] path2 (const char*) - Second path component
 * @param [out] final_path (std::string) - Combined path with denoise prefix
** Creates output filename with denoise prefix
*/
std::string joinPaths(const char* path1, const char* path2) {
    if (!path1) path1 = "";
    if (!path2) path2 = "";

    const char* filename = std::strrchr(path2, '/');
    const char* filenameAlt = std::strrchr(path2, '\\');

    if (filenameAlt && (!filename || filenameAlt > filename)) {
        filename = filenameAlt; 
    }

    std::string directory, filenameOnly;
    if (filename) {
        directory = std::string(path2, filename + 1); 
        filenameOnly = std::string(filename + 1);
    } else {
        directory = "";  // No directory, just filename
        filenameOnly = path2;
    }

    // Compute new filename with "denoise_" prefix
    std::string newFileName = "denoise_" + filenameOnly;
    std::string finalPath = std::string(path1) + "/" + directory + newFileName;

    return finalPath;
}

/**
 * process_chunk: const char*, size_t, size_t, std::ofstream& --> void
-- Processes a chunk of FASTQ data and filters reads based on quality threshold
 * @param [in] data (const char*) - Memory-mapped file data
 * @param [in] start (size_t) - Starting position in the data
 * @param [in] end (size_t) - Ending position in the data
 * @param [in/out] output (std::ofstream&) - Output file stream for high-quality reads
 * @param [out] None - Writes high-quality reads to output stream
** Processes FASTQ chunk and filters by quality score
*/
void process_chunk(const char* data, size_t start, size_t end, std::ofstream& output) {
    size_t i = start;
    std::string high_quality_reads = "";

    while (i < end) {
        // Read FASTQ entry
        size_t entry_start = i;
        std::string id_line, seq_line, plus_line, quality_line;
        
        if (i < end) while (i < end && data[i] != '\n') id_line += data[i++];
        i++;

        if (i < end) while (i < end && data[i] != '\n') seq_line += data[i++];
        i++;

        if (i < end) while (i < end && data[i] != '\n') plus_line += data[i++];
        i++;

        if (i < end) while (i < end && data[i] != '\n') quality_line += data[i++];
        i++;

        // Compute average quality score
        long long total_quality = 0;
        for (char q : quality_line) {
            total_quality += (q - 33);
        }
        double avg_quality = (quality_line.empty()) ? 0 : (double)total_quality / quality_line.size();
        total_quality_sum += total_quality;
        total_chars += quality_line.size();
        // If average quality is above threshold, store the entry
        if (avg_quality > QUALITY_THRESHOLD) {
            high_quality_reads += id_line + "\n" + seq_line + "\n" + plus_line + "\n" + quality_line + "\n";
        } else {
            low_quality_reads++;
        }
        num_reads++;
    }

    std::lock_guard<std::mutex> lock(output_mutex);
    output << high_quality_reads;

}

struct DenoiseResult {
    double avg_quality;
    int64_t total_chars;
    int64_t low_quality_reads;
    int64_t num_reads;
    int threshold;
    std::string output_filename;
};

/**
 * clear_pointers: None --> void
-- Clears global atomic variables for next function usage
 * @param [out] None - Resets global variables to zero
** Resets global counters for next denoise operation
*/
void clear_pointers() {
    //Clear for next function usage
    total_quality_sum = 0;
    total_chars = 0;
    low_quality_reads = 0;
    num_reads = 0;
}

/**
 * denoise: const char*, const char*, const char*, int --> DenoiseResult
-- Filters low-quality reads from a FASTQ file based on quality threshold
 * @param [in] filename (const char*) - Name of the output file
 * @param [in] file_path (const char*) - Path to the input FASTQ file
 * @param [in] output_path (const char*) - Path for output directory
 * @param [in] threshold (int) - Quality threshold for filtering
 * @param [out] result (DenoiseResult) - Statistics about the denoising process
** Main denoising function that filters FASTQ reads by quality
*/
DenoiseResult denoise(const char* filename, const char* file_path, const char* output_path, int threshold) {
    clear_pointers();
    std::string output_filename = joinPaths(output_path, filename);
    std::cout << file_path << std::endl;

    DenoiseResult result;

    QUALITY_THRESHOLD = threshold;

    int fd = open(file_path, O_RDONLY);
    if (fd < 0) {
        std::cerr << "Error opening file!\n";
        return result;
    }

    // Get file size
    stat_t sb;
    if (fstat(fd, &sb) == -1) {
        std::cerr << "Error getting file size!\n";
        fd_close(fd);
        return result;
    }
    size_t file_size = sb.st_size;
    char* data = (char*)mmap(nullptr, file_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (data == MAP_FAILED) {
        std::cerr << "Error memory-mapping file!\n";
        fd_close(fd);
        return result;
    }
    fd_close(fd);

    // Open output file

    std::ofstream output(output_filename, std::ios::out);
    if (!output.is_open()) {
        std::cerr << "Error opening output file!\n";
        munmap(data, file_size);
        return result;
    }

    // Determine chunk size for threads
    size_t chunk_size = file_size / NUM_THREADS;
    std::vector<std::thread> threads;

    for (int i = 0; i < NUM_THREADS; ++i) {
        size_t start = i * chunk_size;
        size_t end = (i == NUM_THREADS - 1) ? file_size : (i + 1) * chunk_size;

        while (start > 0 && data[start - 1] != '\n') start++;
        while (end < file_size && data[end] != '\n') end++;

        //run process_chunk for each chunk and connect it to mutex output
        
        threads.emplace_back(process_chunk, data, start, end, std::ref(output));
    }

    // Join threads
    for (auto& t : threads) {
        t.join();
    }
    output.close();
    munmap(data, file_size);

    double avg_quality_per_char = total_chars ? (double)total_quality_sum / total_chars : 0;
    std::cout << "Average quality of file: " << avg_quality_per_char << "\n";
    std::cout << "Number of reads below threshold: " << low_quality_reads << "\n";
    std::cout << "Percentage of low quality reads: " << ((double)low_quality_reads*100 / num_reads) << "\n";
    std::cout << "Filtered reads saved to " << output_filename << std::endl;
    
    result.low_quality_reads = low_quality_reads;
    result.total_chars = total_chars;
    result.avg_quality = avg_quality_per_char;
    result.num_reads = num_reads;
    result.threshold = QUALITY_THRESHOLD;
    result.output_filename = output_filename;
    clear_pointers();
    return result;
}

PYBIND11_MODULE(denoise, m) {
    m.doc() = "FASTQ denoising module using C++";
    py::class_<DenoiseResult>(m, "DenoiseResult")
        .def(py::init<>())
        .def_readwrite("avg_quality", &DenoiseResult::avg_quality)
        .def_readwrite("total_chars", &DenoiseResult::total_chars)
        .def_readwrite("num_reads", &DenoiseResult::num_reads)
        .def_readwrite("threshold", &DenoiseResult::threshold)
        .def_readwrite("output_filename", &DenoiseResult::output_filename)
        .def_readwrite("low_quality_reads", &DenoiseResult::low_quality_reads);

    m.def("denoise", &denoise, "Filter low-quality reads from a FASTQ file",
          py::arg("filename"), py::arg("file_path"), py::arg("output_path"), py::arg("threshold"));
}