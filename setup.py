from setuptools import setup, find_packages
import os

version = '0.9.2'

setup(name='pyroma',
      version=version,
      description="Test your projects packaging friendlyness",
      long_description=open("README.txt", 'rt').read() + "\n" +
                       open("HISTORY.txt", 'rt').read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
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
          'docutils',
          # -*- Extra requirements: -*-
      ],
      test_suite='pyroma',
      use_2to3=True,
      )
