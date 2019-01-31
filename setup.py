# @Author: yafes
# @Date:   2018-11-20 17:36:16
# @Last Modified by:   yafes
# @Last Modified time: 2018-11-20 17:39:39

from setuptools import setup, find_packages

setup(name='syncsketch',
      version='0.0.1',
      description='Syncsketch Shared Package.',
      author='Flo',
      author_email='flo@test.com',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires=[
                'requests>=2.20.0',
            ],
      license='LICENSE.txt',
    )