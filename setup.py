from setuptools import setup, find_packages

setup(
    name="opper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies from requirements.txt here
    ],
    author="Opper AI",
    description="A scriptable compound AI web agent",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/opperai/opperator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 