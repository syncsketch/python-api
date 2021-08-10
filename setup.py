# @Author: yafes
# @Date:   2018-11-20 17:36:16
# @Last Modified by:   Brady Endres
# @Last Modified time: 2021-08-10

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    readme_text = f.read()

setup(
    name="syncsketch",
    version="1.0.8.8",
    description="SyncSketch Python API",
    author="Philip Floetotto",
    author_email="phil@syncsketch.com",
    long_description=readme_text,
    long_description_content_type="text/markdown",
    url="https://github.com/syncsketch/python-api",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=["requests>=2.20.0"],
    license="LICENSE.txt",
)
