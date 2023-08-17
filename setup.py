#!/usr/bin/env python
from setuptools import setup, find_packages

import setuptools.command.build_py


setup(
    name="pam_monitoring",
    version="0.1.0",
    description="PAM (Prometheus Automatic Monitoring)",
    author="Emanuele Graziano",
    author_email="emanuele@conductive.ai",
    install_requires=[
        "setuptools>=39.0.1",
        "grpcio>=1.51.1",
        "prometheus_client>=0.17.1",
        "grpc_interceptor>=0.15.3",
    ],
    url="https://github.com/conductive/pam-monitoring",
    packages=find_packages(exclude=["examples.*", "examples"]),
)