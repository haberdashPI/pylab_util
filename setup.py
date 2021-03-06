from setuptools import setup

setup(name='nu_wright_lab_util',version='0.1.1',author='David Little',
      packages=['nu_wright_lab_util'],
      package_dir={'nu_wright_lab_util': 'src'},
      package_data={'nu_wright_lab_util': ['stan/*.stan']},
      requires=['statsmodels(>=0.5.0)',
                'pystan(>=2.17.0)',
                'patsy(>=0.3.0)','matplotlib',
                'numpy','pandas','appdirs','scipy', 'h5py', 'pymc3'])
