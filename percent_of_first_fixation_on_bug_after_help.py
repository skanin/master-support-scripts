import pandas as pd


def main():
    '''Creates a dataframe with percentage of first fixation that was on a bug after consulting help section'''

    # Read and group dataframe
    df = pd.read_csv('./data/to_from_fixations_new_with_int_coords.csv')
    df = df.groupby(['Participant', 'To']).size().reset_index(name='count')

    # Read participants
    participants = pd.read_csv('./data/usernames.csv', delimiter='\t')
    participants = participants[participants['helpType'] == 2]['username']

    l = []
    totals = {p: {'participant': p, 'percent': 0, 'bug': 'total', 'all_count': 0, 'bug_count': 0} for p in participants.values}
    for task in range(1, 7, 2): # Loop through task
        for participant in participants.values: # For each task, loop through participants
            
            try:
                s = df[(df['Participant'] == participant) & (df['To'].str.contains(f'Task{task}'))]['count'].sum() # Find total number of fixations after consulting help section
            except IndexError:
                s = 0.0
                
            if task == 1:
                try:
                    num = df[(df['Participant'] == participant) & (df['To'].str.contains(f'Task{task}.Bug'))]['count'].iloc[0] # Find number of fixations on bug after consulting help section
                except IndexError:
                    num = 0.0
                
                if s == 0.0:
                    percent = 0
                else:
                    percent =  (num / s) * 100 # Calculate percentage of first fixation that was on a bug after consulting help section
                
                totals[participant]['all_count'] += s
                totals[participant]['bug_count'] += num
                
                l.append({'participant': participant, 'percent': percent, 'bug': 'Task1.Bug', 'all_count': s, 'bug_count': num})
            else:
                # Tasks 3 and 5 have two bugs
                for i in range(1,3):
                    try:
                        num = df[(df['Participant'] == participant) & (df['To'].str.contains(f'Task{task}.Bug{i}'))]['count'].iloc[0]
                    except IndexError:
                        num = 0.0
                    
                    if s == 0.0:
                        percent = 0
                    else:
                        percent =  (num / s) * 100
                        
                    totals[participant]['all_count'] += s
                    totals[participant]['bug_count'] += num
    
                    l.append({'participant': participant, 'percent': percent, 'bug': f'Task{task}.Bug{i}', 'all_count': s, 'bug_count': num})
    for p in totals: # Calculate total percentages
        totals[p]['percent'] = (totals[p]['bug_count'] / totals[p]['all_count']) * 100

    l.extend(list(totals.values()))

    # Create dataframe from list 
    percents = pd.DataFrame(l)

    # Save dataframe
    percents.to_csv('./data/percent_of_first_fixation_on_bug_after_help.csv', index=False)

if __name__ == '__main__':
    main()
