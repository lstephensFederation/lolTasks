#!/usr/bin/env python3
"""
lolTasks - A terminal-based weekly task management application
"""

from setuptools import setup, find_packages
import os

# Read the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="lolTasks",
    version="1.0.0",
    author="Luke J. Stephens",
    author_email="l.stephens@federation.edu.au",
    description="A terminal-based weekly task management application with advanced text editing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lstephensFederation/lolTasks",
    packages=find_packages(),
    py_modules=['task'],
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'lolTasks=task:entry_point',
            'task=task:entry_point',
        ],
    },
    keywords="task management terminal curses weekly planner",
    project_urls={
        "Bug Reports": "https://github.com/lstephensFederation/lolTasks/issues",
        "Source": "https://github.com/lstephensFederation/lolTasks",
    },
)