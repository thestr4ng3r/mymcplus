
from setuptools import setup

setup(
    name="mymc-plus",
    version="3.0",
    packages=["mymc"],
    entry_points={
        "console_scripts": [
            "mymc-plus = mymc.mymc:main"
        ]
    },
    install_requires=[
        "wxPython" # TODO: make optional
    ]
)