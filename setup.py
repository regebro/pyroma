from setuptools import setup, find_packages

version = "3.2.dev0"

with open("README.rst", encoding="UTF-8") as file:
    long_description = file.read() + "\n"

with open("HISTORY.txt", encoding="UTF-8") as file:
    long_description += file.read()

setup(
    name="pyroma",
    version=version,
    description="Test your project's packaging friendliness",
    long_description=long_description,
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
    ],
    keywords=["pypi", "quality", "testing"],
    author="Lennart Regebro",
    author_email="regebro@gmail.com",
    url="https://github.com/regebro/pyroma",
    project_urls={"Source Code": "https://github.com/regebro/pyroma"},
    license="MIT",
    packages=find_packages(exclude=["ez_setup"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "docutils",
        "pygments",
    ],
    entry_points={
        "console_scripts": ["pyroma = pyroma:main"],
        "zest.releaser.prereleaser.before": ["pyroma = pyroma:zester"],
    },
    test_suite="pyroma",
)
