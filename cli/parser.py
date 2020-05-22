import argparse
import sys


def _create_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Commands',
                                       description='Actions to perform',
                                       help='Commands')

    # 'Delete' command
    parser_delete = subparsers.add_parser('delete')

    # List of directories from which to delete duplicates
    parser.add_argument('dirs',
                        metavar='Directory List',
                        nargs='*',
                        help='Path(s) to directories to search, separated by space',
                        action='store')

    # Optional recursive delete
    parser.add_argument('-r',
                        '--recursive',
                        metavar='Directory List',
                        type=list,
                        nargs='*',
                        help='Enable recursive search for all provided path(s).'
                             'If you only want to recursively search some path(s), but not all,'
                             'include them here',
                        action='store')

    # Optional dry run (prints duplicates but doesn't delete them)
    parser.add_argument('-dry',
                        '--dry',
                        help='Executes as dry run; prints duplicate files but does not make any changes',
                        action='store_true')

    return parser


def main():
    args = _create_parser().parse_args(sys.argv)
    print(args)


if __name__ == "__main__":
    main()
