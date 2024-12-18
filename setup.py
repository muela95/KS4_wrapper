from setuptools import setup, find_packages

setup(
    name="KS4_wrapper", 
    version="0.0.1",    
    author="Pablo Muela",
    author_email="pmuela95@gmail.com",
    description="A wrapper for automatically running Kilosort4",
    long_description=open("README.md").read(),  
    long_description_content_type="text/markdown",
    url="https://github.com/muela95/KS4_wrapper", 
    packages=find_packages(),  # Automatically find all packages
    install_requires=[
        "kilosort",
        "torch",
        "numpy",
        "scipy",
        "spikeinterface"
    ],  # List of dependencies
    entry_points={
        "console_scripts": [
            "KS4_wrapper=KS_wrapper.main:main",  # Command-line entry point
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Minimum Python version
)