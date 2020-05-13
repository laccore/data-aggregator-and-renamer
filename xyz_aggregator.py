import timeit
from pathlib import Path
import argparse
import pandas as pd
import xlsxwriter
import locale
import operator


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


def generate_file_list(input_dir):
    """Comb through directories to generate list of files to combine.

    Given the input directory, scan through all directories and collect 
    the xyz csv files.

    Returns a list of PurePath objects.
    """

    file_list = []

    p = Path(input_dir).iterdir()
    dir_list = [
        entry
        for entry in p
        # if "xyz" in entry.name.lower()
        and "_part" in entry.name.lower()
        and entry.is_dir()
        and not entry.name.startswith(".")
    ]
    # Sort folders by the "_part##" token, which is most consistently correct
    # converting the number to float because there have been times where #.5 has been used
    dir_list = sorted(dir_list, key=lambda d: float(d.name.lower().split("_part")[-1]))

    for d in dir_list:
        p = Path(d).iterdir()
        f_list = [
            entry
            for entry in p
            if "xyz" in entry.name.lower()
            and entry.is_file()
            and not entry.name.startswith(".")
            and entry.suffix == ".csv"
        ]
        if len(f_list) > 1:
            print(f"ERROR: more than one file with extension .csv was found.")
            print(f"Only one csv file required in folder {d.name}.")
            exit(1)

        elif len(f_list) == 0:
            print(f"No .csv file was found in {d.name}.")

        else:
            file_list.append(f_list[0])

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
    """

    df = pd.read_csv(
        file_path,
        delimiter=delimiter,
        skiprows=skip_rows,
        na_filter=False,
        encoding="latin1",
        header=None,
    )

    # here begins madness of trying to deal with a poorly formatted csv
    row1 = df.iloc[0].tolist()
    row2 = df.iloc[1].tolist()
    headers = []
    for pos, header in enumerate(row1):
        if header.strip():
            headers.append(header)
        else:
            headers.append(row2[pos].strip())
    df.columns = headers

    df = df.drop(drop_rows)
    df = df.reset_index(drop=True)

    return df


def clean_headers_add_units(dataframe, column_order, drop_headers=[]):
    """ Drop unwanted headers and add units row to data.

    Any new columns will need to have a units row added to the list 
    below, which is converted into a dict which is converted into 
    a pandas dataframe which is then concatenated to the front of the 
    combined data.
    """

    # Format: machine header, readable header, units
    headers_and_units = [
        ["Section", "Section", ""],
        ["Section Depth", "Section Depth", "cm"],
        ["Laser Profiler", "Laser Profiler", "mm"],
        ["Magnetic Susceptibility", "Magnetic Susceptibility", "SI x 10^-5"],
        ["Greyscale Reflectance", "Greyscale Reflectance", ""],
        ["CIE XYZ Colour Space", "CIE X", ""],
        ["Y", "CIE Y", ""],
        ["Z", "CIE Z", ""],
        ["CIE L*a*b* Colour Space", "CIE L*", ""],
        ["a*", "CIE a*", ""],
        ["b*", "CIE b*", ""],
        ["Reflectance (nm)", "360", "nm"],
    ]

    new_headers = {item[0]: item[1] for item in headers_and_units}
    units = {item[0]: item[2] for item in headers_and_units}
    # headers and units for wavelengths 370 to 740 are the same,
    # so we add them programatically
    for wavelength in range(370, 750, 10):
        new_headers[str(wavelength)] = wavelength
        units[str(wavelength)] = "nm"

    # Remove unwanted column headers
    for dh in drop_headers:
        if dh in column_order:
            column_order.remove(dh)

    # Display warnings if an unrecognized machine header is seen
    for header in column_order:
        if header not in units:
            print(f"WARNING: no associated units for header '{header}'.")
        if header not in new_headers:
            print(f"WARNING: no associated readable header for header '{header}'.")

    # Add units row
    dataframe = pd.concat(
        [pd.DataFrame([units]), dataframe], ignore_index=True, sort=True
    )

    # Fix headers
    dataframe = dataframe.rename(columns=new_headers)
    column_order = [new_headers[header] for header in column_order]

    return dataframe, column_order


def filter_invalid_values(dataframe, filters):
    """Filter invalid values (often machine error) from the dataset
    
    filters format: [column title, operator, value]
    e.g., ["MS", "<", -50] will remove all values in the MS column less than -50
    """

    ops = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "=": operator.eq,
    }

    for col_name, op, val in filters:
        dataframe[col_name] = pd.to_numeric(
            dataframe[col_name], errors="coerce"
        ).astype("float64")

        dataframe[col_name] = dataframe[col_name].mask(
            ops[op](dataframe[col_name], val)
        )

    return dataframe


def aggregate_xyz_data(
    input_dir, out_filename, filter=False, excel=False, verbose=False
):
    """ Aggregate cleaned data from different files and folders, export.

    """

    if verbose:
        start_time = timeit.default_timer()

    input_dir = Path(input_dir)

    file_list = generate_file_list(input_dir)
    if verbose:
        print(f"Found data in {len(file_list)} folders to join.")
        for f in file_list:
            print(f"\t{f.parts[-2]}")
        print()

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
    # First two rows are skipped, they are file metadata we don't care about
    # Unit row (row 0) is dropped and added later
    skip_rows = [0, 1]  # skip first two rows, junk data

    # Munsell Colour isn't a column we want, but it is sometimes accidentally exported
    # drop_columns = ['Munsell Colour']

    for file_name in file_list:
        xyz_df = open_and_clean_file(
            file_path=file_name, delimiter=",", skip_rows=skip_rows, drop_rows=[0, 1]
        )

        if verbose and len(xyz_df.columns) < 52:
            print(f"Found only {len(xyz_df.columns)} columns in '{file_name}'")

        if verbose:
            print(
                f"Loaded {len(xyz_df)} rows from {file_name.name} in {file_name.parts[-2]}"
            )

        # This records column order for the first file, then adds
        # successive columns at the end. The dataframe remains unordered,
        # but when exporting the order will be applied.
        if not column_order:
            column_order = xyz_df.columns.values.tolist()
        else:
            new_columns = [
                c for c in xyz_df.columns.values.tolist() if c not in column_order
            ]
            if new_columns:
                # Preserve column order, and add new columns before last ('Temp') column
                for c in new_columns:
                    column_order.append(c)
                if verbose:
                    print(
                        f"Additional column{'s' if len(new_columns) > 1 else ''} found in '{file_name.name}':\n\t{', '.join(new_columns)}"
                    )
                    print()

        combined_df = combined_df.append(xyz_df, sort=True)

    if verbose:
        print(f"All data combined ({len(combined_df)} rows).")

    if filter:
        # Remove invalid values
        filters = [
            ["Magnetic Susceptibility", "<", -50],
        ]
        combined_df = filter_invalid_values(combined_df, filters)

        if verbose:
            print("Filtered invalid magnetic susceptibility values.")

    # Drop unused columns, add units, and make headers human readable
    drop_columns = ["Depth", "Core Depth", "Munsell Colour", "Time Stamp"]
    combined_df, column_order = clean_headers_add_units(
        dataframe=combined_df, column_order=column_order, drop_headers=drop_columns
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
        description="Aggregate data from Geotek MSCL-XYZ machine output."
    )
    parser.add_argument(
        "input_directory", type=str, help="Directory containing the XYZ csv files."
    )
    parser.add_argument("output_filename", type=str, help="Name of the output file.")
    parser.add_argument(
        "-f",
        "--filter",
        action="store_true",
        help="Filter magnetic susceptibility values < -50 (machine error).",
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

    # join_xyz_data(args.input_directory, args.output_filename, args.verbose)
    aggregate_xyz_data(
        args.input_directory,
        args.output_filename,
        args.filter,
        args.excel,
        args.verbose,
    )

