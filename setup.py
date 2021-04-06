import setuptools
import os

here = os.path.abspath(os.path.dirname(__file__))

# description
with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()

# version
version = {}
with open(os.path.join(here, 'ccc', 'version.py')) as f:
    exec(f.read(), version)


setuptools.setup(
    name="cwb-ccc",
    version=version['__version__'],
    author="Philipp Heinrich",
    author_email="philipp.heinrich@fau.de",
    description="CWB wrapper to extract concordances and collocates",
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ausgerechnet/cwb-ccc",
    install_requires=[
        "association-measures>=0.1.5",
        "cwb-python>=0.2.2",
        "pandas>=1.0.0",
        "numexpr>=2.7.3",
        "Bottleneck>=1.3.2",
        "unidecode>=1.2.0",
        "pyyaml>=5.2.1"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Unix",
    ],
    python_requires='>=3.6',
)
