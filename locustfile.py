import time

from locust import between
from locust import HttpUser
from locust import task


class WebsiteUser(HttpUser):
    wait_time = between(5, 15)

    @task(1)
    def patient_person(self):

        PDFPath = 'test/in.pdf'
        data = open(PDFPath, 'rb')
        data_bytes = data.read()
        data.close()

        print(self.client.post("/documents", files={'data.pdf': data_bytes}).text)

    @task(10)
    def impatient_person(self):

        PDFPath = 'test/in.pdf'
        with open(PDFPath, 'rb') as f:
            data_bytes = f.read()

        with self.client.post("/documents", files={'data.pdf': data_bytes}) as r:
            print(r.text)
            ID = r.json()["id"]

        while True:
            time.sleep(1)
            with self.client.get(f"/documents/{ID}") as r:
                if r.json()['status'] == 'done':
                    break

        with open('test/out1.png', 'rb') as f:
            expected = f.read()

        with self.client.get(f"/documents/{ID}/pages/1") as r:
            result = r.content
            if result != expected:
                r.failure("The generated image differs from template.")
