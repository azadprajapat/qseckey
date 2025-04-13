from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="qseckey",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    author="Azad Prajapat",
    author_email="azadprajapat4@gmail.com",
    description="QSECKEY: Quantum Secure Key generation library for classical KMS integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/azadprajapat/qseckey.git",  
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
