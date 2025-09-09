from django.test import TestCase, Client
from django.urls import reverse
import json

class HelloWorldViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        try:
            print(response.json())  # kalau JSON
        except ValueError:
            print("Response bukan JSON. Konten:", response.content.decode())


class LangchainTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('langchain')
    def test_langchain_prompt(self):
        response=self.client.get(self.url)
        print(response.json())



# class ForecastViewTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.url = reverse('forecast')

#     def test_forecast_invalid_method(self):
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 405)
#         self.assertIn('Metode yang diperbolehkan', response.json()['error'])

#     def test_forecast_invalid_json(self):
#         response = self.client.post(self.url, data="invalid json", content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertIn('Invalid JSON format', response.json()['error'])

#     def test_forecast_not_list(self):
#         payload = {"periode": "202401", "qty": 100}
#         response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertIn('Format JSON harus berupa list', response.json()['error'])

#     def test_forecast_missing_columns(self):
#         payload = [{"wrong": "202401", "qty": 100}]
#         response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertIn('JSON harus mengandung kolom', response.json()['error'])

#     def test_forecast_insufficient_data(self):
#         # Kirim kurang dari 12 data
#         payload = [{"periode": f"20240{i+1}", "qty": 100} for i in range(5)]
#         response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
#         self.assertEqual(response.status_code, 400)
#         self.assertIn('Data minimal 12 periode', response.json()['error'])

#     def test_forecast_success(self):
#         # Kirim 12 data agar memenuhi syarat
#         payload = [{"periode": f"2023{str(i+1).zfill(2)}", "qty": 100 + i} for i in range(12)]
#         response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
#         self.assertEqual(response.status_code, 200)
#         self.assertIsInstance(response.json(), list)
#         self.assertEqual(len(response.json()), 5)  # Karena forecast 5 langkah ke depan
#         self.assertIn('periode', response.json()[0])
#         self.assertIn('qty', response.json()[0])
