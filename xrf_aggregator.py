import timeit
from os import listdir, path
import re
import argparse
import pandas as pd


def join_xrf_data(input_dir, out_filename, e=False, v=False):
  if v:
    start_time = timeit.default_timer()

  if e:
    # pandas won't export an excel file unless it ends with an approved excel extension
    if not (out_filename.endswith('.xlsx') or out_filename.endswith('.xls')):
      out_filename = out_filename + '.xlsx'
  else:
    # pandas seems less concerned with csv export filenames, but just for good measure
    if not out_filename.endswith('.csv'):
      out_filename = out_filename + '.csv'
  
  dir_list = sorted(listdir(path.expanduser(input_dir)))
  xrfs = [f for f in dir_list if re.search(r'.*\.xlsx', f)]

  if v:
    print('Found {} files to join.\n'.format(len(xrfs)))
    print('Ignoring these files in {}:'.format(input_dir[:-1] if input_dir[-1] == '/' else input_dir))
    for f in sorted(set(dir_list)-set(xrfs)):
      print('  '+f)
    print()

  output = pd.DataFrame({'filename' : []})
  column_order = []

  for xrf in xrfs:
    if v:
      print('Opening {}...'.format(xrf), end='\r')
    
    df = pd.read_excel(input_dir+xrf, header=2)

    if v:
      print('Loaded {}    '.format(xrf))

    if not column_order:
      column_order = df.columns.values.tolist()
    else:
      new_elements = [e for e in df.columns.values.tolist() if e not in column_order]
      if len(new_elements) > 0:
        column_order = column_order[:-2] + new_elements + column_order[-2:]
        if v:
          print('Additional elements found: {}'.format(new_elements))
      else:
        if v:
          print('No additional elements found.')
    
    output = output.append(df)

  column_order.remove('filename')

  print('\nExporting data to {}...'.format(out_filename), end='\r')

  if e:
    output[column_order].to_excel(out_filename, index=False)
  else:
    output[column_order].to_csv(out_filename, index=False)

  print('Exported data to {}    \n'.format(out_filename))

  if v:
    end_time = timeit.default_timer()
    print('Completed in {} seconds\n'.format(round(end_time-start_time,2)))

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='stuff')
  parser.add_argument('input_directory', type=str, help='Directory containing the XYZ csv files.')
  parser.add_argument('output_filename', type=str, help='Name of the output file.')
  parser.add_argument('-e', '--excel', action='store_true', help='Export combined data as an xslx file.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Display troubleshooting info.')

  args = parser.parse_args()

  join_xrf_data(args.input_directory, args.output_filename, args.excel, args.verbose)
