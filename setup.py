import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nbscript",
    version="0.0.1",
    author="Richard Darst",
    author_email="author@example.com",
    description="Run Jupyter notebooks like shell scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AaltoScienceIT/nbscript",
    packages=setuptools.find_packages(),
    #py_modules=["nbscript"],
    entry_points={
        'console_scripts': [
            'nbscript=nbscript.nbscript:main',
            'snotebook=nbscript.snotebook:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Framework :: Jupyter",
    ],
)
