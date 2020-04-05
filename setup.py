import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [ line.strip() for line in open("requirements.txt", "r") if line.strip() ]

version_ns = { }
exec(open('nbscript/_version.py').read(), version_ns)
version = version_ns['__version__']

setuptools.setup(
    name="nbscript",
    version=version,
    author="Richard Darst",
    #author_email="author@example.com",
    description="Run Jupyter notebooks like shell scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NordicHPC/nbscript",
    packages=setuptools.find_packages(),
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*,",
    #py_modules=["nbscript"],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'nbscript=nbscript.nbscript:nbscript',
            'snotebook=nbscript.snotebook:snotebook',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Framework :: Jupyter",
    ],
)
# python setup.py sdist bdist_wheel
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# twine upload dist/*
