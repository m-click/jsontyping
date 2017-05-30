from setuptools import setup
setup(
    name='jsontyping',
    version='1.0.3',
    description='JSON support for named tuples, datetime and other objects, preventing ambiguity via type annotations',
    url='https://github.com/m-click/jsontyping',
    author='Volker Diels-Grabsch',
    author_email='volker.diels-grabsch@m-click.aero',
    license='ISC',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='json',
    py_modules=['jsontyping'],
)
