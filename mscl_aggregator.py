import timeit
from os import scandir
import argparse
import pandas as pd
import xlsxwriter

def generate_file_list(input_dir):
  '''Comb through directories to generate list of files to combine.

  Given the input directory, scan through all directories and collect 
  the paired files needed to aggregate data (out and raw).
  
  Returns a nested list of pairs of DirEntry objects.
  '''

  file_list = []

  with scandir(input_dir) as it:
    dir_list = [entry for entry in it 
                if not entry.name.startswith('.') 
                and entry.is_dir()]
    # Sort folders by the "_part##" token, which is most consistently correct
    dir_list = sorted(dir_list, key=lambda d: d.name.split('_')[-1])  

  for d in dir_list:
    with scandir(d) as it:
      f_list = [entry for entry in it
                if not entry.name.startswith('.') 
                and entry.is_file()
                and entry.name.split('.')[-1] in ['out', 'raw']]
      f_list = sorted(f_list, key=lambda f: f.name.split('.')[-1])
      f_list = [d] + f_list

    if len(f_list) != 3:
      print(f"ERROR: {'more' if len(f_list) > 3 else 'less'} than two files with extension .raw or .out were found.")
      print(f'Exactly one of each file required in folder {d.name}.')
      exit(1)

    file_list.append(f_list)

  return file_list


def validate_export_filename(export_filename, excel):
  '''Ensure export extension matches flag, return corrected filename.

  xlswriter won't export an Excel file unless the file extension is a 
  valid Excel file extension (xsls, xls). This script assumes the flag 
  indicates user intention, and will append a correct extension.

  If not using the Excel flag, this ensures the filename ends in .csv.

  Returns the validated/fixed export filename.
  '''

  if excel:
    if export_filename.split('.')[-1] not in ['xlsx', 'xls']:
      export_filename += '.xlsx'
  else:
    if not export_filename.endswith('.csv'):
      export_filename += '.csv'

  return export_filename


def open_and_clean_file(file_path):
  '''Open file in pandas, perform some file cleanup, return a dataframe

  Opens the text files output from the Geotek equipment software 
  with a number of flags, then drops the first row of 'data' which is 
  just the units field.

  Row 0 of data is dropped for both files (it's the units row and will
  be added back in later).

  For .raw files, the second row is also dropped because the Geotek 
  software for the raw files is always off by one compared to the .out
  files.

  Rows are dropped, whitespace is stripped from headers, and the index
  is reset so data aligns later on.

  Notes on files:
  - files are tab-delimited
  - skip the first row (just file metadata)
  - tell pandas to treat empty fields as empty strings, not NaNs
  - the 'latin1' encoding flag is needed to open the .raw files
  '''

  drop_rows = [0, 1] if file_path.name.endswith('.raw') else [0]

  df = pd.read_csv(file_path, 
                   delimiter='\t',
                   skiprows=[0],
                   na_filter=False,
                   encoding='latin1')

  df = df.drop(drop_rows)
  df = df.rename(str.strip, axis='columns')
  df = df.reset_index(drop=True)
  
  return df


def clean_headers_add_units(dataframe, old_headers):
  ''' Drop unwanted headers and add units row to data.

  Any new columns will need to have a units row added to the list 
  below, which is converted into a dict which is converted into 
  a pandas dataframe which is then concatenated to the front of the 
  combined data.

  'SB DEPTH' is dropped because it is not relevant and often confusing.
  '''

  units_file = 'units.txt'
  headers_file = 'readable_headers.txt'
  drop_headers = ['SB DEPTH']

  with open(units_file, 'r+') as f:
    headers_units = [r.split(',') for r in f.read().splitlines()]
    units = {item[0]: item[1] for item in headers_units}

  with open(headers_file, 'r+') as f:
    readable_headers = [r.split(',') for r in f.read().splitlines()]
    new_headers = {item[0]: item[1] for item in readable_headers}

  # Remove unwanted column headers
  for dh in drop_headers:
    if dh in old_headers:
      old_headers.remove(dh)

  # Display warnings if an unrecognized machine header is seen
  for header in old_headers:
    if header not in units:
      print(f"WARNING: no associated units for header '{header}'.")
    if header not in new_headers:
      print(f"WARNING: no associated readable header for header '{header}'.")
  
  # Add units row
  dataframe = pd.concat([pd.DataFrame([units]), dataframe], ignore_index=True)

  # Fix headers
  dataframe = dataframe.rename(columns=new_headers)
  headers = [new_headers[header] for header in old_headers]

  return dataframe, headers


def aggregate_mscl_data(input_dir, out_filename, excel=False, verbose=False):
  ''' Aggregate cleaned data from different files and folders, export.

  '''

  start_time = timeit.default_timer()

  file_list = generate_file_list(input_dir)
  if verbose:
    print(f'Found data in {len(file_list)} folders to join.')
    for folder in file_list:
      print(f'  {folder[0].name}')
    print()

  export_filename = validate_export_filename(out_filename, excel)
  if verbose and export_filename != out_filename:
    print(f"Adjusted export filename to '{export_filename}'")

  # Initialize an empty dataframe to hold combined data
  combined_df = pd.DataFrame()

  # Need to specify column order to match expected output
  column_order = []

  # Start combining data
  for d, out, raw in file_list:
    out_df = open_and_clean_file(out)
    raw_df = open_and_clean_file(raw)

    if verbose:
      print(f'Loaded files from {d.name}')
      print(f'  {out.name}\t({len(out_df)} rows)')
      print(f'  {raw.name}\t({len(raw_df)} rows)')
      print()
    
    if (len(raw_df)-len(out_df)) != 0:
      print('ERROR: Length of .out file and .raw file are not equal. What should happen here? Exiting.')
      exit(1)
    
    # Add 'Temp' column from .raw file to .out file dataframe
    out_df['Temp'] = raw_df['Temp']

    # This records column order for the first file, then adds 
    # successive columns at the second to last place, keeping Temp
    # in the last position. The dataframe remains unordered, but 
    # when exporting the order will be applied.
    if not column_order:
      column_order = out_df.columns.values.tolist()
    else:
      new_columns = [c for c in out_df.columns.values.tolist() if c not in column_order]
      if new_columns:
        # Preserve column order, and add new columns before last ('Temp') column
        column_order[-1:-1] = new_columns
        if verbose:
          print(f"Additional column{'s' if len(new_columns) > 1 else ''} found in \'{out.name}\':\n\t{', '.join(new_columns)}")
          print()

    # Append new data to existing data from other files
    combined_df = combined_df.append(out_df)
  
  if verbose:
    print(f'All data combined ({len(combined_df)} rows).')
  
  # Drop unused headers, add units, and make headers human readable
  combined_df, column_order = clean_headers_add_units(combined_df, column_order)

  # Export data
  print(f"Exporting combined data to '{export_filename}'", end='\r')
  if excel:
    writer = pd.ExcelWriter(export_filename, engine='xlsxwriter', options={'strings_to_numbers': True})
    combined_df[column_order].to_excel(writer, sheet_name='Sheet5test', index=False)
    writer.save()
  else:
    combined_df[column_order].to_csv(export_filename, index=False, float_format='%g', encoding='utf-8-sig')
  print(f"Exported combined data to '{export_filename}' ")

  if verbose:
    end_time = timeit.default_timer()
    print(f'Completed in {round(end_time-start_time,2)} seconds.')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Aggregate data from Geotek MSCL machine output.')
  parser.add_argument('input_directory', type=str, help='Directory containing the MSCL folders (themselves containing .out and .raw files).')
  parser.add_argument('output_filename', type=str, help='Name of the output file.')
  parser.add_argument('-e', '--excel', action='store_true', help='Export combined data as an Excel (xlsx) file.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Display troubleshooting info.')

  args = parser.parse_args()

  aggregate_mscl_data(args.input_directory, args.output_filename, args.excel, args.verbose)
