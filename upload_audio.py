import requests

url = "http://127.0.0.1:8000/process-audio/"
file_path = "C:\Users\DELL\Desktop\udemy AI\practice\pr\Believer.mp3"  # Replace with the path to your audio file

with open(file_path, 'rb') as file:
    files = {'file': file}
    response = requests.post(url, files=files)
    print(response.json())
