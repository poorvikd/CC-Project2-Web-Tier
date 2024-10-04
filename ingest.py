import pandas as pd
import json

def ingest(file_path):
    df = pd.read_csv(file_path, header=0)
    faces = {}
    for index, row in df.iterrows():
        faces[row['Image']] = row['Results']

    with open('faces.json', 'w+') as f:
        json.dump(faces, f)







ingest('/Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/dataset/Classification Results on Face Dataset (100 images).csv')