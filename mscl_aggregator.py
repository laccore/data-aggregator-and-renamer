import argparse
import locale
import timeit
from pathlib import Path

import pandas as pd
import xlsxwriter


def validate_export_filename(export_filename, excel):
    """Ensure export extension matches flag, return corrected filename.

    xlswriter won't export an Excel file unless the file extension is a
    valid Excel file extension (xsls, xls). This script assumes the flag
    indicates user intention, and will append a correct extension.

    If not using the Excel flag, this ensures the filename ends in .csv.

    Returns the validated/fixed export filename.
    """

    if excel:
        if export_filename.suffix not in [".xlsx", ".xls"]:
            return export_filename.with_suffix(".xlsx")
    else:
        if export_filename.suffix != ".csv":
            return export_filename.with_suffix(".csv")

    return export_filename


def generate_file_list(input_dir, separator, verbose=False):
    """Comb through directories to generate list of files to combine.

    Given the input directory, scan through all directories and collect
    the paired files needed to aggregate data (out and raw).

    Returns a nested list of pairs of PurePath objects.
    """

    file_list = []

    p = Path(input_dir).iterdir()
    dir_list = [
        entry
        for entry in p
        if "mscl" in entry.name.lower()
        and separator in entry.name.lower()
        and entry.is_dir()
        and not entry.name.startswith(".")
    ]
    # Sort folders by the "_part##" token, which is most consistently correct
    # converting the number to float because there have been times where #.5 has been used
    dir_list = sorted(dir_list, key=lambda d: float(d.name.split(separator)[-1]))

    for d in dir_list:
        p = Path(d).iterdir()
        f_list = [
            entry
            for entry in p
            if not entry.name.startswith(".")
            and entry.is_file()
            and entry.suffix in [".out", ".raw"]
        ]
        f_list = sorted(f_list, key=lambda f: f.name.split(".")[-1])

        if len(f_list) != 2:
            print(
                f"ERROR: {'more' if len(f_list) > 2 else 'less'} than two files with extension .raw or .out were found."
            )
            print(f"Exactly one of each file required in folder {d.name}.")
            exit(1)

        file_list.append(f_list)

    if verbose:
        print(f"Found data in {len(file_list)} folders to join.")
        for f in file_list:
            print(f"\t{f[0].parts[-2]}")
        print()

    return file_list


def open_and_clean_file(file_path, delimiter, skip_rows, drop_rows):
    """Open file in pandas, perform some file cleanup, return a dataframe

    Opens the text files output from the Geotek equipment software
    with a number of flags, then drops the first row of 'data' which is
    just the units field.

    Rows are dropped, whitespace is stripped from headers, and the index
    is reset so data aligns later on.

    Notes on files:
    - tell pandas to treat empty fields as empty strings, not NaNs
    - the 'latin1' encoding flag is needed to open the .raw files
    - on_bad_lines (requires engine="python") is there to handle poorly
      formatted csv files with extra columns in part of the file
    - na_filter=False means empty cells aren't converted into NaN
    """

    num_cols = len(pd.read_csv(file_path, skiprows=skip_rows, nrows=1).columns)

    df = pd.read_csv(
        file_path,
        delimiter=delimiter,
        skiprows=skip_rows,
        na_filter=False,
        encoding="latin1",
        header=None,
        on_bad_lines=lambda x: x[:num_cols],
        engine="python",
    )

    df = df.rename(str.strip, axis="columns")
    df = df.drop(drop_rows)
    df = df[~df.eq("").all(1)]  # removes empty rows (inconsistent number across files)
    df = df.reset_index(drop=True)

    return df


def clean_headers_add_units(dataframe, column_order, drop_headers=[]):
    """Drop unwanted headers and add units row to data.

    Any new columns will need to have a units row added to the list
    below, which is converted into a dict which is converted into
    a pandas dataframe which is then concatenated to the front of the
    combined data.
    """

    # Format: machine header, readable header, units
    headers_and_units = [
        ["SECT NUM", "SectionID", ""],
        ["SECT DEPTH", "Section Depth", "cm"],
        ["CT", "Sediment Thickness", "cm"],
        ["PWAmp", "pWave Amplitude", ""],
        ["PWVel", "pWave Velocity", "m/s"],
        ["Den1", "Gamma Density", "g/cm³"],
        ["MS1", "MS Loop", "SI x 10^-5"],
        ["Imp", "Impedance", ""],
        ["FP", "Fractional Porosity", ""],
        ["NGAM", "Natural Gamma Radiation", "CPS"],
        ["RES", "Electrical Resistivity", "Ohm-m"],
        ["Temp", "Temperature in Logging Room", "°C"],
    ]

    new_headers = {item[0]: item[1] for item in headers_and_units}
    units = {item[0]: item[2] for item in headers_and_units}

    # Remove unwanted column headers
    for dh in drop_headers:
        if dh in column_order:
            column_order.remove(dh)

    # Display warnings if an unrecognized machine header is seen
    for header in column_order:
        if header not in units:
            print(f"WARNING: no associated units for header '{header}'.")
            units[header] = ""
        if header not in new_headers:
            print(f"WARNING: no associated readable header for header '{header}'.")
            new_headers[header] = header

    # Add units row
    dataframe = pd.concat(
        [pd.DataFrame([units]), dataframe], ignore_index=True, sort=True
    )

    # Fix headers
    dataframe = dataframe.rename(columns=new_headers)
    column_order = [new_headers[header] for header in column_order]

    return dataframe, column_order


def aggregate_mscl_data(
    input_dir, out_filename, separator="-p", excel=False, verbose=False
):
    """Aggregate cleaned data from different files and folders, export."""
    if verbose:
        start_time = timeit.default_timer()

    input_dir = Path(input_dir)

    file_list = generate_file_list(input_dir, separator, verbose)

    out_filename = Path(out_filename)
    export_filename = validate_export_filename(out_filename, excel)
    if verbose and export_filename != out_filename:
        print(f"Adjusted export filename to '{export_filename}'")

    export_path = input_dir / export_filename

    # Initialize an empty dataframe to hold combined data
    combined_df = pd.DataFrame()

    # Need to specify column order to match expected output
    column_order = []

    # Start combining data
    # Row 0 (unit row, added later) of data is dropped for both files.
    # For .raw files, the second row is also dropped because the Geotek
    # software for the raw files is always off by one compared to the .out
    # files.
    skip_rows = [0]  # skip first row of mscl output files

    for out, raw in file_list:
        if verbose:
            print(f"Loading files from {out.parts[-2]}...")
            print()

        out_df = open_and_clean_file(
            file_path=out, delimiter="\t", skip_rows=skip_rows, drop_rows=[0]
        )
        raw_df = open_and_clean_file(
            file_path=raw, delimiter="\t", skip_rows=skip_rows, drop_rows=[0, 1]
        )

        if verbose:
            print(f"Loaded files from {out.parts[-2]}")
            print(f"  {out.name}\t({len(out_df)} rows)")
            print(f"  {raw.name}\t({len(raw_df)} rows)")
            print()

        # Add "Temp" column from .raw file to .out file dataframe
        out_df["Temp"] = raw_df["Temp"]

        # This records column order for the first file, then adds
        # successive columns at the second to last place, keeping Temp
        # in the last position. The dataframe remains unordered, but
        # when exporting the order will be applied.
        if not column_order:
            column_order = out_df.columns.values.tolist()
        else:
            new_columns = [
                c for c in out_df.columns.values.tolist() if c not in column_order
            ]
            if new_columns:
                # Preserve column order, and add new columns before last ("Temp") column
                column_order[-1:-1] = new_columns
                if verbose:
                    print(
                        f"Additional column{'s' if len(new_columns) > 1 else ''} found in '{out.name}':\n\t{', '.join(new_columns)}"
                    )
                    print()

        # Append new data to existing data from other files
        combined_df = combined_df.append(out_df, sort=True)

    if verbose:
        print(f"All data combined ({len(combined_df)} rows).")

    # Drop unused headers, add units, and make headers human readable
    # "SB DEPTH" is dropped because it is not relevant and often confusing.
    combined_df, column_order = clean_headers_add_units(
        dataframe=combined_df, column_order=column_order, drop_headers=["SB DEPTH"]
    )

    # Export data
    print(f"Exporting combined data to '{export_path}'", end="\r")
    if excel:
        writer = pd.ExcelWriter(
            export_path, engine="xlsxwriter", options={"strings_to_numbers": True}
        )
        combined_df[column_order].to_excel(writer, sheet_name="Sheet5test", index=False)
        writer.save()
    else:
        combined_df[column_order].to_csv(
            export_path,
            index=False,
            float_format="%g",
            encoding=locale.getpreferredencoding(),
        )
    print(f"Exported combined data to '{export_path}' ")

    if verbose:
        end_time = timeit.default_timer()
        print(f"Completed in {round(end_time-start_time,2)} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate data from Geotek MSCL-S machine output."
    )
    parser.add_argument(
        "input_directory",
        type=str,
        help="Directory containing the MSCL folders (themselves containing .out and .raw files).",
    )
    parser.add_argument("output_filename", type=str, help="Name of the output file.")
    parser.add_argument(
        "-s", "--separator", type=str, help="Define file part separator"
    )
    parser.add_argument(
        "-e",
        "--excel",
        action="store_true",
        help="Export combined data as an Excel (xlsx) file.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Display troubleshooting info."
    )

    args = parser.parse_args()

    separator = args.separator if args.separator else "-p"

    aggregate_mscl_data(
        args.input_directory, args.output_filename, separator, args.excel, args.verbose
    )
