from setuptools import setup, find_packages

setup(
    name='pyVideoSheet',
    version='1.0',
    packages = find_packages(),
    package_data = {'pyVideoSheet': ['data/*.ttf']},
    description='Python video contact sheet generator',
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    author='Wattanit Hotrakool',
    author_email='wattanit.h@gmail.com',
    url='https://github.com/rorasa/pyVideoSheet',
    license='MPL 2.0',
    python_requires=">=2.7",
    use_2to3=False,
)
