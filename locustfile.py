import time

from locust import between
from locust import HttpUser
from locust import task


class WebsiteUser(HttpUser):
    wait_time = between(5, 15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        PDFPath = 'test/in.pdf'
        with open(PDFPath, 'rb') as f:
            self.data_bytes = f.read()

        with open('test/out1.png', 'rb') as f:
            self.expected = f.read()

    @task(1)
    def patient_person(self):

        print(self.client.post("/documents", files={'data.pdf': self.data_bytes}).text)

    @task(10)
    def impatient_person(self):

        with self.client.post("/documents", files={'data.pdf': self.data_bytes}) as r:
            print(r.text)
            ID = r.json()["id"]

        while True:
            time.sleep(1)
            with self.client.get(f"/documents/{ID}") as r:
                if r.json()['status'] == 'done':
                    break

        with self.client.get(f"/documents/{ID}/pages/1") as r:
            result = r.content
            if result != self.expected:
                r.failure("The generated image differs from template.")
            else:
                print("Success.")
