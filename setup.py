#!env python
from setuptools import setup

INSTALL_REQUIREMENTS = [
    'configobj',
    'requests',
    'common',
    'kombu',
    'influxdb'
]

VERSION = '0.1a'

setup(name='jarvis',
      version=VERSION,
      packages=[
          'jarvis',
      ],
      install_requires=INSTALL_REQUIREMENTS,
      include_package_data=True,
      # Metadata.
      description='Jarvis - communication module for Carrier',
      author='The Butcher team',
      author_email='artyom.rozumenko@gmail.com',
      url='https://github.com/arozumenko',
      license='Custom license')
