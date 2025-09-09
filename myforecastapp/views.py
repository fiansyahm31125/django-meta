from django.shortcuts import render
import pandas as pd
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
import math

# Create your views here.
@csrf_exempt
def forecast(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metode yang diperbolehkan adalah POST'}, status=405)

    try:
        data = json.loads(request.body)
        
        if not isinstance(data, list):
            return JsonResponse({'error': 'Format JSON harus berupa list dari objek'}, status=400)
            
        df = pd.DataFrame(data)

        if 'periode' not in df.columns or 'qty' not in df.columns:
            return JsonResponse({'error': 'JSON harus mengandung kolom "periode" dan "qty"'}, status=400)

        # ✅ Validasi minimal 12 data
        if len(df) < 12:
            return JsonResponse({'error': f'Data minimal 12 periode, data yang dikirim hanya {len(df)}'}, status=400)

        # 4. Ubah kolom 'periode' ke format datetime dan set sebagai index
        df['periode'] = pd.to_datetime(df['periode'], format='%Y%m')
        df.set_index('periode', inplace=True)
        
        # Urutkan berdasarkan tanggal
        df.sort_index(inplace=True)

        # 5. Menentukan dan Fitting Model SARIMA
        p, d, q = 1, 1, 1
        P, D, Q, s = 1, 0, 1, 12  # s = 6 untuk musiman 6 bulan

        model = SARIMAX(df['qty'],
                        order=(p, d, q),
                        seasonal_order=(P, D, Q, s),
                        enforce_stationarity=False,
                        enforce_invertibility=False)
        results = model.fit(disp=False)

        # 6. Forecasting 5 Bulan ke Depan
        forecast_steps = 5
        forecast_results = results.get_forecast(steps=forecast_steps)

        # 7. Dapatkan nilai prediksi
        forecast_values = forecast_results.predicted_mean

        # 8. Persiapkan data untuk respons JSON
        data_to_json = []
        for index, value in forecast_values.items():
            periode = index.strftime('%Y%m')
            data_to_json.append({
                'periode': periode,
                'qty': math.ceil(value)  # ubah ke float agar serializable
            })

        # 9. Kembalikan respons dalam format JSON
        return JsonResponse(data_to_json, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Terjadi kesalahan: {e}'}, status=500)
    
