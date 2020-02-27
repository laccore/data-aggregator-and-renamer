import timeit
from gooey import Gooey, GooeyParser
import mscl_aggregator as mst
import xyz_aggregator as xyz
import xrf_aggregator as xrf
import renamer


@Gooey(
    program_name="Data Aggregator and Renamer ",
    navigation="TABBED",
    default_size=(600, 680),
)
def main():
    parser = GooeyParser(
        description="Aggregate and assign CoreID names to data from Geotek and Itrax machines."
    )

    subs = parser.add_subparsers(help="commands", dest="command")

    mst_parser = subs.add_parser("MSCL-S", help="Combine whole-core data.")
    input_output_mst = mst_parser.add_argument_group(gooey_options={"columns": 1})
    input_output_mst.add_argument(
        "input_directory",
        metavar="Input Directory",
        type=str,
        widget="DirChooser",
        help="Directory containing the MSCL-S folders.",
    )
    input_output_mst.add_argument(
        "output_filename",
        metavar="Output Filename",
        type=str,
        help="Name of the combined output file.",
    )
    options_mst = mst_parser.add_argument_group("Options", gooey_options={"columns": 1})
    options_mst.add_argument(
        "-e",
        "--excel",
        metavar="Export as Excel ",
        action="store_true",
        help="Export combined data as an Excel (xlsx) file.",
    )
    options_mst.add_argument(
        "-v",
        "--verbose",
        metavar="Verbose ",
        action="store_true",
        help="Display troubleshooting info.",
    )

    xyz_parser = subs.add_parser("MSCL-XYZ", help="Combine split-core data.")
    input_output_xyz = xyz_parser.add_argument_group(gooey_options={"columns": 1})
    input_output_xyz.add_argument(
        "input_directory",
        metavar="Input Directory",
        type=str,
        widget="DirChooser",
        help="Directory containing the MSCL-XYZ folders.",
    )
    input_output_xyz.add_argument(
        "output_filename",
        metavar="Output Filename",
        type=str,
        help="Name of the combined output file.",
    )
    options_xyz = xyz_parser.add_argument_group("Options", gooey_options={"columns": 1})
    options_xyz.add_argument(
        "-f",
        "--filter",
        metavar="Filter bad MS values",
        action="store_true",
        help="Filter magnetic susceptibility values < -50 (machine error) ",
    )
    options_xyz.add_argument(
        "-e",
        "--excel",
        metavar="Export as Excel ",
        action="store_true",
        help="Export combined data as an Excel (xlsx) file.",
    )
    options_xyz.add_argument(
        "-v",
        "--verbose",
        metavar="Verbose ",
        action="store_true",
        help="Display troubleshooting info.",
    )

    xrf_parser = subs.add_parser("XRF", help="Combine XRF data.")
    input_output_xrf = xrf_parser.add_argument_group(gooey_options={"columns": 1})
    input_output_xrf.add_argument(
        "input_directory",
        metavar="Input Directory",
        type=str,
        widget="DirChooser",
        help="Directory containing the XRF folders.",
    )
    input_output_xrf.add_argument(
        "output_filename",
        metavar="Output Filename",
        type=str,
        help="Name of the combined output file.",
    )
    options_xrf = xrf_parser.add_argument_group("Options", gooey_options={"columns": 1})
    options_xrf.add_argument(
        "-s",
        "--sitehole",
        metavar="Export by SiteHole ",
        action="store_true",
        help="Split aggregated data by SiteHole and export each file individually.",
    )
    options_xrf.add_argument(
        "-e",
        "--excel",
        metavar="Export as Excel ",
        action="store_true",
        help="Export combined data as an Excel (xlsx) file.",
    )
    options_xrf.add_argument(
        "-v",
        "--verbose",
        metavar="Verbose ",
        action="store_true",
        help="Display troubleshooting info.",
    )

    renamer_parser = subs.add_parser(
        "Rename", help="Rename aggregated data with CoreIDs"
    )
    input_output_renamer = renamer_parser.add_argument_group(
        gooey_options={"columns": 1}
    )
    input_output_renamer.add_argument(
        "input_file",
        widget="FileChooser",
        metavar="Input file (without CoreIDs)",
        help="Name of input file.",
    )
    input_output_renamer.add_argument(
        "corelist",
        widget="FileChooser",
        metavar="Core list file",
        help="CSV in the format coreID,sectionNumber",
    )
    options_renamer = renamer_parser.add_argument_group(
        "Optional Parameters ",
        "The program will try to make sensible choices if these are left blank.",
        gooey_options={"columns": 2},
    )
    options_renamer.add_argument(
        "-o",
        "--output_filename",
        metavar="Output filename",
        type=str,
        help="Name of the output file.",
    )
    options_renamer.add_argument(
        "-v",
        "--verbose",
        metavar="Verbose ",
        action="store_true",
        help="Print troubleshooting information.",
    )
    options_renamer.add_argument(
        "-s",
        "--section_column",
        type=int,
        metavar="Section Number Column",
        help="Column number the section numbers are in (count starts at 0).",
    )
    options_renamer.add_argument(
        "-d",
        "--depth_column",
        type=int,
        metavar="Section Depth Column",
        help="Column number the section depths are in (count starts at 0).",
    )

    args = parser.parse_args()

    if args.command == "MSCL-S":
        mst.aggregate_mscl_data(
            input_dir=args.input_directory,
            out_filename=args.output_filename,
            excel=args.excel,
            verbose=args.verbose,
        )
    elif args.command == "MSCL-XYZ":
        print(args)
        xyz.aggregate_xyz_data(
            input_dir=args.input_directory,
            out_filename=args.output_filename,
            filter=args.filter,
            excel=args.excel,
            verbose=args.verbose,
        )
    elif args.command == "XRF":
        xrf.aggregate_xrf_data(
            input_dir=args.input_directory,
            out_filename=args.output_filename,
            excel=args.excel,
            sitehole=args.sitehole,
            verbose=args.verbose,
        )
    elif args.command == "Rename":
        renamer.apply_names(
            args.input_file,
            args.corelist,
            section_column=args.section_column,
            depth_column=args.depth_column,
            output_filename=args.output_filename,
            verbose=args.verbose,
        )
    else:
        print(f"Something went wrong. Invalid data type: {args.data_type}")


if __name__ == "__main__":
    main()
