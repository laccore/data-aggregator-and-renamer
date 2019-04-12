import pandas as pd

def validate_export_filename(export_filename, excel):
  '''Ensure export extension matches flag, return corrected filename.

  xlswriter won't export an Excel file unless the file extension is a 
  valid Excel file extension (xsls, xls). This script assumes the flag 
  indicates user intention, and will append a correct extension.

  If not using the Excel flag, this ensures the filename ends in .csv.

  Returns the validated/fixed export filename.
  '''

  extension = export_filename.split('.')[-1]

  if excel:
    if extension not in ['xlsx', 'xls']:
      export_filename += '.xlsx'
  else:
    if extension != 'csv':
      export_filename += '.csv'

  return export_filename


def open_and_clean_file(file_path, delimiter, skip_rows, drop_rows, drop_columns=[]):
  '''Open file in pandas, perform some file cleanup, return a dataframe

  Opens the text files output from the Geotek equipment software 
  with a number of flags, then drops the first row of 'data' which is 
  just the units field.

  Rows are dropped, whitespace is stripped from headers, and the index
  is reset so data aligns later on.

  Notes on files:
  - tell pandas to treat empty fields as empty strings, not NaNs
  - the 'latin1' encoding flag is needed to open the .raw files
  '''

  df = pd.read_csv(file_path, 
                   delimiter=delimiter,
                   skiprows=skip_rows,
                   na_filter=False,
                   encoding='latin1')

  df = df.drop(drop_rows)
  df = df.rename(str.strip, axis='columns')
  df = df.reset_index(drop=True)

  if drop_columns:
    cols = [c for c in df.columns if c not in drop_columns]
    return df[cols]
  else:
    return df


def clean_headers_add_units(dataframe, column_order, file_type, drop_headers=[]):
  ''' Drop unwanted headers and add units row to data.

  Any new columns will need to have a units row added to the list 
  below, which is converted into a dict which is converted into 
  a pandas dataframe which is then concatenated to the front of the 
  combined data.
  ''' 

  if file_type == 'mscl':
    units_file = file_type + '_units.txt'
    headers_file = file_type + '_headers.txt'

    with open(units_file, 'r+') as f:
      headers_units = [r.split(',') for r in f.read().splitlines()]
      units = {item[0]: item[1] for item in headers_units}

    with open(headers_file, 'r+') as f:
      readable_headers = [r.split(',') for r in f.read().splitlines()]
      new_headers = {item[0]: item[1] for item in readable_headers}

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
    dataframe = pd.concat([pd.DataFrame([units]), dataframe], ignore_index=True, sort=True)

    # Fix headers
    dataframe = dataframe.rename(columns=new_headers)
    column_order = [new_headers[header] for header in column_order]

  elif file_type == 'xyz':
    headers_units_file = 'xyz_headers_units.txt'

    with open(headers_units_file, 'r+') as f:
      headers_units = [r.split(',') for r in f.read().splitlines()]
    
    # dataframe = dataframe.drop([0])
    dataframe.columns = headers_units[0]
    dataframe = pd.concat([pd.DataFrame(headers_units[1]), dataframe], ignore_index=True, sort=True)
    
    column_order = [header for header in headers_units[0] if header not in drop_headers]

  else:
    print(f"Error: cannot process files of type '{file_type}'. Exiting.")
    exit(1)
  
  return dataframe, column_order
