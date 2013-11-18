reprapnb
========

2nd generation reprap host software based on wxpython

This program, inaddition to being based on wxpython instead of tkinter, offers the following improvements:

- notebook style interface with functions logically separated.  Pages for plating, file preparation, manual control and print monitoring.  Also a separate page for the log.
- support of up to 3 extruders
- allows one file to be sliced and examined while another is being printed.
- has basic plating functionality integrated so that stl files can be combined and arranged
- works natively with slic3r and skeinforge, and integrates with their mechanism for storing profiles.  Allows for profile selection before invoking slicer.
