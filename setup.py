from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="grblogtools",
    version="0.1.1",
    author="Gurobi Optimization, LLC",
    description="Gurobi log file tools for parsing and data exploration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    platforms=["Windows", "Linux", "macOS"],
    url="https://github.com/Gurobi/grblogtools",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["ipywidgets", "numpy", "pandas", "plotly", "xlsxwriter"],
    python_requires=">=3.6",
)
