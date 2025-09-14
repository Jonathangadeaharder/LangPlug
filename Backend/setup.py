from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="langplug-backend",
    version="1.0.0",
    author="LangPlug Team",
    description="German Language Learning Platform Backend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.116.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "langplug-export-openapi=export_openapi:export_openapi",
        ],
    },
)