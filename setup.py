import pathlib
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

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='ocds-api.client.python',
    version=version,
    description='',
    long_description=README,
    long_description_content_type="text/markdown",
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 4 - Beta'
    ],
    keywords=['ocds-client', 'ocds-api', 'ocds'],
    author='Quintagroup, Ltd.',
    author_email='info@quintagroup.com',
    url='https://github.com/openprocurement/ocds-api.client.python',
    license='Apache Software License 2.0',
    packages=find_packages(exclude=['ez_setup', 'tests']),
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
