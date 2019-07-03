import os
from setuptools import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='air-quality-index',
    version='0.0.3',
    description="Download air quality index data from AirNow",
    long_description=read('README.rst'),
    author='Los Angeles Times Data Desk',
    author_email='datadesk@latimes.com',
    url='http://www.github.com/datadesk/air-quality-index',
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
        'License :: OSI Approved :: MIT License',
    ],
    project_urls={
        'Maintainer': 'https://github.com/datadesk',
        'Source': 'https://github.com/datadesk/air-quality-index',
        'Tracker': 'https://github.com/datadesk/air-quality-index/issues'
    },
)
