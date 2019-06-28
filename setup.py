import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tuyapy",
    version="0.1.3",
    author="Tuya Inc.",
    author_email="tuyasmart@tuya.com",
    description="A Python library for Tuya Device with Python 3+",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ),
)

