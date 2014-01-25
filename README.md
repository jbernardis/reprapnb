reprapnb
========

reprap host software based on wxpython that supports multiple simultaneous printer connections and printing

This program, inaddition to being based on wxpython instead of tkinter, offers the following improvements:

- notebook style interface with functions logically separated.  Pages for plating, file preparation, G Code reference and connection management.  Also a separate page for the log.
- as printers are connected and disconnected, notebook pages are added for manual control and print monitoring for each printer
- each printer may have up to 3 extruders
- allows one file to be sliced and examined while another is being printed on each connected printer.
- has basic plating functionality integrated so that stl files can be combined and arranged
- allows STL files to be merged into multi-material AMF files
- has an 3D STL/AMF file viewer
- works natively with slic3r, skeinforge, and now cura, and integrates seamlessly with their mechanism for storing profiles.  Allows for profile selection before invoking slicer.
