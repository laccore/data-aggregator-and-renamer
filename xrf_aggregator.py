import timeit
from os import listdir, path
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


def generate_file_list(input_dir, verbose=False):
  '''Comb through directories to generate list of files to combine.

  Given the input directory, scan through all directories and collect 
  the paired files needed to aggregate data (out and raw).
  
  Returns a nested list of pairs of DirEntry objects.
  '''

  file_list = sorted(listdir(path.expanduser(input_dir)))
  xrfs = [f for f in file_list if re.search(r'.*\.xlsx', f)]
  
  if verbose:
    print(f'Found {len(xrfs)} files to join.')
    print('Ignoring these files in {}:'.format(input_dir[:-1] if input_dir[-1] == '/' else input_dir))
    for f in sorted(set(listdir(path.expanduser(input_dir)))-set(xrfs)):
      print(f'\t{f}')
    print()
  
  return xrfs


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

  aggregate_xrf_data(args.input_directory, args.output_filename, args.excel, args.verbose)
