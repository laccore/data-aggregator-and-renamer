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

  if verbose:
    print(f'Scanning subfolders of {input_dir} for .xslx files.')

  file_list = []

  with scandir(input_dir) as it:
    dir_list = [entry for entry in it 
                if entry.is_dir()
                and not entry.name.startswith('.')
                and not '_xr' in entry.name.lower()]
    dir_list = sorted(dir_list, key=lambda d: process_core_id(d.name))

  for d in dir_list:
    with scandir(d) as it:
      f_list = [entry for entry in it
                if not entry.name.startswith('.') 
                and entry.is_file()
                and entry.name.split('.')[-1] == 'xlsx']

    if len(f_list) != 1:
      print(f'ERROR: {len(f_list)} files with extension .xlsx were found.')
      print(f'Exactly one xslx file required in folder {d.name}.')
      exit(1)

    file_list.append(f_list[0])
  
  if verbose:
    print(f'Found data in {len(file_list)} folders to aggregate:')
    for f in file_list:
      print(f"  {f.path.split('/')[-2]}")
    print()

  return file_list


def aggregate_xrf_data(input_dir, out_filename, excel=False, sitehole=False, verbose=False):
  if verbose:
    start_time = timeit.default_timer()

  export_filename = validate_export_filename(out_filename, excel)
  if verbose and export_filename != out_filename:
    print(f"Adjusted export filename to '{export_filename}'")
    
  xrfs = generate_file_list(input_dir, verbose)

  # does pandas need an initial column?
  output = pd.DataFrame({'filename' : []})

  # need to specify a column order for export file
  column_order = []

  for xrf in xrfs:
    if verbose:
      print('Opening {}...'.format(xrf.name), end='\r')
    
    # load file, first two rows are junk data so start at row 3 (zero indexed)
    df = pd.read_excel(path.join(input_dir,xrf), header=2)

    if verbose:
      print('Loaded {}    '.format(xrf.name))

    if not column_order:
      column_order = df.columns.values.tolist()
    else:
      new_elements = [e for e in df.columns.values.tolist() if e not in column_order]
      if new_elements:
        # preserve column order, but add new elements before last two columns (cr coh, cr incoh)
        column_order = column_order[:-2] + new_elements + column_order[-2:]
        if verbose:
          print(f"Additional element{'s' if len(new_elements) > 1 else ''} found: {', '.join(new_elements)}")
          print()
    
    output = output.append(df, sort=True)

  # don't export column filename
  column_order.remove('filename')

  if verbose:
    print()

  if not sitehole:
    export_path = path.join(input_dir, export_filename)
    print(f'Exporting data ({len(output)} rows) to {export_path}...', end='\r')

    if excel:
      output[column_order].to_excel(export_path, index=False)
    else:
      output[column_order].to_csv(export_path, index=False)
    
    print(f'Exported data ({len(output)} rows) to {export_path}    ')
  
  else:
    if 'SectionID' not in df.columns.values.tolist():
      print("ERROR: column 'SectionID' not found, must be present to export by SiteHole.")
      exit(1)
    # create the sitehole column
    output['shfe'] = output['SectionID'].str.split('-', expand=True)[2]

    holes = output['shfe'].unique()

    for hole in holes:
      filtered_export_filename = '.'.join(export_filename.split('.')[:-1]) + '-' + hole + '.' + export_filename.split('.')[-1]
      export_path = path.join(input_dir, filtered_export_filename)

      filtered_data = output.loc[output['shfe'] == hole]

      print(f'Exporting data from SiteHole {hole} ({len(filtered_data)} rows) to {filtered_export_filename}...', end='\r')

      if excel:
        filtered_data[column_order].to_excel(export_path, index=False)
      else:
        filtered_data[column_order].to_csv(export_path, index=False)
    
      print(f'Exported data from SiteHole {hole} ({len(filtered_data)} rows) to {filtered_export_filename}    ')

  if verbose:
    end_time = timeit.default_timer()
    print()
    print('Completed in {} seconds'.format(round(end_time-start_time,2)))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='stuff')
  parser.add_argument('input_directory', type=str, help='Directory containing the XRF Excel files.')
  parser.add_argument('output_filename', type=str, help='Name of the output file.')
  parser.add_argument('-e', '--excel', action='store_true', help='Export combined data as an xslx file.')
  parser.add_argument('-s', '--sitehole', action='store_true', help='Export data to multiple files, grouped by SiteHole.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Display troubleshooting info.')

  args = parser.parse_args()

  aggregate_xrf_data(input_dir=args.input_directory,
                     out_filename=args.output_filename,
                     excel=args.excel,
                     sitehole=args.sitehole,
                     verbose=args.verbose)
