from setuptools import setup, find_packages

import ssp


setup(name='ssp',
      version=ssp.__version__,
      author='Codasip s.r.o',
      author_email='support@codasip.com',
      packages=find_packages(),
      python_requires='>=3.6',
      entry_points='''
            [console_scripts]
            ssp=ssp.cli:ssp
      '''
      )
