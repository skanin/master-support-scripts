import os
import pandas as pd


def fix_aoi_names(df):
    '''
        Takes a Tobii data dataframe and fixes the AOI names.
    '''

    old_names = list(filter(lambda x: 'AOI hit' in x, df.columns))
    new_names = dict([(x, 'AOI.Hit.' + x.split('-')[1][1:x.split('-')[1].rindex(']')]) for x in old_names])
    return df.rename(columns=new_names, inplace=False)


def main():
    for file in os.listdir('./data/new_data'):
        fix_aoi_names(pd.read_csv(f'./data/new_data/{file}')).to_csv(f'./data/data_with_aoi_names_fix/{file}')


if __name__ == '__main__':
    main()
