import os

from setuptools import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


def version_scheme(version):
    """
    Version scheme hack for setuptools_scm.

    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342

    If that issue is resolved, this method can be removed.
    """
    import time

    from setuptools_scm.version import guess_next_version

    if version.exact:
        return version.format_with("{tag}")
    else:
        _super_value = version.format_next_version(guess_next_version)
        now = int(time.time())
        return _super_value + str(now)


def local_version(version):
    """
    Local version scheme hack for setuptools_scm.

    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342

    If that issue is resolved, this method can be removed.
    """
    return ""


setup(
    name="air-quality-index",
    description="Download air quality index data from AirNow",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Ben Welsh",
    author_email="b@palewi.re",
    url="https://palewi.re/docs/air-quality-index/",
    license="MIT",
    packages=("air_quality_index",),
    install_requires=[
        "requests",
        "click",
        "kml2geojson",
    ],
    entry_points="""
        [console_scripts]
        airqualityindex=air_quality_index.cli:cmd
    """,
    use_scm_version={"version_scheme": version_scheme, "local_scheme": local_version},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    project_urls={
        "Maintainer": "https://github.com/datadesk",
        "Source": "https://github.com/datadesk/air-quality-index",
        "Tracker": "https://github.com/datadesk/air-quality-index/issues",
    },
)
