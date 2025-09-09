from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Set API key dari environment variable
# Ganti 'YOUR_API_KEY' dengan kunci API Gemini Anda
os.environ["GOOGLE_API_KEY"] = "AIzaSyCTr-BWtHHrym0DquNZvWlgoowx21wqAdc"

# Inisialisasi model LLM dari Google Generative AI (Gemini)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

# Buat template prompt
prompt_template = "Tuliskan nama produk yang menarik dan slogan untuk perusahaan yang membuat {jenis_produk}."
prompt = PromptTemplate.from_template(prompt_template)

# Gunakan operator pipe (|) untuk membuat 'chain'
# Ini adalah cara modern yang disarankan
chain = prompt | llm

# Jalankan 'chain' dengan input yang diinginkan
# Anda harus menggunakan metode .invoke()
hasil_jawaban = chain.invoke({"jenis_produk": "kopi"})

# Cetak hasil jawaban
print(hasil_jawaban)