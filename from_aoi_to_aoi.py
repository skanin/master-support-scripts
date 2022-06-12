from tqdm import tqdm
import pandas as pd
import os
import json

def min_distance(rect, p):
    '''Finds minimum distance between point p and rectangle rect.'''

    min_x = int(min(rect, key=lambda x: x['X'])['X'])
    min_y = int(min(rect, key=lambda x: x['Y'])['Y'])
    max_x = int(max(rect, key=lambda x: x['X'])['X'])
    max_y = int(max(rect, key=lambda x: x['Y'])['Y'])
    
    dx = max(min_x - p[0], 0, p[0] - max_x);
    dy = max(min_y - p[1], 0, p[1] - max_y);
    
    distance = (dx*dx + dy*dy)**(1/2)
    
    return distance

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

    # Read all AOIs
    aois = json.load(open('./data/aois/all_aois.aois'))
    aois = list(map(lambda x: [x['Name'], x['KeyFrames'][0]['Vertices']], aois['Aois']))

    for aoi in aois: # There was a problem with the Task5.Bug1 AOI, where it had been placed in the wrong line. This fixes that, and does not affect the results.
        if aoi[0] == 'Task5.Bug1':
            aoi[1] = list(filter(lambda x: x[0] == 'Task5.Line15', aois))[0][1]

    # Read usernames
    usernames = pd.read_csv('./data/usernames.csv', delimiter='\t')
    usernames = usernames[usernames['helpType'] == 2]['username'].values
    
    # Use these columns when reading data files. We do not need all columns
    usecols = ['HelpType', 'Participant name', 'Eye movement type index', 'Recording timestamp', 'Task', 'Eye movement type', 'Fixation point X', 'Fixation point Y']
    
    # Read one data file, get the AOI hit-columns
    df = pd.read_csv('./data/data_with_aoi_names_fix/afraidphyllida.csv')
    aoi_hit_cols = [col for col in df.columns if 'aoi.hit' in col.lower()] + [f'AOI.Hit.Task{i}.Help' for i in range(1,7)]
    usecols.extend(aoi_hit_cols)
    usecols.remove('AOI.Hit.Task5.Line15')

    rows = []
    for file in tqdm(list(filter(lambda x: x.split('.')[0] in usernames, os.listdir('./data/data_with_aoi_names_fix')))):
        if 'expert' in file:
            # We do not care about the expert
            continue
            
        # Read data file
        df = pd.read_csv(f'./data/data_with_aoi_names_fix/{file}', usecols=usecols)
        
        # Get participant name
        partic = df.iloc[0]['Participant name']
            
        for task in range(1, 7): # Loop through tasks       
            prev_aoi = '' # Save previous AOI

            # Get task dataframe
            taskdf = df[df['Task'] == f'Task{task}'].reset_index().sort_values('Recording timestamp')
            
            # Get indicies of fixations in task
            inds = taskdf[(taskdf['Eye movement type'] == 'Fixation')]['Eye movement type index'].unique()
            
            for ind in inds: # Loop through fixations
                # Get fixation dataframe
                fix = taskdf[(taskdf['Eye movement type index'] == ind) & (taskdf['Eye movement type'] == 'Fixation')]
                
                # Get the AOI that was hit
                aoi_hit = get_aoi(fix, f'Task{task}')
                
                if aoi_hit == '':
                    # No AOI was hit, set it to "NoAOI"
                    aoi_hit = f'AOI.Hit.Task{task}.NoAOI'
                    
                if not aoi_hit.endswith('Help') and prev_aoi.endswith('Help'):
                    # We have found a fixation after a help-fixation.

                    # Find X and Y values for the fixation
                    x, y = fix['Fixation point X'].iloc[0], fix['Fixation point Y'].iloc[0]
                    
                    to_add = {
                        'From': prev_aoi,
                        'To': aoi_hit,
                        'X': x,
                        'Y': y,
                        'Participant': partic,
                        'Distance.bug1': -1,
                        'Distance.bug2': -1
                    }
                    
                    if task in (3, 5):
                        # If we are in task 3 or 5, we have two bugs. Find distances to each
                        for i in range(1,3):
                            rect = list(filter(lambda x: x[0] == f'Task{task}.Bug{i}', aois))[0][1]
                            to_add[f'Distance.bug{i}'] = min_distance(rect, (x, y)) 
                    elif task == 1:
                        # Task 1 has only one bug
                        rect = list(filter(lambda x: x[0] == f'Task1.Bug', aois))[0][1]
                        to_add[f'Distance.bug1'] = min_distance(rect, (x, y)) 
                    
                    rows.append(to_add)
                
                # Update prevous AOI
                prev_aoi = aoi_hit

    # Create dataframe of list            
    fixations_df = pd.DataFrame(rows)

    # Save dataframe
    fixations_df.to_csv('./data/to_from_fixations.csv', index=False)

if __name__ == '__main__':
    main()
