# CSDCO Geotek Data Aggregator and Renamer

![icon]

This project aggregates data from machine outputs of different scientific machines used at the [Continental Scientific Drilling Coordination Office (CSDCO)](https://csdco.umn.edu).

This tool will also [apply core names/IDs](#rename) to aggregated data.

The tool currently supports machine outputs from several instruments.

- [Geotek MSCL-S Whole-Core Logger](#geotek-mscl-s-whole-core-logger)
- [Geotek MSCL-XYZ Split-Core Logger](#geotek-mscl-xyz-split-core-logger)
- [Itrax XRF Scanner](#itrax-xrf-scanner)

## Usage

This tool is written in Python, and uses [Gooey](https://github.com/chriskiehl/Gooey) to create a simple GUI. Each script can also be run as a stand-alone script from the command line by using the `--ignore-gooey` flag. The `-h` flag will list required and optional parameters when running any of the scripts.

### Geotek MSCL-S Whole-Core Logger

Given an input directory (which should contain the folders from the machine ouput) and an output filename, it aggregates data from all folders, accounting for differing columns present in different files. It has options to export as an Excel file, and print a large amount of troubleshooting information (verbose).

![s1]

### Geotek MSCL-XYZ Split-Core Logger

Given an input directory (which should contain the folders from the machine ouput) and an output filename, it aggregates data from all folders, accounting for differing columns present in different files. It has options to export as an Excel file, print a large amount of troubleshooting information (verbose), and to **filter invalid Magnetic Susceptibility values** frequently recorded by the machines in our facility.

Currently, 'invalid values' are defined as any value below -50, but framework exists to apply different cutoffs to any column required just by modifying the [filter list](https://github.com/laccore/geotek-aggregator-and-renamer/blob/master/xyz_aggregator.py#L289).

![s2]

### Itrax XRF Scanner

Given an input directory (which should contain the folders from the machine ouput) and an output filename, it aggregates data from all folders, accounting for differing columns present in different files. It has options to export as an Excel file, print a large amount of troubleshooting information (verbose), and export the aggregated data into separate files by SiteHole.

![s3]

### Rename

Given an aggregated data file (generated by one of the above tabs) and a [core list file](#core-list-file) (with a core_ID,section_number csv), the tool can assign CoreIDs to the aggregated file based on the order. It is possible to specify the column number for the required fields, though the software will search through column names and try to find matches itself.

![s4]

#### Core List File

The structure of the core list file is a csv with `CoreID, Section Number`. Each line represents a new core, and the software is meant to be run with multiple files run together, even if only one core is in each original file (it uses section depth to detect a new core in the aggregated file). Numbers do not need to be consecutive, but they do need to be sequential.

An example of the core list file is provided below. This file represents 10 cores aggregated from 3 different MSCL-S sessions (i.e., data folders).

```csv
EXPD-SPR20-1A-1P-1,1
EXPD-SPR20-1A-1P-2,2
EXPD-SPR20-1B-1P-1,4
EXPD-SPR20-1B-2B-1,5
EXPD-SPR20-1B-3B-1,1
EXPD-SPR20-2A-1P-1,1
EXPD-SPR20-2A-2B-1,2
EXPD-SPR20-2A-2B-2,3
EXPD-SPR20-2A-3L-1,4
EXPD-SPR20-2A-4L-1,5
```

[icon]: docs/icon/aggregator_icon.png "Icon for the Data Aggregator and Renamer"
[s1]: docs/screenshots/1-mscl_s.png "Screenshot of the Data Aggregator MSCL-S screen"
[s2]: docs/screenshots/2-mscl_xyz.png "Screenshot of the Data Aggregator MSCL-XYZ screen"
[s3]: docs/screenshots/3-xrf.png "Screenshot of the Data Aggregator XRF screen"
[s4]: docs/screenshots/4-rename.png "Screenshot of the Data Aggregator Rename screen"
