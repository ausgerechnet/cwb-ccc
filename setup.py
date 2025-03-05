#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shlex
import subprocess

from setuptools import Extension, setup

# try:
#     from Cython.Build import cythonize
#     USE_CYTHON = True
# except ImportError:
USE_CYTHON = False              # use cython -2 ccc/cl.pyx instead


########################
# read local resources #
########################

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), mode='rt', encoding='utf-8') as f:
    long_description = f.read()

version = {}
with open(os.path.join(here, 'ccc', 'version.py'), mode='rt', encoding='utf-8') as f:
    exec(f.read(), version)

with open(os.path.join(here, 'requirements.txt'), mode='rt', encoding='utf-8') as f:
    install_requires = f.read().strip().split("\n")

print(install_requires)


##############
# cwb-config #
##############

# - version
cwb_version = subprocess.run(shlex.split("cwb-config -v"), capture_output=True).stdout.decode().strip()
# - cqp binaries
cwb_bindir = subprocess.run(shlex.split("cwb-config --bindir"), capture_output=True).stdout.decode().strip()
# - effective registry directory or directories:
cwb_registry = subprocess.run(shlex.split("cwb-config -r"), capture_output=True).stdout.decode().strip()
# - libdir (CL library)
cwb_libdir = subprocess.run(shlex.split("cwb-config --libdir"), capture_output=True).stdout.decode().strip()
# - incdir (C header)
cwb_incdir = subprocess.run(shlex.split("cwb-config --incdir"), capture_output=True).stdout.decode().strip()
# - compiler flags for linking against CL library
cwb_compiler_flags = subprocess.run(shlex.split("cwb-config -I"), capture_output=True).stdout.decode().strip()
# - linker flags for linking against CL library
cwb_linker_flags = subprocess.run(shlex.split("cwb-config -L"), capture_output=True).stdout.decode().strip()


####################################
# define (and compile) C-extension #
####################################

# ensure compatibility with CWB v3.4.36 and below
if int(cwb_version.split(".")[0]) == 3 and int(cwb_version.split(".")[1]) == 4 and int(cwb_version.split(".")[2]) < 37:
    cwb_linker_flags = "-L/usr/local/lib -lcl  -lm   -lpcre -lglib-2.0"

# define include directories, library directories, and library names
libraries = [t[2:] for t in shlex.split(cwb_linker_flags) if t.startswith("-l")]
inc_dirs = [cwb_incdir] + [t[2:] for t in shlex.split(cwb_compiler_flags) if t.startswith("-I")]
lib_dirs = [cwb_libdir] + [t[2:] for t in shlex.split(cwb_linker_flags) if t.startswith("-L")]

ccc_cl = Extension(
    name="ccc.cl",
    sources=['ccc/cl' + ('.pyx' if USE_CYTHON else '.c')],
    include_dirs=inc_dirs,  # list of directories to search for C/C++ header files
    library_dirs=lib_dirs,  # list of directories to search for C/C++ libraries at link time
    libraries=libraries     # list of library names (not filenames or paths) to link against
)

# cythonize?
extensions = [ccc_cl]
if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)


#################
# actual set-up #
#################
setup(
    name="cwb-ccc",
    version=version["__version__"],
    description="CWB wrapper to extract concordances and score frequency lists",
    license='GNU General Public License v3 or later (GPLv3+)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Philipp Heinrich",
    author_email="philipp.heinrich@fau.de",
    url="https://github.com/ausgerechnet/cwb-ccc",
    packages=[
        'ccc'
    ],
    ext_modules=extensions,
    python_requires='>=3.8.0',
    install_requires=install_requires,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Development Status :: 4 - Beta",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Cython'
    ],
)
