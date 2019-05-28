import timeit
from gooey import Gooey, GooeyParser
import mscl_aggregator as mst
import xyz_aggregator as xyz
import xrf_aggregator as xrf


@Gooey(program_name='Data Aggregator',
       navigation='TABBED',
       default_size=(600, 650))
def main():
  parser = GooeyParser(description='Aggregate data from Geotek and _____ machine outputs.')

  subs = parser.add_subparsers(help='commands', dest='command')

  mst_parser = subs.add_parser('MSCL-S', help='Combine whole-core data.')
  input_output_mst = mst_parser.add_argument_group(gooey_options={'columns': 1})
  input_output_mst.add_argument('input_directory',
                                metavar='Input Directory',
                                type=str,
                                widget='DirChooser',
                                help='Directory containing the MSCL-S folders.')
  input_output_mst.add_argument('output_filename',
                                metavar='Output Filename',
                                type=str,
                                help='Name of the combined output file.')
  options_mst = mst_parser.add_argument_group('Options', gooey_options={'columns': 1})
  options_mst.add_argument('-e', '--excel',
                           metavar='Export as Excel',
                           action='store_true',
                           help='Export combined data as an Excel (xlsx) file.')
  options_mst.add_argument('-v', '--verbose',
                           metavar='Verbose',
                           action='store_true',
                           help='Display troubleshooting info.')

  xyz_parser = subs.add_parser('MSCL-XYZ', help='Combine split-core data.')
  input_output_xyz = xyz_parser.add_argument_group(gooey_options={'columns': 1})
  input_output_xyz.add_argument('input_directory',
                                metavar='Input Directory',
                                type=str,
                                widget='DirChooser',
                                help='Directory containing the MSCL-XYZ folders.')
  input_output_xyz.add_argument('output_filename',
                                metavar='Output Filename',
                                type=str,
                                help='Name of the combined output file.')
  options_xyz = xyz_parser.add_argument_group('Options', gooey_options={'columns': 1})
  options_xyz.add_argument('-e', '--excel',
                           metavar='Export as Excel',
                           action='store_true',
                           help='Export combined data as an Excel (xlsx) file.')
  options_xyz.add_argument('-v', '--verbose',
                           metavar='Verbose',
                           action='store_true',
                           help='Display troubleshooting info.')

  xrf_parser = subs.add_parser('XRF', help='Combine XRF data.')
  input_output_xrf = xrf_parser.add_argument_group(gooey_options={'columns': 1})
  input_output_xrf.add_argument('input_directory',
                                metavar='Input Directory',
                                type=str,
                                widget='DirChooser',
                                help='Directory containing the XRF folders.')
  input_output_xrf.add_argument('output_filename',
                                metavar='Output Filename',
                                type=str,
                                help='Name of the combined output file.')
  options_xrf = xrf_parser.add_argument_group('Options', gooey_options={'columns': 1})
  options_xrf.add_argument('-s', '--sitehole',
                           metavar='Export by SiteHole',
                           action='store_true',
                           help='Split aggregated data by SiteHole and export each file individually.')
  options_xrf.add_argument('-e', '--excel',
                           metavar='Export as Excel',
                           action='store_true',
                           help='Export combined data as an Excel (xlsx) file.')
  options_xrf.add_argument('-v', '--verbose',
                           metavar='Verbose',
                           action='store_true',
                           help='Display troubleshooting info.')


  args = parser.parse_args()

  if args.command == 'MSCL-S':
    mst.aggregate_mscl_data(input_dir=args.input_directory,
                            out_filename=args.output_filename,
                            excel=args.excel,
                            verbose=args.verbose)
  elif args.command == 'MSCL-XYZ':
    xyz.aggregate_xyz_data(input_dir=args.input_directory,
                            out_filename=args.output_filename,
                            excel=args.excel,
                            verbose=args.verbose)
  elif args.command == 'XRF':
    xrf.aggregate_xrf_data(input_dir=args.input_directory, 
                           out_filename=args.output_filename,
                           excel=args.excel,
                           sitehole=args.sitehole,
                           verbose=args.verbose)
  else:
    print(f"Something went wrong. Invalid data type: {args.data_type}")


if __name__ == '__main__':
  main()

