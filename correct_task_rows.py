import numpy as np
import pandas as pd
import os
from tqdm import tqdm


def fix(data, metrics):
    '''
        Takes in a data-dataframe and a metrics-dataframe, read from Tobii-generated tsv files.
        Corrects the task start and end times by finding start and end time of when a task AOI is active. 
    '''
    new_col = [np.nan]*len(data)
    media = metrics[metrics['TOI'] == 'Entire Recording']['Media'].iloc[0]
    for task in range(1, 7):
        aoi = f'AOI hit [{media} - Task{task}.Line1]'
        rows = data[(data[aoi] == 0) | (data[aoi] == 1)]

        start_index = rows.index[0]
        end_index = rows.index[-1]
        new_col[start_index:end_index + 1] = [f'Task{task}']*(end_index-start_index + 1)
    data['Task'] = new_col
    return data


def main():
    '''Fixes task times for all files in the data folder.'''

    usernames = pd.read_csv('./data/usernames.csv', delimiter='\t')
    usernames = sorted(list(usernames[(usernames['helpType'] == 0) | (usernames['helpType'] == 2)]['username']))
    for username in usernames:
        df = pd.read_csv(f'./data/data/{username}_data.tsv', delimiter='\t')
        metrics = pd.read_csv(f'./data/metrics/{username}_metrics_interval.tsv', '\t')
        df = fix(df, metrics)
        df.to_csv(f'./data/new_data/{username}.csv', index=False)


if __name__ == '__main__':
    main()
