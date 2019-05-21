import timeit
from gooey import Gooey, GooeyParser
import mscl_aggregator as mscl_s
import xyz_aggregator as mscl_xyz


@Gooey(program_name='Data Aggregator')
def main():
  parser = GooeyParser(description='Aggregate data from Geotek and _____ machine outputs.')

  subs = parser.add_subparsers(help='commands', dest='command')

  mscls_parser = subs.add_parser('MSCL-S', help='Combine whole-core data.')
  input_output = mscls_parser.add_argument_group(gooey_options={'columns': 1})
  input_output.add_argument('input_directory',
                            metavar='Input Directory',
                            type=str,
                            widget='DirChooser',
                            help='Directory containing the MSCL folders.')
  input_output.add_argument('output_filename',
                            metavar='Output Filename',
                            type=str,
                            help='Name of the combined output file.')
  options = mscls_parser.add_argument_group('Options', gooey_options={'columns': 1})
  options.add_argument('-e',
                       '--excel',
                       metavar='Export as Excel',
                       action='store_true',
                       help='Export combined data as an Excel (xlsx) file.')
  options.add_argument('-v',
                       '--verbose',
                       metavar='Verbose',
                       action='store_true',
                       help='Display troubleshooting info.')

  msclxyz_parser = subs.add_parser('MSCL-XYZ', help='Combine split-core data.')

  xrf_parser = subs.add_parser('XRF', help='Combine XRF data.')


  args = parser.parse_args()

  if args.command == 'MSCL-S':
    mscl_s.aggregate_mscl_data(args.input_directory, args.output_filename, args.excel, args.verbose)
  elif args.command == 'MSCL-XYZ':
    print('Soon.')
  elif args.command == 'XRF':
    print('Not yet implemented.')
  else:
    print(f"Something went wrong. Invalid data type: {args.data_type}")


if __name__ == '__main__':
  main()

