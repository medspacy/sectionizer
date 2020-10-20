from setuptools import setup

# read the contents of the README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

def get_version():
    """Load the version from version.py, without importing it.
    This function assumes that the last line in the file contains a variable defining the
    version string with single quotes.
    """
    try:
        with open('clinical_sectionizer/_version.py', 'r') as f:
            return f.read().split('\n')[0].split('=')[-1].replace('\'', '').strip()
    except IOError:
        raise IOError

setup(
    name="clinical_sectionizer",
    version=get_version(),
    description="Document section detector using spaCy for clinical NLP",
    author="medSpaCy",
    author_email="medspacy.dev@gmail.com",
    packages=["clinical_sectionizer"],
    install_requires=[
        "spacy>=2.3.0,<3.0.0",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_data={"clinical_sectionizer": ["../resources/*"]},
)