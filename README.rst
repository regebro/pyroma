pyroma
======

Pyroma rhymes with aroma, and is a product aimed at giving a rating of how well
a Python project complies with the best practices of the Python packaging
ecosystem, primarily PyPI, pip, Distribute etc, as well as a list of issues that
could be improved.

The aim of this is both to help people make a project that is nice and usable,
but also to improve the quality of Python third-party software, making it easier
and more enjoyable to use the vast array of available modules for Python.

It's written so that there are a library with methods to call from Python, as
well as a script, also called pyroma.

It can be run on a project directory before making a release:

    $ pyroma .

On a distribution before uploading it to the CheeseShop:

    $ pyroma pyroma-1.0.tar.gz

Or you can give it a package name on CheeseShop:

    $ pyroma pyroma

Giving it a name on CheeseShop is the most extensive test, as it will
test for several things isn't otherwise tested.

In all cases the output is similar::

    ------------------------------
    Checking .
    Found pyroma
    ------------------------------
    The packages long_description is quite short.
    ------------------------------
    Final rating: 9/10
    Cottage Cheese
    ------------------------------


Tests
-----

This is the list of checks that are currently performed:

* The package should have a name, a version and a Description.
  If it does not, it will receive a rating of 0.

* The version number should be a string. A floating point number will
  work with distutils, but most other tools will fail.

* The version number should comply to PEP386.

* The description should be over 10 characters, and the long_description
  should be over a 100 characters.

* Pyroma will convert your long_description to HTML using Docutils, to
  verify that it is possible. This guarantees pretty formatting of your
  description on PyPI. As long as Docutils can convert it, this passes,
  even if there are warnings or error in the conversion. These warnings
  and errors are printed to stdout so you will see them.

  NB! Currently this doesn't change the rating, this is because Docutils
  no longer raises an error during this process, so I have to rewrite the
  test. Once it's reinstated, incorrect syntax will be fatal.

* You should have the following meta data fields filled in:
  classifiers, keywords, author, author_email, url and license.

* You should have classifiers specifying the supported Python versions.

* You should have a classifier specifying the project license.

* If you are checking on a PyPI package, and not a local directory or
  local package, pyroma will check the number of owners the package has
  on PyPI. It should be three or more, to minimize the "Bus factor",
  the risk of the index owners suddenly going off-line for whatever reason.

* If you are checking on a PyPI package, and not a local directory or
  local package, pyroma will check that you have uploaded a source
  distribution, and not just binary distributions.


Version control integration
---------------------------

With `pre-commit <https://pre-commit.com>`_, pyroma can be run whenever you
commit your work by adding the following to your ``.pre-commit-config.yaml``:

.. code-block:: yaml

    repos:
    -   repo: https://github.com/regebro/pyroma
        rev: "3.2"
        hooks:
        -   id: pyroma


Credits
-------

The project was created by Lennart Regebro, regebro@gmail.com

The name "Pyroma" was coined by Wichert Akkerman, wichert@wiggy.net

Contributors:

  * Godefroid Chapelle
  * Dmitry Vakhrushev
  * hugovk
  * Jeff Quast
  * Maurits van Rees
  * Hervé Beraud
  * Érico Andrei
  * Jakub Wilk
  * Andreas Lutro
  * Scott Colby
  * Andrew Murray
  * Nikita Sobolev
  * Charles Tapley Hoyt
  * Max Tyulin
  * Michael Howitz
  * Florian Bruhin
  * Christopher A.M. Gerlach
