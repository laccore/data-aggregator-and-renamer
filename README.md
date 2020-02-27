# CSDCO Geotek Data Aggregator and Renamer

![icon]

This projet aggregates data from machine outputs of different scientific machines used at the [Continental Scientific Drilling Coordination Office (CSDCO)](https://csdco.umn.edu). It will also apply core names/IDs to aggregated data, if [supplied a file to translate](#core-list-file).

The tool currently supports these machine outputs

* Geotek MSCL-S whole core logger
* Geotek MSCL-XYZ split core logger
* Itrax XRF scanner

Given an input directory (which should contain the folders from the machine ouput) and an output filename, it aggregates data from all folders, accounting for differing columns present in different files. It has options to export as an Excel file, output a large amount of troubleshooting information, and, for XRF only right now, export the aggregated data into separate files by SiteHole.

Given an aggregated data file and a core list file (with a core_ID,section_number csv), the tool can assign CoreIDs to the aggregated file based on the order.

There is a front-end GUI that includes the functionality of all three smaller scripts. The program can be downloaded as a pre-built executables or run with `python gui.py`. The smaller scripts can by run manually if desired.

## Core List File

How to use a core list file to rename aggregated data.

## Screenshots

![s1]

[icon]: docs/aggregator_icon.png "Icon for the Data Aggregator and Renamer"
[s1]: docs/screenshots/1-mscl_s.png "Screenshot of the CSDCO Collection Generator"
