from django.shortcuts import render
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse

def getQRISInteractive(year,month,day):
    # Tentukan tanggal yang Anda inginkan
    thedate = datetime(year,month,day)
    
    # Format tanggal menjadi string 'YYYYMMDD'
    # Perhatikan format '%d' untuk hari
    strtime = thedate.strftime('%Y%m%d')
    
    # URL file yang akan diunduh dengan tanggal yang diformat
    url = f"https://my.finpay.id/storage/interactive/QRIS_Interactive_{strtime}.xlsx"
    
    # Mengunduh konten file dari URL
    try:
        response = requests.get(url)
        # Memunculkan error untuk status kode yang buruk (misalnya 404 Not Found)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengunduh file: {e}")
        # Hentikan eksekusi jika gagal
        exit()
    
    # Membaca konten yang diunduh dari memori
    excel_file = BytesIO(response.content)
    
    # Konversi langsung ke Pandas DataFrame
    df = pd.read_excel(excel_file)
    return df

# Create your views here.
def index(request):
    df_data = None
    if request.method == 'POST':
        startdate_str = request.POST.get("startdate")
        enddate_str = request.POST.get("enddate")
        startdate_obj=datetime.strptime(startdate_str,'%Y-%m-%d')
        enddate_obj=datetime.strptime(enddate_str,'%Y-%m-%d')
        
        start_year = startdate_obj.year
        start_month = startdate_obj.month
        start_day = startdate_obj.day

        end_year = enddate_obj.year
        end_month = enddate_obj.month
        end_day = enddate_obj.day

        if(start_month!=end_month or start_day>end_day):
            return HttpResponse({'error': 'Invalid DATE'})
        
        df_matrix = []
        for i in range(start_day, end_day+1):
            tmpdf = getQRISInteractive(start_year, start_month, i )
            tmpdf['tanggal_excel'] = i
            df_matrix.append(tmpdf)
        dfjuli = pd.concat(df_matrix)
        
        # Mengubah DataFrame menjadi list dari dictionary untuk iterasi di template
        df_data = dfjuli.to_dict('records')
        
    context = {
        'df_data': df_data,
    }
    return render(request, 'finnet.html', context)