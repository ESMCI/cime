#!/usr/bin/env python

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

setup(
    author="CIME developers",
    python_requires=">=3.5",
    description=" Common Infrastructure for Modeling the Earth",
    long_description=readme,
    include_package_data=True,
    name="CIME",
    packages=find_packages(),
    test_suite="CIME.tests",
    tests_requires=["pytest"],
    url="https://github.com/ESMCI/cime",
    version="0.1.0"
)
