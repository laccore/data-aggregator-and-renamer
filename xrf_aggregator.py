import timeit
from os import scandir, path
import re
import argparse
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
      if len(export_filename.split('.')) > 1:
        export_filename = '.'.join(export_filename.split('.')[0:-1]) + '.xlsx'
      else:
        export_filename += '.xlsx'
  else:
    if extension != 'csv':
      if len(export_filename.split('.')) > 1:
        export_filename = '.'.join(export_filename.split('.')[0:-1]) + '.csv'
      else:
        export_filename += '.csv'

  return export_filename


def process_core_id(core_id):
  ''' This function splits all parts of a LacCore CoreID, casts the numeric 
  portions as ints (so sorting works properly), and returns a tuple with all 
  sortable parts separated. Used for sorting a directory list. 

  LacCore Core IDs are in the format 
  PROJECT-[LAKENAME][2DIGITYEAR]-[SITE][HOLE]-[CORE][TOOL]-SECTION
  e.g. PROJ-LAK19-1A-1L-1
  '''
  parts = core_id.split(' ')[0].split('-')

  return (
    *parts[:2],
    int(parts[2][:-1]),
    parts[2][-1],
    int(parts[3][:-1]),
    parts[3][-1],
    int(parts[-1])
  )


def generate_file_list(input_dir, verbose=False):
  '''Rewrite after code rewrite
  
  '''

  file_list = []

  with scandir(input_dir) as it:
    dir_list = [entry for entry in it 
                if entry.is_dir()
                and not entry.name.startswith('.')
                and not '_xr' in entry.name.lower()]
    dir_list = sorted(dir_list, key=lambda d: process_core_id(d.name))
    for d in dir_list:
      print(d.name)

  # for d in dir_list:
  #   with scandir(d) as it:
  #     f_list = [entry for entry in it
  #               if not entry.name.startswith('.') 
  #               and entry.is_file()
  #               and entry.name.split('.')[-1] in ['out', 'raw']]
  #     f_list = sorted(f_list, key=lambda f: f.name.split('.')[-1])
  #     f_list = [d] + f_list

  #   if len(f_list) != 3:
  #     print(f"ERROR: {'more' if len(f_list) > 3 else 'less'} than two files with extension .raw or .out were found.")
  #     print(f'Exactly one of each file required in folder {d.name}.')
  #     exit(1)

  #   file_list.append(f_list)
  
  # if verbose:
  #   print(f'Found data in {len(file_list)} folders to join.')
  #   for folder in file_list:
  #     print(f'  {folder[0].name}')
  #   print()

  return file_list


def aggregate_xrf_data(input_dir, out_filename, excel=False, verbose=False):
  if verbose:
    start_time = timeit.default_timer()

  export_filename = validate_export_filename(out_filename, excel)
  if verbose and export_filename != out_filename:
    print(f"Adjusted export filename to '{export_filename}'")
  
  export_path = path.join(input_dir, export_filename)
  
  xrfs = generate_file_list(input_dir, verbose)

  # does pandas need an initial column?
  output = pd.DataFrame({'filename' : []})

  # need to specify a column order for export file
  column_order = []

  for xrf in xrfs:
    if verbose:
      print('Opening {}...'.format(xrf), end='\r')
    
    # load file, first two rows are junk data so start at row 3 (zero indexed)
    df = pd.read_excel(path.join(input_dir,xrf), header=2)

    if verbose:
      print('Loaded {}    '.format(xrf))

    if not column_order:
      column_order = df.columns.values.tolist()
    else:
      new_elements = [e for e in df.columns.values.tolist() if e not in column_order]
      if new_elements:
        # preserve column order, but add new elements before last two columns (cr coh, cr incoh)
        column_order = column_order[:-2] + new_elements + column_order[-2:]
        if verbose:
          print('Additional elements found: {}'.format(new_elements))
      # else:
      #   if v:
      #     print('No additional elements found.')
    
    output = output.append(df, sort=True)

  # filename value is junk and we don't want to export it
  column_order.remove('filename')

  if verbose:
    print('\nExporting data to {}...'.format(export_path), end='\r')

  if excel:
    output[column_order].to_excel(export_path, index=False)
  else:
    output[column_order].to_csv(export_path, index=False)

  print('Exported data to {}    \n'.format(export_path))

  if verbose:
    end_time = timeit.default_timer()
    print('Completed in {} seconds\n'.format(round(end_time-start_time,2)))

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='stuff')
  parser.add_argument('input_directory', type=str, help='Directory containing the XRF Excel files.')
  parser.add_argument('output_filename', type=str, help='Name of the output file.')
  parser.add_argument('-e', '--excel', action='store_true', help='Export combined data as an xslx file.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Display troubleshooting info.')

  args = parser.parse_args()

  generate_file_list(args.input_directory)
  # aggregate_xrf_data(args.input_directory, args.output_filename, args.excel, args.verbose)
