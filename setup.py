#
# This file is part of mymc+, based on mymc by Ross Ridge.
#
# mymc+ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mymc+ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mymc+.  If not, see <http://www.gnu.org/licenses/>.
#

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