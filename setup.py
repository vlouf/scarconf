# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="scarconf",
    version="1.1.0",
    description="S3car global parameters.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vlouf/scarconf",
    author="Valentin Louf",
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="radar weather meteorology correction",
    packages=find_packages(exclude=["notebook"]),
    install_requires=["pandas"],
    project_urls={"Source": "https://gitlab.bom.gov.au/radarcal/scarconf/",},
)
