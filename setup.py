# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="costi",
    version="0.2",
    author="Lorenz Heiler",
    author_email="contact@lorenzheiler.com",
    url="www.lorenzheiler.com",
    license="GPL",
    description="Costi - Collection of Open Source Threat Intelligence ",
    long_description="",
    classifiers="",
    entry_points={
        "console_scripts": ['costi = costi.costi:main']
        },
    packages=['costi', 'costi.plugins'],
    include_package_data=True,
    install_requires=[
        'web.py',
        'pygal',
        'numpy',
        'exrex',
        'feedparser',
        'lxml',
        'pycurl'
        ],

)
