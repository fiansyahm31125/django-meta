from django.http import HttpResponse
import pandas as pd
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from django.http import JsonResponse

def hello_world(request):
    return HttpResponse("Hello, world.")

def forecast(request):
    # Dapatkan path absolut dari direktori file views.py
    # Ini adalah cara yang lebih baik daripada menggunakan path relatif statis
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Gabungkan path dasar dengan nama file
    file_path = os.path.join(base_dir, 'Qris_transaction_juni_2025_interactive.xlsx')
    
    file_path2 = os.path.join(base_dir, 'Qris_transaction_juli_2025_interactive.xlsx')
    
    try:
        # Baca file Excel menggunakan pandas
        df1 = pd.read_excel(file_path)
        df2 = pd.read_excel(file_path2)

        df = pd.concat([df1, df2], ignore_index=True)

        # 2. Ubah 'trxDate' ke format datetime
        df['trxDate'] = pd.to_datetime(df['trxDate'])

        # 3. Buat kolom 'date'
        df['date'] = df['trxDate'].dt.to_period('D')

        # 4. Hitung total penjualan per transaksi
        df['value'] = df['totalTrx'] * df['amountTrx']

        # 5. Kelompokkan dan hitung total
        dfnew = df.groupby(['date'])['value'].sum().reset_index()

        dfnew['date'] = dfnew['date'].dt.to_timestamp()

        # ## Langkah 2: Menentukan dan Fitting Model SARIMA
        # Parameter non-musiman
        p, d, q = 1, 1, 1
        # Parameter musiman
        P, D, Q, s = 1, 0, 1, 7

        model = SARIMAX(dfnew['value'],
                        order=(p, d, q),
                        seasonal_order=(P, D, Q, s),
                        enforce_stationarity=False,
                        enforce_invertibility=False)

        results = model.fit()

        # ## Langkah 3: Forecasting 20 Hari ke Depan
        forecast_steps = 20
        forecast = results.get_forecast(steps=forecast_steps)

        # Dapatkan nilai prediksi
        forecast_values = forecast.predicted_mean

        # # Persiapkan data untuk JSON
        data_to_json = []
        for index, value in forecast_values.items():
            # Format tanggal (index) menjadi string ISO
            periode = index
            # Tambahkan data ke list
            data_to_json.append({
                'periode': periode,
                'qty': value
            })

        # Kembalikan respons dalam format JSON
        return JsonResponse(data_to_json, safe=False)
        
        
    except FileNotFoundError:
        # Tangani kasus jika file tidak ditemukan
        return HttpResponse("Error: File tidak ditemukan!", status=404)
    except Exception as e:
        # Tangani error lainnya
        return HttpResponse(f"Terjadi kesalahan: {e}", status=500)