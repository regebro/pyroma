from datetime import datetime

args = ("https://pypi.org/pypi",)
kw = {}
data = {
    "package_releases": {("complete",): ["1.0.dev1"]},
    "release_data": {
        ("complete", "1.0.dev1"): {
            "maintainer": None,
            "requires_python": None,
            "maintainer_email": None,
            "cheesecake_code_kwalitee_id": None,
            "keywords": ["pypi", "quality", "example"],
            "package_url": "http://pypi.org/project/complete",
            "author": "Lennart Regebro",
            "author_email": "regebro@gmail.com",
            "download_url": "UNKNOWN",
            "platform": "UNKNOWN",
            "version": "1.0.dev1",
            "cheesecake_documentation_id": None,
            "_pypi_hidden": False,
            "description": """Complete
========

This is a test package for pyroma that is supposed to have a complete
set of metadata and also runnable tests. It should score the maximum possible
on package tests.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed porttitor, neque
at dignissim condimentum, libero est dictum dolor, sit amet tempor urna diam
eget velit. Suspendisse at odio quam, ut vestibulum ipsum. Nulla facilisi.
Nullam nunc dolor, tempus in vulputate id, fringilla eget metus. Pellentesque
nulla nisl, imperdiet ac vulputate non, commodo tincidunt purus. Aenean
sollicitudin orci eget diam dignissim scelerisque. Donec quis neque nisl, eu
adipiscing velit. Aenean convallis ante sapien. Etiam vitae viverra libero.
Nullam ac ligula erat. Aliquam pellentesque, est eget faucibus pharetra, urna
orci rhoncus nisi, adipiscing elementum libero lectus ut odio. Duis tincidunt
mi quam, quis interdum enim. Nunc sed urna urna, id lacinia turpis. Quisque
malesuada, velit ut tincidunt lacinia, dolor augue varius velit, in ultrices
lectus enim et dolor. Fusce augue eros, aliquet ac dapibus at, tincidunt vitae
leo. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus sapien
neque, fermentum sed ultrices sit amet, fermentum nec est. Pellentesque
imperdiet enim nec velit posuere id dignissim massa molestie.""",
            "release_url": "http://pypi.org/project/distribute/1.0.dev1",
            "_pypi_ordering": 115,
            "classifiers": [
                "Development Status :: 6 - Mature",
                "Operating System :: OS Independent",
                "Programming Language :: Python :: 2.6",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3.1",
                "Programming Language :: Python :: 3.2",
                "Programming Language :: Python :: 3.3",
                "License :: OSI Approved :: MIT License",
            ],
            "name": "complete",
            "license": "MIT",
            "summary": "This is a test package for pyroma.",
            "home_page": "https://github.com/regebro/pyroma",
            "stable_version": None,
            "cheesecake_installability_id": None,
        }
    },
    "release_urls": {
        ("complete", "1.0.dev1"): [
            {
                "has_sig": False,
                "upload_time": datetime(2011, 3, 16, 16, 31, 39),
                "comment_text": "",
                "python_version": "source",
                "url": "http://pypi.python.org/packages/source/c/complete/"
                "complete-1.0.dev1.tar.gz",
                "md5_digest": "ea52e1412e7ff560c290266ed400e216",
                "downloads": 0,
                "filename": "complete-1.0.dev1.tar.gz",
                "packagetype": "sdist",
                "size": 289103,
            }
        ]
    },
    "package_roles": {
        ("complete",): [["Owner", "someone"], ["Owner", "me"], ["Owner", "other"]]
    },
}
