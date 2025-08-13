from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import sysconfig
import platform
import os
import subprocess

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path, based on the python version"""
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

class CustomBuildExt(build_ext):
    """Custom build command to handle platform-specific compilation"""
    
    def build_extension(self, ext):
        # Set platform-specific compiler options
        if platform.system() == "Windows":
            # Ensure we're using the right compiler on Windows
            if not hasattr(self.compiler, 'compiler_so'):
                self.compiler.compiler_so = ['cl.exe']
            if not hasattr(self.compiler, 'compiler_cxx'):
                self.compiler.compiler_cxx = ['cl.exe']
            
            # Add Windows-specific defines for better compatibility
            if not hasattr(ext, 'define_macros'):
                ext.define_macros = []
            ext.define_macros.extend([
                ('_WIN32_WINNT', '0x0601'),
                ('WIN32_LEAN_AND_MEAN', None),
                ('_CRT_SECURE_NO_WARNINGS', None),
                ('PYTHON_DLL_NAME', 'python312.dll'),  # Explicitly specify Python DLL
            ])
        
        super().build_extension(ext)

def l_requirements(filename):
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def get_platform_flags():
    """Get platform-specific compilation and linking flags"""
    system = platform.system()
    python_libdir = sysconfig.get_config_var("LIBDIR")
    
    print(f"Detected platform: {system}")
    
    if system == "Darwin":  # macOS
        compile_args = ["-std=c++17", "-mmacosx-version-min=10.15"]
        link_args = [f"-L{python_libdir}"] if python_libdir else []
        print(f"macOS flags: compile={compile_args}, link={link_args}")
    elif system == "Windows":  # Windows
        # Windows-specific compilation flags - use MD for dynamic linking (better for PyInstaller)
        compile_args = ["/std:c++17", "/EHsc", "/MD", "/D_CRT_SECURE_NO_WARNINGS", "/D_WIN32_WINNT=0x0601", "/DWIN32_LEAN_AND_MEAN"]
        link_args = []
        if python_libdir:
            link_args.append(f"/LIBPATH:{python_libdir}")
        print(f"Windows flags: compile={compile_args}, link={link_args}")
    else:  # Linux and other Unix-like systems
        compile_args = ["-std=c++17"]
        link_args = [f"-L{python_libdir}"] if python_libdir else []
        print(f"Linux flags: compile={compile_args}, link={link_args}")
    
    return compile_args, link_args

# Get platform-specific flags
compile_args, link_args = get_platform_flags()

# Define the extension modules
ext_modules = [
    Extension(
        "capgenie.filter_module",
        ["src/capgenie/filter_count.cpp"],
        include_dirs=[
            str(get_pybind_include()),
            str(get_pybind_include(user=True)),
            "src/capgenie",
        ],
        extra_link_args=link_args,
        language="c++",
        extra_compile_args=compile_args,
    ),
    Extension(
        "capgenie.denoise",
        ["src/capgenie/denoise.cpp"],
        include_dirs=[
            str(get_pybind_include()),
            str(get_pybind_include(user=True)),
            "src/capgenie",
        ],
        extra_link_args=link_args,
        language="c++",
        extra_compile_args=compile_args,
    ),
    Extension(
        "capgenie.mani",
        ["src/capgenie/mani.cpp"],
        include_dirs=[
            str(get_pybind_include()),
            str(get_pybind_include(user=True)),
            "src/capgenie",
        ],
        extra_link_args=link_args,
        language="c++",
        extra_compile_args=compile_args,
    ),
    Extension(
        "capgenie.fuzzy_match",
        ["src/capgenie/fuzzy_match.cpp", "src/capgenie/edlib/edlib.cpp"],
        include_dirs=[
            str(get_pybind_include()),
            str(get_pybind_include(user=True)),
            "src/capgenie/edlib",
        ],
        extra_link_args=link_args,
        language="c++",
        extra_compile_args=compile_args,
    ),
]

setup(
    name="capgenie",
    version="0.1",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CustomBuildExt},
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    # Remove install_requires and entry_points to avoid conflicts with pyproject.toml
)
