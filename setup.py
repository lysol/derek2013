try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(name='derek',
      version='0.1',
      description='derek',
      author='Derek Arnold',
      author_email='derek@derekarnold.net',
      url='http://derekarnold.net',
      packages=['derek'],
      zip_safe=False,
      install_requires=[
          'Flask',
          'python-dateutil',
          'feedgenerator'
      ],
      include_package_data=True,
      package_data={
          '': ['static/posts/*.markdown',
          'static/css/*.css', 'static/js/*.js', 'templates/*.html',
          'static/img/icons/*.jpg',
          'static/img/icons/*.png', 'static/img/*.png', 'static/img/*.jpg']
      }
      )
