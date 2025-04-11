#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="docker-resources",
    version="1.0.0",
    description="Инструмент для проверки ресурсов Docker на удаленных серверах",
    author="",
    packages=find_packages(),
    install_requires=[
        "paramiko>=3.0.0",
        "prettytable>=3.0.0",
    ],
    entry_points={
        'console_scripts': [
            'docker-resources=docker_resources:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.6",
)