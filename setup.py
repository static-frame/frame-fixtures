from setuptools import setup #type: ignore
from codecs import open
from os import path
import typing as tp

# https://packaging.python.org/distributing/
# to deploy:
# pip install wheel, twine
# python setup.py sdist
# python setup.py bdist_wheel
# twine upload dist/*
# rm -r build; rm -r dist; rm -r *.egg-info

# in /static-frame-feedstock/recipe
# update meta.yaml in feedstock: set version and tar sha256 for tar, commit and push
# submit PR to conda-forge/static-frame-feedstock from fork
# merge into conda forge feedstock after all checks pass

ROOT_DIR_FP = path.abspath(path.dirname(__file__))

def get_long_description() -> str:
    with open(path.join(ROOT_DIR_FP, 'README.rst'), encoding='utf-8') as f:
        msg = []
        collect = False
        start = -1
        for i, line in enumerate(f):
            if line.startswith('frame-fixtures'):
                start = i + 2 # skip this line and the next
            if i == start:
                collect = True
            if collect:
                msg.append(line)

    return ''.join(msg).strip()


def get_version() -> str:
    with open(path.join(ROOT_DIR_FP, 'frame_fixtures', '__init__.py'),
            encoding='utf-8') as f:
        for l in f:
            if l.startswith('__version__'):
                if '#' in l:
                    l = l.split('#')[0].strip()
                return l.split('=')[-1].strip()[1:-1]
    raise ValueError("__version__ not found!")


def _get_requirements(file_name: str) -> tp.Iterator[str]:
    with open(path.join(ROOT_DIR_FP, file_name)) as f:
        for line in f:
            line = line.strip()
            if line:
                yield line

def get_install_requires() -> tp.Iterator[str]:
    yield from _get_requirements('requirements.txt')

def get_extras_require() -> tp.Dict[str, tp.List[str]]:
    # For now, have only one group that installs all extras; in the future, can create specialized groups if necessary.
    return {'extras': list(_get_requirements('requirements-extras.txt'))}

setup(
    name='frame-fixtures',
    version=get_version(),
    description='Use compact expressions to create diverse, deterministic DataFrame fixtures with StaticFrame',
    long_description=get_long_description(),
    python_requires='>3.6.0',
    install_requires=list(get_install_requires()),
    extras_require=get_extras_require(),
    url='https://github.com/InvestmentSystems/frame-fixtures',
    author='Christopher Ariza',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Topic :: Software Development',
            'Topic :: Scientific/Engineering',
            'Topic :: Scientific/Engineering :: Information Analysis',
            'License :: OSI Approved :: MIT License',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            ],

    keywords='dataframe fixtures test staticframe pandas numpy',
    packages=[
            'frame_fixtures',
            ],
    )