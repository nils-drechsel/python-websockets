#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 10:15:23 2020

@author: nils
"""


import setuptools
from PackageVersion import get_git_version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="WebSocketServer",
    version=get_git_version(),
    author="Nils J. D. Drechsel",
    author_email="nils.drechsel@gmail.com",
    description="Extension of websockets to allow easier usage and rooms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nils-drechsel/python-websockets",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.7',
    install_requires = ""
)