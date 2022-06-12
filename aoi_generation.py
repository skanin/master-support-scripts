import json
import os
from copy import deepcopy

aois = []
with open('./data/aois/all.aois', 'r') as f:
    aois = json.load(f)


line_aois = {'Aois': list(
    filter(lambda x: 'line' in x['Name'].lower() or 'bug' in x['Name'].lower(), aois['Aois']))}

aoi_files = os.listdir('./data/aois/participant_aois')

for filename in aoi_files:
    username = filename.split('.')[0]

    participant_aois = json.load(
        open(f'./data/aois/participant_aois/{filename}'))

    task_names = list(map(lambda x: x['Name'], participant_aois['Aois']))
    line_names = list(map(lambda x: x['Name'], line_aois['Aois']))

    aois = []

    for line in line_names:
        parts = line.split('.')
        task = parts[0]

        line_aois_copy = deepcopy(line_aois['Aois'])

        line_aoi = list(
            filter(lambda x: line == x['Name'], line_aois_copy)).copy()
        line_keyframes = line_aoi[0]['KeyFrames']
        line_keyframe = line_keyframes[0].copy()

        task_keyframes = list(filter(lambda x: f'{task}.Code' in x['Name'], participant_aois['Aois']))[
            0]['KeyFrames'].copy()

        for i in range(1, 3):
            seconds = task_keyframes[i]['Seconds']
            line_keyframe['Seconds'] = seconds
            line_keyframe['IsActive'] = i == 1

        aois.append(line_aoi)

        if line in map(lambda x: x['Name'], participant_aois['Aois']):
            for aoi in participant_aois['Aois']:
                if aoi['Name'] == line:
                    aoi['KeyFrames'].clear()
                    aoi['KeyFrames'] = line_aoi[0]['KeyFrames']
        else:
            participant_aois['Aois'].append(line_aoi[0])

    with open(f'./data/aois/new_aois/{username}.aois', 'w') as f:
        json.dump(participant_aois, f)
