import sys
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
from pip.req import parse_requirements
from pip.download import PipSession

here = path.abspath(path.dirname(__file__))


install_reqs = parse_requirements(path.join(here, 'requirements.txt'), session=PipSession())

if sys.version_info < (3, 4):
    sys.exit('Sorry, Python < 3.4 is not supported')

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
      name='pylinky',
      version='0.1.1',
      description='Get your consumption data from your Enedis account (www.enedis.fr)',
      long_description=long_description,
      author='Dimitri Capitaine',
      author_email='grytes29@gmail.com',
      url='https://github.com/Pirionfr/pyLinky',
      package_data={'': ['LICENSE']},
      include_package_data=True,
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'pylink = pylink.__main__:main'
          ]
      },
      license='Apache 2.0',
      install_requires=[str(r.req) for r in install_reqs],
      classifiers=[
          'Programming Language :: Python :: 3.5',
      ]
)
