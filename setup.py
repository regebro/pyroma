from setuptools import setup, find_packages
import os

version = '0.9.1'

setup(name='pyroma',
      version=version,
      description="Tests the quality of Python modules",
      long_description=open("README.txt").read() + "\n" +
                       open("HISTORY.txt").read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python :: 2.6",
        ],
      keywords='pypi quality testing',
      author='Lennart Regebro',
      author_email='regebro@gmail.com',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      scripts=['scripts/pyroma',],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      test_suite='pyroma',
      )
