
# mymc+

mymc+ is a PlayStation 2 memory card manager for to be used with
.ps2 images as created by the PCSX2 emulator for example.

It is based on the classic [mymc](http://www.csclub.uwaterloo.ca:11068/mymc/)
utility created by Ross Ridge and released as Public Domain.
Changes that have been made from the original code include the following:

* Ported to Python 3 and wxPython Phoenix
* Replaced the natively implemented 3D icon renderer with a cross-platform solution using OpenGL 3.2 Core
* Added support for importing PSV files (as created by the PlayStation 3)
* Added a py.test based test suite
* Many other small refactorings...

Please note that mymc+ is released under the **GPLv3, not Public Domain**!

Here is an overview of most features:

* Read and write the PS2 memory card file system, including extracting and adding files at file system level
* Import save games in MAX Drive (.max), EMS (.psu), SharkPort (.sps), X-Port (.xps), Code Breaker (.cbs) and PSV (.psv) format
* Export save games in MAX Drive (.max) and EMS (.psu) format
* Command line interface
* Optional wxPython based GUI, also displaying the 3D icons

![Screenshot](screenshot.png)

## License

mymc+  
by Florian Märkl, based on mymc by Ross Ridge

This program is free software: you can redistribute it and/or modify  
it under the terms of the GNU General Public License as published by  
the Free Software Foundation, either version 3 of the License, or  
(at your option) any later version.

This program is distributed in the hope that it will be useful,  
but WITHOUT ANY WARRANTY; without even the implied warranty of  
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the  
GNU General Public License for more details.

You should have received a copy of the GNU General Public License  
along with this program.  If not, see <https://www.gnu.org/licenses/>.
