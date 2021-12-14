"""
Copyright 2021 Daniel Afriyie

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import setuptools
from raccy import __version__

with open('README.md', 'r', encoding='utf-8') as f:
    long_des = f.read()

install_requires = [
    'selenium>=3.141.0',
    'wget==3.2',
    'requests==2.26.0',
    'raccy-orm==0.0.1',
    'raccy-utils==0.1.1'
]

include = (
    'raccy', 'raccy.*'
)

setuptools.setup(
    name="raccy",
    version=__version__,
    description="Web Scraping Library Based on Selenium",
    long_description=long_des,
    long_description_content_type="text/markdown",
    author='Daniel Afriyie',
    author_email='danielafriyie98@gmail.com',
    url="https://github.com/danielafriyie/raccy",
    license='Apache License, Version 2.0',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 5 - Production/Stable'
    ],
    packages=setuptools.find_packages(include=include),
    install_requires=install_requires,
    python_requires=">=3.7",
)
