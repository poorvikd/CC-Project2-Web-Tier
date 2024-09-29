import pandas as pd
import requests
url = 'http://localhost:8000'

def ingest(file_path):
    df = pd.read_csv(file_path, header=0)

    for index, row in df.iterrows():
        face = {'id':index, 'name':row['Results'], 'image_name':row['Image']}
        response = requests.post(f'{url}/add_face', json=face)
        if response.status_code == 200:
            print(f'{index} added')
        else:
            print("Error")





ingest('/Users/poorvikd/Documents/CloudComp/Project2-Web-Tier/Classification Results on Face Dataset (1000 images).csv')