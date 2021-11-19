from setuptools import find_packages
from distutils.core import setup, Extension
from pathlib import Path
import os

here = os.path.abspath(os.path.dirname(__file__))

# description
with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()

# version
version = {}
with open(os.path.join(here, 'ccc', 'version.py')) as f:
    exec(f.read(), version)


# CL directory for C-extension
def guess_cl_directory():

    # ... fallback
    cwb_dirs = ["/usr/local/include/"]

    # ... take from environment variable
    if 'CWB_DIR' in os.environ:
        cwb_dirs += os.environ['CWB_DIR']

    # ... guess according to CQP location
    cqp_location = os.popen('which cqp').read().rstrip()
    if cqp_location != "":
        cwb_dirs += [os.path.join(Path(cqp_location).parents[1], 'include')]

    return cwb_dirs


# define (and compile) C-extension
# try:
#     from Cython.Build import cythonize
#     USE_CYTHON = True
# except ImportError:
USE_CYTHON = False              # use cython -2 ccc/cl.pyx instead

ext = '.pyx' if USE_CYTHON else '.c'

extensions = [
    Extension(
        name="ccc.cl",
        sources=['ccc/cl' + ext],
        libraries=['cl', 'pcre', 'glib-2.0'],
        library_dirs=guess_cl_directory()
    )
]

if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)


setup(
    name="cwb-ccc",
    version=version['__version__'],
    author="Philipp Heinrich",
    author_email="philipp.heinrich@fau.de",
    description="CWB wrapper to extract concordances and score frequency lists",
    packages=find_packages(exclude=["tests", "test_*"]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ausgerechnet/cwb-ccc",
    ext_modules=extensions,
    install_requires=[
        "association-measures>=0.1.6",
        "pandas>=1.2.0",
        "numexpr>=2.7.1",
        "Bottleneck>=1.3.2",
        "unidecode>=1.1.1",
        "pyyaml>=5.4.1"
    ],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Cython',
    ],
    python_requires='>=3.6.1',
)
