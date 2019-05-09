import timeit
from gooey import Gooey, GooeyParser
import mscl_aggregator as mscl_s
import xyz_aggregator as mscl_xyz


@Gooey
def main():
  parser = GooeyParser(description='Aggregate data from Geotek machine outputs.')
  input_output = parser.add_argument_group(gooey_options={'columns': 1})
  input_output.add_argument('input_directory', type=str, widget='DirChooser', help='Directory containing the MSCL folders or files.')
  parser.add_argument('output_filename', type=str, help='Name of the output file.')
  parser.add_argument('data_type', choices=['MSCL-S', 'MSCL-XYZ', 'XRF'])
  parser.add_argument('-e', '--excel', action='store_true', help='Export combined data as an Excel (xlsx) file.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Display troubleshooting info.')

  args = parser.parse_args()

  if args.data_type == 'MSCL-S':
    mscl_s.aggregate_mscl_data(args.input_directory, args.output_filename, args.excel, args.verbose)
  elif args.data_type == 'MSCL-XYZ':
    print('Soon.')
  elif args.data_type == 'XRF':
    print('Not yet implemented.')
  else:
    print(f"Something went wrong. Invalid data type: {args.data_type}")


if __name__ == '__main__':
  main()

