#!/usr/bin/env python
from setuptools import setup, find_packages

import setuptools.command.build_py


setup(
    name="pam-monitoring",
    version="0.1.0",
    description="PAM (Prometheus Automatic Monitoring)",
    author="Emanuele Graziano",
    author_email="emanuele@conductive.ai",
    install_requires=[
        "setuptools>=39.0.1",
        "grpc>=1.0.0",
        "prometheus_client>=0.17.1",
        "grpc_interceptor>=0.15.3",
    ],
    url="https://github.com/conductive/py-grpc-prometheus",
    packages=find_packages(exclude=["examples.*", "examples"]),
)