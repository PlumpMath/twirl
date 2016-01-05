#!/usr/bin/python

from setuptools import find_packages, setup


setup(
    name="twirl",
    version="0.1",
    author="Vitold Sedyshev",
    author_email="vit1251@gmail.com",
    description="Twirl is twisted clone but on libuv reactor",
    license="MIT",
    keywords="twisted twirl socket reactor eventloop libuv uv pyuv",
    url="https://github.com/vit1251/twirl",
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires=['apipkg', "pyuv"],
    classifiers=[
        "Development Status :: 3 - Alpha",
    ]
)
