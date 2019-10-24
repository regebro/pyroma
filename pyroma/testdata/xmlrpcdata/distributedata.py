from datetime import datetime

args = ("https://pypi.org/pypi",)
kw = {}
data = {
    "package_releases": {("distribute",): ["0.6.15"]},
    "release_data": {
        ("distribute", "0.6.15"): {
            "maintainer": None,
            "requires_python": None,
            "maintainer_email": None,
            "cheesecake_code_kwalitee_id": None,
            "keywords": "CPAN PyPI distutils eggs package management",
            "package_url": "http://pypi.org/project/distribute",
            "author": "The fellowship of the packaging",
            "author_email": "distutils-sig@python.org",
            "download_url": "UNKNOWN",
            "platform": "UNKNOWN",
            "version": "0.6.15",
            "cheesecake_documentation_id": None,
            "_pypi_hidden": False,
            "description": """===============================
Installing and Using Distribute
===============================

.. contents:: **Table of Contents**

-----------
Disclaimers
-----------

This is an example of a long_description
========================================

It doesn't need to be much longer than this, I think.
""",
            "release_url": "http://pypi.org/project/distribute/0.6.15",
            "_pypi_ordering": 115,
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: " "Python Software Foundation License",
                "License :: OSI Approved :: Zope Public License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
                "Topic :: Software Development :: " "Libraries :: Python Modules",
                "Topic :: System :: Archiving :: Packaging",
                "Topic :: System :: Systems Administration",
                "Topic :: Utilities",
            ],
            "name": "distribute",
            "license": "PSF or ZPL",
            "summary": "Easily download, build, install, upgrade, and "
            "uninstall Python packages",
            "home_page": "http://packages.python.org/distribute",
            "stable_version": None,
            "cheesecake_installability_id": None,
        }
    },
    "release_urls": {
        ("distribute", "0.6.15"): [
            {
                "has_sig": False,
                "upload_time": datetime(2011, 3, 16, 16, 31, 39),
                "comment_text": "",
                "python_version": "source",
                "url": "http://pypi.python.org/packages/source/d/"
                "distribute/distribute-0.6.15.tar.gz",
                "md5_digest": "ea52e1412e7ff560c290266ed400e216",
                "downloads": 0,
                "filename": "distribute-0.6.15.tar.gz",
                "packagetype": "sdist",
                "size": 289103,
            }
        ]
    },
    "package_roles": {
        ("distribute",): [
            ["Owner", "someone"],
            ["Owner", "me"],
            ["Maintainer", "other"],
        ]
    },
}
