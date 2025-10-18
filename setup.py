from setuptools import setup, find_packages

setup(
    name="myprintx",
    version="1.0.3",
    author="Hualala",
    author_email="1061700625@qq.com",
    description="An enhanced print function supporting color and text styles.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/1061700625/myprintx",
    packages=find_packages(),
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Intended Audience :: Developers"
    ],
)
