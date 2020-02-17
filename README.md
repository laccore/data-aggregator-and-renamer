# CSDCO Geotek Data Aggregator and Renamer

This projet aggregates data from three different machine outputs (Geotek MSCL-S whole core logger, Geotek MSCL-XYZ split core logger,
Itrax XRF scanner) used at the [Continental Scientific Drilling Coordination Office (CSDCO)](https://csdco.umn.edu).

Given an input directory (which should contain the folders from the machine ouput) and an output filename, it aggregates data from 
all folders, accounting for differing columns present in different files. It has options to export as an Excel file, output a large 
amount of troubleshooting information, and, for XRF only right now, export the aggregated data into separate files by SiteHole.

Given an aggregated data file and a core list file (with a core_ID,section_number csv), the tool can assign CoreIDs to the aggregated file based on the order.

There is a front-end GUI that includes the functionality of all three smaller scripts. The program can be downloaded as a 
pre-built executables or run with `python gui.py`. The smaller scripts can by run manually if desired.

## Screenshot
<img src="https://user-images.githubusercontent.com/6476269/58586906-c14b9b00-8221-11e9-9b8b-2e56aa6a46f5.png" width="80%" alt="Screenshot of the CSDCO Collection Generator" />
