"""
Arguments: input_file.csv [corelist.csv]

You can specify a core list file name, but if none is specified it looks for a file
in the same directory named corelist.csv to use. It will fail if no file is 
specified and corelist.csv doesn't exist.

Examples:
  $ python3 renamer.py DCH_MSCL_raw.csv
  $ python3 renamer.py YLAKE_XYZ.csv YLAKE_core_list.csv

Incorrect command line usage will print an explanation.
"""

import sys
import os.path
import timeit
import argparse
import csv

version = '1.0.0'


def apply_names(input_file, core_list_filename, **kwargs):
  verbose = kwargs['verbose'] if 'verbose' in kwargs else False

  if verbose:
    start_time = timeit.default_timer()

  # Default values
  header_row = 0
  units_row = 1
  start_row = 2

  ### Import the data
  mscl_data = []
  section_list = []

  with open(input_file, 'r', encoding='utf-8-sig') as f:
    mscl_data = [r.strip().split(',') for r in f.read().splitlines()]


  # Find the section number column:
  #   1) check if it was passed via command line/GUI
  #   2) search the row of headers for one of the expected names
  #   3) if neither of those succeed, exit and print an error message
  if 'section_column' in kwargs and kwargs['section_column']:
    section_column = kwargs['section_column']
    if verbose:
      print(f'Section column passed at command line: {section_column}')
  else:
    for col_name in ['SECT NUM', 'Section', 'SectionID']:
      if col_name in mscl_data[header_row]:
        section_column = mscl_data[header_row].index(col_name)
        if verbose:
          print(f"Section number column found in column {section_column} with name '{col_name}'")
        break
    else:
      print("ERROR: Cannot find section number column. Please change section number column name to 'Section', 'SectionID', or 'SECT NUM'.")
      exit(1)

  # Find the section depth column:
  #   1) check if it was passed via command line/GUI
  #   2) search the row of headers for one of the expected names
  #   3) if neither of those succeed, exit and print an error message
  if 'depth_column' in kwargs and kwargs['depth_column']:
    section_depth_column = kwargs['depth_column']
    if verbose:
      print(f'Section depth column passed at command line: {section_depth_column}')
  else:
    for col_name in ['Section Depth', 'SECT DEPTH']:
      if col_name in mscl_data[header_row]:
        section_depth_column = mscl_data[header_row].index(col_name)
        if verbose:
          print(f"Section depth column found in column {section_depth_column} with name '{col_name}'")
        break
    else:
      print("ERROR: Cannot find section depth column. Please change section number column name to 'Section Depth' or 'SECT DEPTH'.")
      exit(1)


  # Build the section list
  with open(core_list_filename, 'r', encoding='utf-8-sig') as f:
    rows = f.read().splitlines()
    section_list = [[int(core_num), core_name] for core_num, core_name in [r.split(',') for r in rows]]

  # Add the filepart_section notation field to the section log
  num_sections = 1
  for i, row in enumerate(section_list):
    if i == 0:
      row.append('1_' + str(section_list[i][0]))
    elif i > 0:
      if section_list[i][0] <= section_list[i-1][0]:
        num_sections += 1
      row.append(str(num_sections) + '_' + str(section_list[i][0]))

  # Build a dictionary for lookup from the list
  sectionDict = {section[2]: section[1] for section in section_list}

  # Add the part_section notation field to the mscl data
  num_sections = 1
  for i, row in enumerate(mscl_data):
    if i == header_row:
      row.append('Part_Section')
    elif i == units_row:
      row.append('')
    elif i == start_row:
      row.append(str(num_sections) + '_' + mscl_data[i][section_column])
    elif i > start_row:
      if int(mscl_data[i][section_column]) < int(mscl_data[i-1][section_column]):
        num_sections += 1
      elif ((int(mscl_data[i][section_column]) == int(mscl_data[i-1][section_column])) & (float(mscl_data[i][section_depth_column]) < float(mscl_data[i-1][section_depth_column]))):
        num_sections += 1
      row.append(str(num_sections) + '_' + mscl_data[i][section_column])
    else:
      if verbose:
        print(f'Ignored row {i} (not header or units row and before start row):\n{row}')


  ### Build the export lists
  matched_data = []
  unmatched_data = []

  # Build the export lists, replacing the geotek file section number with the
  # coreID and removing the extra part_section column if the row was matched.
  for row in mscl_data[start_row:]:
    if row[-1] in sectionDict.keys():
      row[section_column] = sectionDict[row[-1]]
      matched_data.append(row[:-1])
    else:
      unmatched_data.append(row)

  # Build export names
  if 'output_filename' in kwargs and kwargs['output_filename']:
    matched_filename = kwargs['output_filename']
  elif 'unnamed' in input_file:
    matched_filename = input_file.replace('_unnamed','')
  else:
    matched_filename = input_file.split('.')[0] + '_coreID.csv'
  
  unmatched_filename = '.'.join(input_file.split('.')[:-1]) + '_unmatched.csv'

  ### Export matched data
  with open(matched_filename, 'w', encoding='utf-8-sig') as f:
    csvwriter = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(mscl_data[header_row][:-1])
    csvwriter.writerow(mscl_data[units_row][:-1])
    for r in matched_data:
      csvwriter.writerow(r)

  ### Export unmatched data
  if len(unmatched_data) != 0:
    with open(unmatched_filename, 'w', encoding='utf-8-sig') as f:
      csvwriter = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
      csvwriter.writerow(mscl_data[header_row])
      csvwriter.writerow(mscl_data[units_row])
      for r in unmatched_data:
        csvwriter.writerow(r)


  ### Reporting stuff
  # Create a set to check unique cores names
  named_set = set()

  for row in matched_data[start_row:]:
    named_set.add(row[section_column])

  core_name_list = list(sectionDict.values())
  for core_name in sorted(list(set(core_name_list))):
    core_name_count = core_name_list.count(core_name)
    if core_name_count > 1:
      print(f'WARNING: Core {core_name} appears in {core_list_filename} {str(core_name_count)} times.')

  count_diff = len(set(sectionDict.values())) - len(named_set)
  if (count_diff > 0):
    print(f'\nWARNING: Not all cores in {core_list_filename} were used.')
    print(f"The following {str(count_diff)} core {'names were' if count_diff != 1 else 'name was'} not used:")
    for v in sorted(list(set(sectionDict.values()))):
      if (v not in named_set):
        print(f'\t{v}')
    print()


  print(f'{len(matched_data)} rows had section names assigned ({matched_filename}).')
  print('There were no unmatched rows.' if len(unmatched_data) == 0 else f'There were {str(len(unmatched_data))} unmatched rows ({unmatched_filename}).')
  if verbose:
    end_time = timeit.default_timer()
    print(f'Completed in {round((end_time - start_time),2)} seconds.')


def main():
  parser = argparse.ArgumentParser(description='Apply CoreIDs to the output from Geotek MSCL software.')
  parser.add_argument('input_file', type=str, help='Name of input file.')
  parser.add_argument('corelist', type=str, help='Name of the core list file.')
  parser.add_argument('-o', '--output_filename', type=str, help='Name of the output file.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Increase verbosity.')
  parser.add_argument('-s', '--section_column', type=int, help='Column number the section numbers are in (count starts at 0).')
  parser.add_argument('-d', '--depth_column', type=int, help='Column number the section depths are in (count starts at 0).')

  args = parser.parse_args()

  apply_names(args.input_file,
              args.corelist,
              section_column=args.section_column,
              depth_column=args.depth_column,
              output_filename=args.output_filename,
              verbose=args.verbose)

if __name__ == '__main__':
  main()
