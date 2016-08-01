from setuptools import setup


setup(
    name='woody',
    version='1.0a1',
    description='XML/HTML scraper using XPath queries.',
    long_description='',
    url='https://bitbucket.org/uyar/woody',
    author='H. Turgut Uyar',
    author_email='uyar@tekir.org',
    license='GPL',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        'Programming Language :: Python :: 3.5'
    ],
    keywords='xml html xpath scrape',
    py_modules=['woody'],
    install_requires=[],
    tests_require=['pytest', 'pytest-cov', 'flake8'],
    entry_points="""
        [console_scripts]
        woody=woody:main
    """
)
