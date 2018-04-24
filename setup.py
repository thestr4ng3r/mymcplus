
from setuptools import setup

setup(
    name="mymcplus",
    version="3.0",
    packages=["mymcplus", "mymcplus.gui"],
    entry_points={
        "console_scripts": [
            "mymcplus = mymcplus.mymc:main"
        ]
    },
    install_requires=[
        "wxPython" # TODO: make optional
    ]
)