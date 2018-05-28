from setuptools import setup, find_packages
from io import open

version = '2.3.1'

long_description = (open("README.rst", 'rt', encoding='UTF-8').read() + "\n" +
                    open("HISTORY.txt", 'rt', encoding='UTF-8').read())

setup(name='pyroma',
      version=version,
      description="Test your project's packaging friendliness",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: Implementation :: PyPy",
          "License :: OSI Approved :: MIT License",
      ],
      keywords=['pypi', 'quality', 'testing'],
      author='Lennart Regebro',
      author_email='regebro@gmail.com',
      url='https://github.com/regebro/pyroma',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'docutils',
      ],
      entry_points={
          'console_scripts': [
              'pyroma = pyroma:main',
          ],
          'zest.releaser.prereleaser.before': [
              'pyroma = pyroma:zester',
          ],
      },
      test_suite='pyroma',
      )
