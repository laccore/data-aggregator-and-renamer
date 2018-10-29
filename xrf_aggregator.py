import timeit
from os import listdir, path
import re
import argparse

def join_xyz_data(input_dir, out_filename, v=False):
  if v:
    start_time = timeit.default_timer()
  
  dir_list = sorted(listdir(path.expanduser(input_dir)))
  csvs = [f for f in dir_list if re.search(r'\w+\_XYZ\_[0-9]{8}\_part[0-9]+.*\.csv', f)]
  # regex notes for future me, match the following rules (in order):
  #   any non-whitespace (word) characters 1+ times
  #   the string '_XYZ_'
  #   8 digits (date)
  #   the string '_part' and then any number 1+ times
  #   any characters 0+ times (I'm least sure about this part, but sometimes filenames include weird notes)
  #   files ending in '.csv'

  if v:
    print('Found {} files to join.\n'.format(len(csvs)))
    print('Ignoring these files in {}:'.format(input_dir))
    for f in sorted(set(dir_list)-set(csvs)):
      print('  '+f)
    print()

  headers = ['Depth','Core Depth','Section','Section Depth','Laser Profiler','Magnetic Susceptibility','Greyscale Reflectance','Munsell Colour','CIE X','CIE Y','CIE Z','CIE L*','CIE a*','CIE b*','360','370','380','390','400','410','420','430','440','450','460','470','480','490','500','510','520','530','540','550','560','570','580','590','600','610','620','630','640','650','660','670','680','690','700','710','720','730','740']
  units = ['m','m','','cm','mm','SI','','','','','','','','','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm','nm']

  combined_data = [headers, units]

  def import_csv(infile):
    with open(infile, 'r', encoding='utf-8-sig') as f:
      rawdata = [r.split(',') for r in f.read().splitlines()][4:-1]
    return rawdata

  for csv in csvs:
    if v:
      print('Joining file {}...'.format(csv), end='\r')
    combined_data += import_csv(csv)
    if v:
      print('Joined file {}    '.format(csv))


  print('\nExporting data to {}...'.format(out_filename), end='\r')

  with open(out_filename, 'w', encoding='utf-8-sig') as f:
    for r in combined_data:
      f.write(','.join(r)+'\n')

  print('Exported data to {}    \n'.format(out_filename))
  if v:
    end_time = timeit.default_timer()
    print('Completed in {0} seconds\n'.format(round(end_time-start_time,2)))

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='stuff')
  parser.add_argument('input_directory', type=str, help='Directory containing the XYZ csv files.')
  parser.add_argument('output_filename', type=str, help='Name of the output file.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Display troubleshooting info.')

  args = parser.parse_args()

  join_xyz_data(args.input_directory, args.output_filename, args.verbose)
