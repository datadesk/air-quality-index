import os
from setuptools import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='air-quality-index',
    version='0.1.1',
    description="Download air quality index data from AirNow",
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Ben Welsh',
    author_email='b@palewi.re',
    url='http://www.github.com/palewire/air-quality-index',
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
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
    ],
    project_urls={
        'Maintainer': 'https://github.com/palewire',
        'Source': 'https://github.com/palewire/air-quality-index',
        'Tracker': 'https://github.com/palewire/air-quality-index/issues'
    },
)
