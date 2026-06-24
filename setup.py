# @Author: yafes
# @Date:   2018-11-20 17:36:16
# @Last Modified by:   Brady Endres
# @Last Modified time: 2025-07-07

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    readme_text = f.read()

setup(
    name="syncsketch",
    version="1.0.12.1",
    description="SyncSketch Python API",
    author="Philip Floetotto",
    author_email="phil@syncsketch.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        # BSD-3-Clause
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    python_requires=">=2.7, <3.15",
    long_description=readme_text,
    long_description_content_type="text/markdown",
    url="https://github.com/syncsketch/python-api",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=[
        'requests>=2.20.0,<2.28; python_version < "3.0"',
        'requests>=2.20.0; python_version >= "3.7" and python_version < "3.9"',
        'requests>=2.33.0; python_version >= "3.9"',
        'urllib3>=2.6.3; python_version >= "3.9"',
    ],
    extras_require={
        "test": [
            "pytest>=7.0,<10.0",
            "pytest-cov>=4.0",
            "responses>=0.20.0",
        ],
    },
    license="BSD-3-Clause",
)
