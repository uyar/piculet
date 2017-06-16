from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

setup(
    name='piculet',
    version='1.0b2',
    description='XML/HTML scraper using XPath queries.',
    long_description=readme + '\n\n' + history,
    url='https://bitbucket.org/uyar/piculet',
    author='H. Turgut Uyar',
    author_email='uyar@tekir.org',
    license='LGPL',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Utilities'
    ],
    keywords='xml html xpath scrape json',
    py_modules=['piculet'],
    install_requires=[],
    extras_require={
        'dev': [
            'flake8',
            'wheel',
            'twine'
        ],
        'doc': [
            'sphinx',
            'sphinx_rtd_theme',
            'pygenstub'
        ],
        'test': [
            'pytest',
            'pytest-cov'
        ],
    },
    entry_points="""
        [console_scripts]
        piculet=piculet:main
    """
)
