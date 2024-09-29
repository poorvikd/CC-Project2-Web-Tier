import requests
import os

IMAGE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'face_images_1000')

def test():
    file = {'inputFile': open(f'{IMAGE_FILE_PATH}/test_000.jpg', 'rb')}
    response = requests.post('http://localhost:8000', files=file)
    if response.status_code == 200:
        print(response.json())
    else:
        print("Error")

if __name__ == '__main__':
    test()