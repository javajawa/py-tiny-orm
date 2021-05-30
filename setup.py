#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""
Setup Tools configuration for "py-tiny-orm".

This package is a ~1000 line SQLite object relation manager (ORM) which
automatically generates tables and queries using dataclasses.

Find this project at:
  https://github.com/javajawa/py-tiny-orm
  https://pypi.org/project/py-tiny-orm/
"""

import os
import subprocess
import setuptools  # type: ignore


def determine_version() -> str:
    """Automatically determine a version from git"""

    if os.environ.get("GITHUB_EVENT_NAME", "") == "release":
        tag = os.environ.get("GITHUB_REF")

        if tag:
            _, _, tag = tag.split("/", 2)

            return tag

    result = subprocess.run(
        ["git", "describe", "--tags"], stdout=subprocess.PIPE, check=False
    )

    if result.returncode == 0:
        tags = result.stdout.decode("utf-8").split("-")

        if len(tags) == 1:
            return tags[0]

        if len(tags) == 3:
            return ".dev".join(tags[0:2])

    result = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, check=False)

    if result.returncode == 0:
        sha = result.stdout.decode("utf-8")[0:6]
    else:
        sha = "000000"

    return "0.1.dev" + str(int(sha, 16))


with open("README.md", "r") as ifile:
    description = ifile.read()

setuptools.setup(
    name="py-tiny-orm",
    version=determine_version(),
    description="Trivial ORM for mapping dataclasses to SQLite",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/javajawa/py-tiny-orm",
    project_urls={
        "Source": "https://github.com/javajawa/py-tiny-orm",
    },
    author="Benedict Harcourt",
    author_email="ben.harcourt@harcourtprogramming.co.uk",
    license="BSD-2-Clause",
    python_requires=">=3.7",
    packages=["orm"],
    install_requires=["typing_inspect"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
