import gzip
import json
from glob import glob

from cutils.times import Progress
from pandas import DataFrame, read_csv


def get_meta(path_meta):
    print("reading meta data from path %s" % path_meta)
    meta = read_csv(path_meta, sep="\t", dtype=str)
    meta = meta.set_index(meta.columns[0])
    meta.index.name = 'tweet_id'
    return meta


def collect_results(paths_left, meta_left, paths_right, meta_right):

    print("reading result files")
    records = list()
    pb = Progress(length=len(paths_left), rate=1)
    for p_left, p_right in zip(paths_left, paths_right):

        # read results
        with gzip.open(p_left, "rt") as f:
            r_left = json.loads(f.read())
        with gzip.open(p_right, "rt") as f:
            r_right = json.loads(f.read())

        # name
        try:
            name = r_left['name']
            if name != r_right['name']:
                raise ValueError
            # left
            ids_left = list(r_left['result']['meta']['s_id'].values())
            m = meta_left.loc[ids_left]
            nr_left = len(m)
            dup_left = (m['duplicated'] == "duplicate").sum()
            # right
            ids_right = list(r_right['result']['meta']['s_id'].values())
            m = meta_right.loc[ids_right]
            nr_right = len(m)
            dup_right = (m['duplicated'] == "duplicate").sum()
            # combine
            record = {
                'name': name,
                'freq_left': nr_left,
                'freq_right': nr_right,
                'dup_left': dup_left,
                'dup_right': dup_right
            }
            records.append(record)

        except KeyError:
            pass

        pb.up()

    df = DataFrame.from_records(records)
    df['N_left'] = df['freq_left'].sum()
    df['N_right'] = df['freq_right'].sum()
    df['dup_ratio_left'] = round(df['dup_left'] / df['freq_left'] * 100, 3)
    df['dup_ratio_right'] = round(df['dup_right'] / df['freq_right'] * 100, 3)
    df['freq_1000_tweets_left'] = round(df['freq_left'] / meta_left.shape[0] * 1000, 3)
    df['freq_1000_tweets_right'] = round(df['freq_right'] / meta_right.shape[0] * 1000, 3)
    df['freq_rel_left'] = round(df['freq_left'] / df['N_left'], 3)
    df['freq_rel_right'] = round(df['freq_right'] / df['N_right'], 3)
    df['total'] = df['freq_left'] + df['freq_right']

    return df


if __name__ == '__main__':

    # set paths
    p_meta_bre = "~/corpora/cwb/upload/brexit/brexit-2019/brexit-2019.meta.tsv.gz"
    p_meta_env = "~/corpora/cwb/upload/environment/env2019-v3.tsv.gz"
    path_out = "overview-results-bre-env.tsv.gz"

    # set results path
    paths_left = glob("/home/ausgerechnet/projects/spheroscope/instance-stable/query-results/brexit-2019/*.json.gz")
    paths_right = glob("/home/ausgerechnet/projects/spheroscope/instance-stable/query-results/env2019-v3/*.json.gz")

    # get meta data
    meta_left = get_meta(p_meta_bre)
    meta_right = get_meta(p_meta_env)

    # compare results
    df = collect_results(paths_left, meta_left, paths_right, meta_right)
    df = df.sort_values(by='total', ascending=False)

    df = df[[
        'total',
        'freq_left',
        'freq_right',
        'freq_rel_left',
        'freq_rel_right',
        'freq_1000_tweets_left',
        'freq_1000_tweets_right',
        'dup_ratio_left',
        'dup_ratio_right',
        'name'
    ]]

    df.to_csv(path_out, sep="\t", compression="gzip", index=False)
