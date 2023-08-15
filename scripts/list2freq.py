from argparse import ArgumentParser

from pandas import DataFrame, read_csv


def main(path_in, path_out, col):
    print('reading')
    df = read_csv(path_in, sep="\t",
                  header=None, quoting=3, keep_default_na=False)
    print('counting')
    df = DataFrame(df[col].value_counts())
    print('writing')
    df.to_csv(path_out, sep="\t", header=None, compression="gzip")


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("path_in",
                        type=str,
                        help="path to list of items")
    parser.add_argument("path_out",
                        type=str,
                        help="path to save counts to (.tsv.gz)")
    parser.add_argument("--col",
                        "-c",
                        type=int,
                        dest="col",
                        default=1,
                        help="0-based column to count")
    args = parser.parse_args()

    main(args.path_in, args.path_out, col=args.col)
