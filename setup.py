from setuptools import setup, find_packages

setup(
    name="web_agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "playwright>=1.39.0",
        "rich>=13.0.0",
        "opperai>=0.1.0",
    ],
) 