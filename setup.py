import setuptools
from scrawler import __version__

with open('README.md', 'r', encoding='utf-8') as f:
    long_des = f.read()

install_requires = [
    'lxml>=4.6.3',
    'selenium>=3.141.0',
    'urllib3>=1.26.4'

]

exclude = (
    '.idea', '.idea.*', 'bunny', 'bunny.*', 'env', 'env.*', 'tests', 'tests.*',
    'logs', 'logs.*', 'screenshots', 'screenshots.*'
)

setuptools.setup(
    name="Scrawler",
    version=__version__,
    description="Web Scraping Library Based on Selenium",
    long_description=long_des,
    long_description_content_type="text/markdown",
    url="https://github.com/danielafriyie/scrawler",
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "Operating System :: OS Independent",
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 5 - Production/Stable'
    ],
    packages=setuptools.find_packages(exclude=exclude),
    install_requires=install_requires,
    python_requires=">=3.7",
)
