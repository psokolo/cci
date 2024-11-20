from setuptools import setup, find_packages

setup(
    name="cci_calculator",
    version="0.1.3",
    description="Charlson Comorbidity Index calculator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    authors=[
        "Sokolowski, Piotr",
        "Siegel, Fabian"
        ],
    author_email="sokol.to@gmail.com",
    url="https://github.com/psokolo/cci/tree/main/cci_calculator",
    license="MIT",
    packages=find_packages(),
    install_requires=[],
    package_data={
        "": ["codes.json"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)