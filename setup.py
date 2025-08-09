#!/usr/bin/env python3
"""
Zaim CLI セットアップスクリプト
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="zaim-cli",
    version="1.0.0",
    author="Claude Code",
    author_email="noreply@anthropic.com",
    description="Zaim家計簿管理のためのコマンドラインツール",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/user/use-zaim-api",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "zaim-cli=zaim_cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)