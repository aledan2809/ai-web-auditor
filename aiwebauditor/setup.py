from setuptools import setup, find_packages

setup(
    name="aiwebauditor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.9.0",
        "httpx>=0.26.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.1.0",
        "pydantic>=2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "aiwebauditor=src.cli:main",
        ],
    },
    python_requires=">=3.10",
)
