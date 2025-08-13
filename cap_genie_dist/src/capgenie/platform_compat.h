#pragma once

// Platform detection
#ifdef _WIN32
    #define PLATFORM_WINDOWS 1
#elif defined(__APPLE__)
    #define PLATFORM_MACOS 1
#elif defined(__linux__)
    #define PLATFORM_LINUX 1
#else
    #define PLATFORM_UNIX 1
#endif

#ifdef PLATFORM_WINDOWS
    // Windows-specific includes
    #include <windows.h>
    #include <io.h>
    #include <fcntl.h>
    #include <sys/stat.h>
    
    // Define MAP_FAILED before using it
    #define MAP_FAILED ((void*)-1)
    
    // Windows equivalents for Unix functions
    #define open _open
    #define read _read
    #define write _write
    #define lseek _lseek
    #define stat _stat
    #define fstat _fstat
    
    // Use a more specific name for file descriptor close to avoid conflicts
    inline int fd_close(int fd) { return _close(fd); }
    
    // Memory mapping on Windows
    #include <memoryapi.h>
    #define PROT_READ PAGE_READONLY
    #define MAP_PRIVATE FILE_MAP_COPY
    #define MAP_SHARED FILE_MAP_READ
    
    // Windows doesn't have mmap, so we'll use file mapping
    void* mmap(void* addr, size_t length, int prot, int flags, int fd, off_t offset) {
        HANDLE fileHandle = (HANDLE)_get_osfhandle(fd);
        if (fileHandle == INVALID_HANDLE_VALUE) {
            return MAP_FAILED;
        }
        
        HANDLE mappingHandle = CreateFileMapping(fileHandle, NULL, PAGE_READONLY, 0, 0, NULL);
        if (mappingHandle == NULL) {
            return MAP_FAILED;
        }
        
        void* mappedData = MapViewOfFile(mappingHandle, FILE_MAP_READ, 0, offset, length);
        CloseHandle(mappingHandle);
        
        return mappedData ? mappedData : MAP_FAILED;
    }
    
    int munmap(void* addr, size_t length) {
        return UnmapViewOfFile(addr) ? 0 : -1;
    }
    
#else
    // Unix/Linux/macOS includes
    #include <sys/mman.h>
    #include <sys/stat.h>
    #include <sys/types.h>
    #include <fcntl.h>
    #include <unistd.h>
    
    // Linux-specific includes
    #ifdef PLATFORM_LINUX
        #include <features.h>
    #endif
    
    // macOS-specific includes
    #ifdef PLATFORM_MACOS
        #include <TargetConditionals.h>
    #endif
    
    // Unix file descriptor close function
    inline int fd_close(int fd) { return close(fd); }
#endif

#include <string>
#include <vector>
#include <unordered_map>

// Cross-platform stat type definition
#ifdef PLATFORM_WINDOWS
    typedef struct _stat64i32 stat_t;
#else
    typedef struct stat stat_t;
#endif

// Platform-specific constants and macros
#ifndef MAP_FAILED
    #define MAP_FAILED ((void*)-1)
#endif

// Ensure off_t is available on all platforms
#include <sys/types.h> 