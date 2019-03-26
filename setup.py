from setuptools import find_packages, setup

version = '0.0.1b'

install_requires = [
    'backoff',
    'gevent',
    'iso8601',
    'munch',
    'requests',
    'simplejson',
]

tests_require = [
    'flake8',
    'pytest-cov',
    'pytest-mock',
    'pytest',
]

setup(
    name='ocds_client',
    version=version,
    description='',
    long_description=f'{open("README.md").read()}\n',

    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Programming Language :: Python",
    ],
    keywords='',
    author='Quintagroup, Ltd.',
    author_email='info@quintagroup.com',
    url='https://github.com/openprocurement/ocds.client.python',
    license='Apache Software License 2.0',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={"test": tests_require},
    entry_points="""
    # -*- Entry points: -*-
    """,
    test_suite="ocds_client.tests.main:suite"
)