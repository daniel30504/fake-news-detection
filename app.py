from flask import Flask, request, render_template
import requests
import markdown

app = Flask(__name__)

# Konfigurasi Gemini Flash API
GEMINI_API_KEY = "AIzaSyAdaeUma2RiwQptfPiYyaYbwHyNYUqRKQ4"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deteksi', methods=['POST'])
def deteksi():
    teks = request.form['berita'].strip()

    prompt = f"""
Asumsikan kamu adalah AI dengan pengetahuan terkini dan kemampuan pencarian web.
Tugasmu adalah mengklasifikasikan klaim berikut ini dan menjelaskan alasannya secara jelas dan padat.

Klaim: "{teks}"

Kategori klasifikasi:
- FAKTA: Klaim benar dan dapat diverifikasi.
- HOAKS: Klaim salah dan bertentangan dengan fakta.
- MENYESATKAN: Klaim mengandung sebagian kebenaran namun dapat disalahartikan.

❗ Jawaban, penjelasan, dan sumber harus SEBAIKNYA menggunakan *bahasa Indonesia*.
❗ Jika memungkinkan, prioritaskan referensi dari situs atau artikel berbahasa Indonesia.

Tampilkan jawaban dalam format markdown berikut (WAJIB ikuti dan isi semuanya):

Kesimpulan: FAKTA / HOAKS / MENYESATKAN

Penjelasan: Penjelasan WAJIB selalu ada, meskipun singkat. Sertakan alasan klasifikasi.

Sumber: (Jika ada, tampilkan sebagai tautan markdown: [Judul](https://...).
Jika tidak ada, tulis: Tidak ada sumber spesifik dari pencarian web.)
"""

    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        parts = result.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        if not parts:
            return "Respon dari Gemini kosong.", 500

        full_output = parts[0].get('text', '')

        kesimpulan = "TIDAK DITENTUKAN"
        penjelasan_lines = []
        sumber_lines = []
        current_section = None

        for line in full_output.splitlines():
            stripped = line.strip().lower()
            if stripped.startswith("kesimpulan:"):
                kesimpulan = line.split(":", 1)[1].strip().upper()
                current_section = None
            elif stripped.startswith("penjelasan:"):
                current_section = "penjelasan"
                inline = line.split(":", 1)[1].strip()
                if inline:
                    penjelasan_lines.append(inline)
            elif stripped.startswith("sumber:"):
                current_section = "sumber"
                inline = line.split(":", 1)[1].strip()
                if inline:
                    sumber_lines.append(inline)
            elif current_section == "penjelasan":
                penjelasan_lines.append(line.strip())
            elif current_section == "sumber":
                sumber_lines.append(line.strip())

        penjelasan_md = "\n".join(penjelasan_lines).strip()
        if not penjelasan_md or len(penjelasan_md) < 10:
            penjelasan_md = "Model tidak memberikan penjelasan spesifik untuk klaim ini."

        sumber_md = "\n".join(sumber_lines).strip()
        if not sumber_md:
            sumber_md = "Tidak ada sumber spesifik dari pencarian web."

        penjelasan_html = markdown.markdown(penjelasan_md)
        sumber_html = markdown.markdown(sumber_md)

        klaim = teks if len(teks) <= 120 else teks[:120] + "..."

        return render_template("index.html",
            hasil=True,
            klaim=klaim,
            kesimpulan=kesimpulan,
            penjelasan_html=penjelasan_html,
            sumber_html=sumber_html
        )

    except requests.exceptions.RequestException as e:
        return f"Terjadi kesalahan koneksi ke Gemini API: {e}", 500
    except Exception as e:
        return f"Terjadi kesalahan: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
