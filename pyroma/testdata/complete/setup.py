from setuptools import setup, find_packages

version = "1.0"

with open("README.txt", encoding="UTF-8") as readme:
    long_description = readme.read()

setup(
    name="complete",
    version=version,
    description="This is a test package for pyroma.",
    long_description=long_description,
    python_requires=">=2.6",
    classifiers=[
        "Development Status :: 6 - Mature",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=["pypi", "quality", "example"],
    author="Lennart Regebro",
    author_email="regebro@gmail.com",
    url="https://github.com/regebro/pyroma",
    project_urls={"Source Code": "https://github.com/regebro/pyroma"},
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    install_requires=["zope.event"],
    tests_require=["six"],
    setup_requires=["setuptools"],
    zip_safe=True,
)
