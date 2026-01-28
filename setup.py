"""Setup para instalação do wxcode."""

from setuptools import setup, find_packages

setup(
    name="wxcode",
    version="0.1.0",
    description="Conversor universal de projetos WinDev/WebDev/WinDev Mobile",
    author="Gilberto",
    author_email="gilberto@example.com",
    license="MIT",
    python_requires=">=3.11",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "wxcode=wxcode.cli:app",
        ],
    },
)
