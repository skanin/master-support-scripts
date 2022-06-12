from tqdm import tqdm
import pandas as pd
import numpy as np
import json

aois = json.load(open('./data/aois/all_aois.aois'))
aois = list(map(lambda x: {'name': x['Name'], 'coords': x['KeyFrames'][0]['Vertices']},aois['Aois']))

lengths = {
    'task1': {'bug': {'furthest': 'Line22'}},
    'task3': {'bug1': {'furthest': 'Line1'}, 'bug2': {'furthest': 'Line55'}},
    'task5': {'bug1': {'furthest': 'Line49'}, 'bug2': {'furthest': 'Line49'}},
}


def min_distance(rect1, rect2):
    '''Calculates min distance between two rectangles (AOIs)'''

    x_min1 = int(min(rect1, key=lambda x: x['X'])['X'])
    y_min1 = int(min(rect1, key=lambda x: x['Y'])['Y'])
    x_max1 = int(max(rect1, key=lambda x: x['X'])['X'])
    y_max1 = int(max(rect1, key=lambda x: x['Y'])['Y'])
    
    x_min2 = int(min(rect2, key=lambda x: x['X'])['X'])
    y_min2 = int(min(rect2, key=lambda x: x['Y'])['Y'])
    x_max2 = int(max(rect2, key=lambda x: x['X'])['X'])
    y_max2 = int(max(rect2, key=lambda x: x['Y'])['Y'])
    
    dx1 = max(x_min1 - x_min2, 0, x_min2 - x_max1)
    dx2 = max(x_min2 - x_min1, 0, x_min1 - x_max2)
    
    dy1 = max(y_min1 - y_min2, 0, y_min2 - y_max1)
    dy2 = max(y_min2 - y_min1, 0, y_min1 - y_max2)
    
    return (min(dx1, dx2)**2 + min(dy1, dy2)**2)**.5

def get_coords(aoi):
    '''Returns coordinates of AOI'''
    return list(filter(lambda x: aoi.lower() == x['name'].lower(), aois))[0]['coords']

def main():
    '''Groups fixations into percentiles away from a bug'''

    fixations = pd.read_csv('./data/fixations_with_new_task_duration.csv')


    dist_to_bug1 = np.array([-1] * len(fixations))
    dist_to_bug2 = np.array([-1] * len(fixations))

    bugs = {'Task1': ['Task1.Bug'], 'Task3': ['Task3.Bug1', 'Task3.Bug2'], 'Task5': ['Task5.Bug1', 'Task5.Bug2']}

    pars = {par: {f'Task{i}': {0: 0, 25: 0, 50: 0, 75: 0, 100: 0} for i in range(1,7)} for par in fixations['Participant'].unique()}

    for i in tqdm(fixations.index):
        task = fixations.loc[i]['Task']
        if int(task[-1]) % 2 == 0:
            # Even tasks are comprehension tasks and does not have any bugs
            continue
            
        for bug in bugs[task]: # Loop through all bugs in the task

            aoi = fixations.loc[i]['AOI']
            if aoi == 'Task5.Line11_new':
                # Fix AOI name
                aoi = 'Task5.Line11'
            else:
                aoi = '.'.join(aoi.split('.')[2:])

            if 'NoAOI' not in aoi and 'Code' not in aoi and not aoi.endswith('Help'):
                # NoAOI and Code AOI cannot be measured to a bug, help AOI doed not count as percentile away
                 
                bug_coords = get_coords(bug)
                
                # Find the furthest distance
                furthest = min_distance(bug_coords, get_coords(task + '.' + lengths[task.lower()][bug.split('.')[-1].lower()]['furthest']))
                
                # Find the distance to the bug
                dist = min_distance(bug_coords, get_coords(aoi))
                
                # Find percent away and place in a percentile
                per = dist/furthest
                if 0 < per <= .25:
                    per = 25
                elif .25 < per <= .50:
                    per = 50
                elif .50 < per <= .75:
                    per = 75
                elif .75 < per:
                    per = 100
                    
                if '2' in bug:
                    dist_to_bug2[i] = per
                else:
                    dist_to_bug1[i] = per
                
                participant = fixations.loc[i]['Participant']
                pars[participant][task.capitalize()][per] += 1

    groups = {par: {'HelpGroup': -1, 'ExpertiseGroup': -1, 'PerformanceGroup': -1, 'study_score': -1} for par in fixations['Participant'].unique()}
    l = []
    for entry in pars:
        for task in pars[entry]:
            for percentile in pars[entry][task]:
                # First fix HelpGroup and ExpertiseGroup
                if groups[entry]['HelpGroup'] == -1 and entry != 'Expert':
                    groups[entry]['HelpGroup'] = fixations[fixations['Participant'] == entry]['HelpGroup'].iloc[0]

                if groups[entry]['ExpertiseGroup'] == -1 and entry != 'Expert':
                    groups[entry]['ExpertiseGroup'] = fixations[fixations['Participant'] == entry]['ExpertiseGroup'].iloc[0]

                if groups[entry]['PerformanceGroup'] == -1 and entry != 'Expert':
                    groups[entry]['PerformanceGroup'] = fixations[fixations['Participant'] == entry]['PerformanceGroup'].iloc[0]
                
                # Then append row to a list
                l.append({
                    'Task': task,
                    'Participant': entry,
                    'Percentile_all_bugs': percentile,
                    'PerformanceGroup': groups[entry]['PerformanceGroup'],
                    'ExpertiseGroup': groups[entry]['ExpertiseGroup'],
                    'HelpGroup': groups[entry]['HelpGroup'],
                    'count': pars[entry][task][percentile]
                })
                
    # Convert list to dataframe
    all_bugs = pd.DataFrame(l)

    # Save dataframe
    all_bugs.to_csv('./data/percentile_all_bugs.csv', index=False)

if __name__ == '__main__':
    main()
