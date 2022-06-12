from tqdm import tqdm
import pandas as pd
import numpy as np
import os


def get_aoi(df, task):
    '''
        Takes in a dataframe of fixations and task name.
        Returns which AOI that was hit, if any.
    '''

    col = ''
    row = df.iloc[0]
    for colname in df.filter(regex=f'AOI.Hit.{task}.*').columns:
        if 'Code' in colname:
            continue

        if row[colname]:
            col = colname
            break

    if col == '' and row[f'AOI.Hit.{task}.Code']:
        col = f'AOI.Hit.{task}.Code'

    return col


def main():
    '''Generates fixation and duration dataframes'''

    # Usecols for faster loading of data file. Don't need all columns.
    usecols = ['HelpType', 'Participant name', 'Eye movement type index', 'Recording timestamp',
               'Task', 'Eye movement type', 'Fixation point X', 'Fixation point Y']

    # Read in data file to get all AOI-columns and add them to usecols.
    df = pd.read_csv('./data/data_with_aoi_names_fix/afraidphyllida.csv')
    aoi_hit_cols = [col for col in df.columns if 'aoi.hit' in col.lower()] + [f'AOI.Hit.Task{i}.Help' for i in range(1, 7)]
    usecols.extend(aoi_hit_cols)

    # Read graded study scores and pretest scores. Compute total score for both.
    study = pd.read_csv('./data/corrected_grading.csv')
    study['study_score'] = study[[f'studyTask{i}_points' for i in range(1, 7)]].sum(axis=1)
    pretest = pd.read_csv('./data/graded_pretest_with_helptype.csv')
    pretest['pretest_score'] = pretest[[f'pretest.{i}-1_participant_correct' for i in range(1, 11)]].sum(axis=1)

    # Read all usernames
    usernames = pd.read_csv('./data/usernames.csv', delimiter='\t')
    usernames = sorted(list(usernames[(usernames['helpType'] == 0) | (usernames['helpType'] == 2)]['username']))

    rows = []
    durs = []
    pretest_median = pretest['pretest_score'].median()
    study_median = study['study_score'].median()
    
    for file in tqdm(list(filter(lambda x: x.split('.')[0] in usernames, os.listdir('./data/data_with_aoi_names_fix')))):
        if 'expert' in file:
            # Expert does not have all the same AOIs as the other participants
            df = pd.read_csv('./data/data_with_aoi_names_fix/expert.csv', low_memory=False)
        else:
            df = pd.read_csv(f'./data/data_with_aoi_names_fix/{file}', usecols=usecols)

        if 'expert' not in file:
            # Get Condition, Expertise group and Performance group
            help_type = df.iloc[0]['HelpType']

            partic = df.iloc[0]['Participant name']
            if partic == 'arrograntimperious':
                partic = 'arrogantimperious'

            help_group = 'Help' if help_type == 2 else 'Control'
            expertise = 'high' if pretest[pretest['username'] == partic]['pretest_score'].iloc[0] >= pretest_median else 'low'
            performance = 'high' if study[study['username'] == partic]['study_score'].iloc[0] >= study_median else 'low'
        else:
            # Expert does not have a Condition, Expertise group and Performance group
            help_type = -1
            partic = 'Expert'
            expertise = np.nan
            performance = np.nan
            help_group = np.nan

        for task in range(1, 7): # Iterate through each study task

            # Get dataframe consisting of rows only from current task
            taskdf = df[df['Task'] == f'Task{task}'].reset_index().sort_values('Recording timestamp')

            # Get fixation indicies
            inds = taskdf[(taskdf['Eye movement type'] == 'Fixation')]['Eye movement type index'].unique()
            
            # Find start and end of each task, calculate task duration
            task_start = taskdf['Recording timestamp'].iloc[0]
            task_end = taskdf['Recording timestamp'].iloc[-1]
            task_dur = task_end - task_start

            help_dur = 0
            task_list = []

            for ind in inds:
                # Get dataframe consisting of rows only from current fixation
                fix = taskdf[(taskdf['Eye movement type index'] == ind) & (taskdf['Eye movement type'] == 'Fixation')]

                # Find fixation start and end
                fixation_start = fix['Recording timestamp'].iloc[0]
                fixation_end = fix['Recording timestamp'].iloc[-1]

                # Get the AOI that was hit, and the X and Y coordinates of the fixation
                aoi_hit = get_aoi(fix, f'Task{task}')
                x, y = fix['Fixation point X'].iloc[0], fix['Fixation point Y'].iloc[0]
                
                if aoi_hit == '':
                    # If no AOI was hit, set AOI to "NoAOI"
                    aoi_hit = f'AOI.Hit.Task{task}.NoAOI'

                if aoi_hit == 'AOI.Hit.Task5.Line11_new':
                    # If the AOI was the line 11, set the AOI to "Line11"
                    aoi_hit = 'AOI.Hit.Task5.Line11'

                if aoi_hit.endswith('Help') and help_type == 2:
                    # If the AOI was a help AOI and the participant was a help participant, add the duration to the help duration
                    help_dur += fixation_end - fixation_start

                to_add = {
                    'FixationStart': fixation_start,
                    'FixationEnd': fixation_end,
                    'X': x,
                    'Y': y,
                    'Participant': partic,
                    'TaskStart': task_start,
                    'TaskEnd': task_end,
                    'TaskDuration': task_dur,
                    'Task': f'Task{task}',
                    'AOI': aoi_hit,
                    'HelpType': help_type,
                    'PerformanceGroup': performance,
                    'ExpertiseGroup': expertise,
                    'HelpGroup': help_group
                }
                
                # Add new fixaion
                task_list.append(to_add)

            durations = {}
            for entry in task_list:
                aoi = entry['AOI']
                entry['TaskDuration'] = entry['TaskDuration'] - help_dur # Subtract help duration from task duration
                durations[aoi] = durations.get(aoi, 0) + entry['FixationEnd'] - entry['FixationStart'] # Accumulate fixation duration 

            for entry in durations:
                durations[entry] = durations[entry] / (task_dur - help_dur) # Normalize each duration by task duration

            rows.extend(task_list)

            for f in durations:
                to_add = {
                    'AOI': f,
                    'Duration': durations[f],
                    'Participant': partic,
                    'HelpType': help_type,
                    'PerformanceGroup': performance,
                    'ExpertiseGroup': expertise,
                    'Task': f'Task{task}',
                    'HelpGroup': help_group
                }

                # Add fixation duration
                durs.append(to_add)

    # Create dataframe from rows
    fixations_df = pd.DataFrame(rows)
    durations_df = pd.DataFrame(durs)

    # Save dataframes
    fixations_df.to_csv('./data/fixations.csv', index=False)
    durations_df.to_csv('./data/durations.csv', index=False)


if __name__ == '__main__':
    main()
