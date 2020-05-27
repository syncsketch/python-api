# @Author: yafes
# @Date:   2018-11-20 17:36:16
# @Last Modified by:   Brady endres
# @Last Modified time: 2020-05-27 17:39:39

from setuptools import setup, find_packages

setup(name='syncsketch',
      version='1.0.7',
      description='SyncSketch Python API',
      author='Philip Floetotto',
      author_email='phil@syncsketch.com',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires=[
                'requests>=2.20.0',
            ],
      license='LICENSE.txt',
    )