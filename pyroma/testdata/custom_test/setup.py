from setuptools import setup, find_packages
from setuptools.command.test import test

version = "0.0foo"


class CustomTest(test):
    pass


setup(
    name="minimal",
    version=version,
    description="Test",
    classifiers=[],
    keywords="",
    author="",
    author_email="",
    url="",
    license="",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points="""
      # -*- Entry points: -*-
      """,
    cmdclass={"test": CustomTest},
)
