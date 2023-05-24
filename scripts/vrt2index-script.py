import gzip
import os
from argparse import ArgumentParser
from collections import defaultdict

from cutils.times import Progress
from cutils.vrt import meta2dict


def create_file(path_in, corpus_name, registry_dir, registry_name, data, p_att, s_att):

    preamble = """#!/bin/bash

# name file and target corpus
file_in="{path_in}"
name="{corpus_name}"

# registry
export CORPUS_REGISTRY="{registry_dir}"
registry_file="{registry_file}"

# data
data="{data_dir}"
mkdir -p $data
""".format(registry_dir=registry_dir,
           registry_file=os.path.join(registry_dir, registry_name),
           path_in=path_in,
           corpus_name=corpus_name,
           data_dir=data)

    encode = """
# encode
echo "cwb-encode"
cwb-encode -d $data -f $file_in -R "$registry_file" -xsB -c utf8 {p_att} {s_att}
""".format(p_att=p_att, s_att=s_att)

    cwb_make = """
# cwb-make
echo "cwb-make on remaining attributes"
cwb-make -M 4096 -V "$name"
"""

    return "".join([
        preamble,
        encode,
        cwb_make
    ])


def main(args, registry_dir, data_dir):

    # path_in
    path_in = args.path_in
    dir_in = os.path.dirname(path_in)
    f_name = args.path_in.split("/")[-1].split(".")[0].replace("-", "_").lower()

    # path_out
    if args.path_out is None:
        path_out = os.path.join(dir_in, f_name + ".sh")
        if os.path.exists(path_out) and not args.force:
            raise FileExistsError((
                '"%s" already exists!\n'
                "you can force to overwrite by directly "
                "specifying the path using --path_out or -o\n"
                "or by using --force / -f"
            ) % path_out)
    else:
        path_out = args.path_out

    # corpus_name
    if args.corpus_name is None:
        corpus_name = f_name.upper()
    else:
        corpus_name = args.corpus_name

    # data_dir
    data = os.path.join(data_dir, corpus_name.lower())

    # guess attributes
    guessed_attributes = guess_attributes(path_in, args.cut_off)

    # p_atts
    nr_p_atts = max(guessed_attributes['p_atts'])
    if nr_p_atts > 1:
        print(nr_p_atts)
        p_att = "-P " + " -P ".join(args.p_atts[: nr_p_atts - 1])
    else:
        p_att = ""
    # s_atts
    s_atts = guessed_attributes['s_atts']
    s_att = "-S " + " -S ".join(s_atts)

    # create file contents
    file_contents = create_file(path_in, corpus_name, registry_dir,
                                corpus_name.lower(), data, p_att, s_att)

    # write
    with open(path_out, "wt") as f:
        f.write(file_contents)

    # status
    print("output written to %s" % path_out)


def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return test_f.read(2) == b'\x1f\x8b'


def guess_attributes(path_in, cut_off):

    print("getting attributes")
    s_atts = defaultdict(set)
    p_atts = []

    if is_gz_file(path_in):
        f = gzip.open(path_in, "rt")
    else:
        f = open(path_in, "rt")

    pb = Progress(length=cut_off, rate=100000)
    for line in f:
        if not line.startswith("<?"):
            if line.startswith("<") and not line.startswith("</"):
                typ, ann = parse_s_att(line)
                s_atts[typ] = s_atts[typ].union(ann)
            else:
                p_atts.append(len(line.split("\t")))
        pb.up()
        if pb.c >= cut_off:
            break

    f.close()

    s_atts_new = list()
    for s in s_atts.keys():
        if len(s_atts[s]) == 0:
            s_atts_new.append(s)
        else:
            new = s + ":0+" + "+".join(sorted(list(s_atts[s])))
            s_atts_new.append(new)

    return {
        's_atts': s_atts_new,
        'p_atts': p_atts
    }


def parse_s_att(line):
    row = line.rstrip()
    row = row.rstrip(">").lstrip("<")
    row = row.split(" ")
    typ = row[0]
    ann = set(meta2dict(line, level=typ).keys())
    return typ, ann


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("path_in",
                        type=str,
                        help="path to .vrt.gz to index")
    parser.add_argument("--p_atts",
                        "-p",
                        dest="p_atts",
                        nargs="+",
                        type=str,
                        default=['pos', 'lemma'],
                        help="what p-attributes to index")
    parser.add_argument("--path_out",
                        "-o",
                        dest="path_out",
                        default=None,
                        type=str,
                        help="where to save the bash script")
    parser.add_argument("--name",
                        "-n",
                        dest="corpus_name",
                        default=None,
                        help="corpus name")
    parser.add_argument("--cut_off",
                        "-c",
                        dest="cut_off",
                        type=int,
                        default=1000000,
                        help="how many lines to look at")
    parser.add_argument("--force",
                        "-f",
                        dest="force",
                        default=False,
                        action='store_true',
                        help="overwrite existing output file?")

    args = parser.parse_args()

    registry_dir = "/home/ausgerechnet/corpora/cwb/registry/"
    data_dir = "/home/ausgerechnet/corpora/cwb/data/"

    main(args, registry_dir, data_dir)
