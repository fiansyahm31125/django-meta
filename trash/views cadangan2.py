from django.http import HttpResponse
import pandas as pd
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

def hello_world(request):
    return HttpResponse("Hello, world.")

@csrf_exempt
def forecast(request):
    # Hanya izinkan metode POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Metode yang diperbolehkan adalah POST'}, status=405)

    try:
        # 1. Ambil data JSON dari body request
        data = json.loads(request.body)
        
        # 2. Buat DataFrame dari data JSON
        # Pastikan data yang diterima adalah list
        if not isinstance(data, list):
            return JsonResponse({'error': 'Format JSON harus berupa list dari objek'}, status=400)
            
        df = pd.DataFrame(data)

        # 3. Validasi kolom yang dibutuhkan
        if 'periode' not in df.columns or 'qty' not in df.columns:
            return JsonResponse({'error': 'JSON harus mengandung kolom "periode" dan "qty"'}, status=400)

        # 4. Ubah kolom 'periode' ke format datetime dan set sebagai index
        df['periode'] = pd.to_datetime(df['periode'])
        df.set_index('periode', inplace=True)
        
        # Urutkan berdasarkan tanggal
        df.sort_index(inplace=True)

        # 5. Menentukan dan Fitting Model SARIMA
        # Parameter non-musiman
        p, d, q = 1, 1, 1
        # Parameter musiman
        P, D, Q, s = 1, 0, 1, 7 # Asumsi: pola musiman mingguan (s=7)

        model = SARIMAX(df['qty'],
                        order=(p, d, q),
                        seasonal_order=(P, D, Q, s),
                        enforce_stationarity=False,
                        enforce_invertibility=False)

        results = model.fit(disp=False) # disp=False untuk menonaktifkan output fitting

        # 6. Forecasting 20 Hari ke Depan
        forecast_steps = 20
        forecast_results = results.get_forecast(steps=forecast_steps)

        # 7. Dapatkan nilai prediksi
        forecast_values = forecast_results.predicted_mean

        # 8. Persiapkan data untuk respons JSON
        data_to_json = []
        for index, value in forecast_values.items():
            # Format tanggal (index) menjadi string ISO
            periode = index.strftime('%Y-%m-%d')
            # Tambahkan data ke list
            data_to_json.append({
                'periode': periode,
                'qty': value
            })

        # 9. Kembalikan respons dalam format JSON
        return JsonResponse(data_to_json, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Terjadi kesalahan: {e}'}, status=500)