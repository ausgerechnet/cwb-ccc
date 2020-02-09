import setuptools
from os import path


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md')) as fh:
    long_description = fh.read()


setuptools.setup(
    name="cwb-ccc",
    version="0.9.6",
    author="Philipp Heinrich",
    author_email="philipp.heinrich@fau.de",
    description="CWB wrapper to extract concordances and collocates",
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.cs.fau.de/pheinrich/ccc",
    install_requires=[
        "pandas>=0.24.2",
        "cwb-python>=0.2.2",
        "association-measures>=0.1.3"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
