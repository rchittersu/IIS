import os
import json
import os.path as osp
import shutil
import numpy as np
import sys

# usage: python eval/get_means.py <scores_dir>
path = sys.argv[1]

scores = {}
for file in os.listdir(path):
    if not file.endswith('.jsonl'):
        continue
    file_path = osp.join(path,file)
    file_name = file.split('.jsonl')[0]

    tmp = {}
    scores[file_name] = {}
    with open(file_path, 'r') as json_file:
        json_list = list(json_file)

        for json_str in json_list:
            # print(json_str)
            dict_file = json.loads(json_str)
            for x in dict_file.keys():
                if x not in tmp.keys():
                    tmp[x] = []
                else:
                    tmp[x].append(dict_file[x])
                    
    for item in tmp.keys():
        scores[file_name][item] = np.mean(tmp[item])


with open(osp.join(path, "means.json"), "w") as op:
    json.dump(scores, op, indent=4)