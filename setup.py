from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

setup(
    name='piculet',
    version='1.0a1',
    description='XML/HTML scraper using XPath queries.',
    long_description=readme + '\n\n' + history,
    url='https://bitbucket.org/uyar/piculet',
    author='H. Turgut Uyar',
    author_email='uyar@tekir.org',
    license='GPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.4'
    ],
    keywords='xml html xpath scrape',
    py_modules=['piculet'],
    install_requires=[],
    tests_require=['pytest', 'pytest-cov', 'flake8'],
    entry_points="""
        [console_scripts]
        piculet=piculet:main
    """
)
