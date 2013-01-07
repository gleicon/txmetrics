import sys, os, os.path, subprocess
from setuptools.command import easy_install
import pkg_resources as pkgrsrc

from setuptools import setup
from distutils import log
log.set_threshold(log.INFO)

setup(
        name            = "txmetrics",
        version         = "0.2",

        packages        =   ['txmetrics'],
        install_requires = ['txredisapi'],

        # metadata for upload to PyPI
        author          = "Gleicon Moraes",
        author_email    = "gleicon@gmail.com",
        keywords        = "twisted metrics redis",
        description     = "simple python metrics for twisted",
        url             = "https://github.com/gleicon/txmetrics",
    )

