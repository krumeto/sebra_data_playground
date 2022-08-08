from setuptools import setup, find_packages

base_packages = [
    "scikit-learn>=0.23.2",
    "pandas>=0.23.4",
    "dateparser>=1.1.1",
    "altair>=4.2.0",
    "matplotlib>=3.5.0",
]

setup(
    name="sebradata",
    version="0.1.0",
    packages=find_packages(),
    author="Krum Arnaudov",
    description="Wrangling utils for the SEBRA data published by the Bulgarian government",
    install_requires=base_packages,
)