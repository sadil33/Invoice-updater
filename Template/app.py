import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, send_file, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ==========================================
# 🚨 SECURITY UPDATE: REPLACE THESE KEYS 🚨
# ==========================================
# 1. Get a new key here: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PDF_CO_API_KEY = os.getenv("PDF_CO_API_KEY")
# ==========================================

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

genai.configure(api_key=GEMINI_API_KEY)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- HTML TEMPLATE (Updated with Auto-Stop Loader) ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Invoice AI Updater</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

  <style>
    :root {
      --primary: #6366f1;
      --primary-glow: rgba(99, 102, 241, 0.4);
      --accent: #06b6d4;
      --glass-bg: rgba(15, 23, 42, 0.75);
      --glass-border: rgba(255, 255, 255, 0.1);
      --input-bg: rgba(0, 0, 0, 0.2);
      --bg-base: #0f0c29;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; font-family: 'Outfit', sans-serif;
      display: flex; justify-content: center; align-items: center;
      background-color: var(--bg-base); overflow-y: auto; padding: 2rem 0;
    }
    .bg-texture { position: fixed; top: 0; left: 0; width: 100%; height: 100%; filter: url(#noiseFilter); opacity: 0.15; z-index: -1; pointer-events: none; }
    .ambient-light { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -2; background: radial-gradient(circle at center, transparent 0%, #000 90%); }
    .container {
      position: relative; z-index: 10; width: 450px; padding: 2.5rem; border-radius: 24px;
      background: var(--glass-bg); backdrop-filter: blur(30px); border: 1px solid var(--glass-border);
      box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.6); margin: 50px 0;
    }
    h2 { text-align: center; margin: 0 0 0.5rem 0; font-size: 2rem; color: white; }
    p.subtitle { text-align: center; color: #94a3b8; margin-bottom: 1.5rem; font-size: 0.9rem; }
    .input-group { position: relative; margin-bottom: 1rem; }
    .input-group i { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #64748b; font-size: 1rem; transition: 0.3s; z-index: 2; }
    label { display: block; margin-bottom: 6px; font-size: 0.8rem; color: #cbd5e1; font-weight: 500; margin-left: 4px; }
    input {
      width: 100%; padding: 12px 16px 12px 46px; border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.08); background: var(--input-bg);
      color: white; font-size: 0.9rem; outline: none; transition: 0.3s;
    }
    input:focus { border-color: var(--primary); background: rgba(255, 255, 255, 0.08); }
    input:focus + i { color: var(--primary); }
    .row { display: flex; gap: 10px; }
    .col { flex: 1; }
    .file-drop-area {
      display: flex; align-items: center; justify-content: center; width: 100%; padding: 20px;
      border: 2px dashed rgba(255,255,255,0.15); border-radius: 16px; transition: 0.3s;
      background: rgba(0,0,0,0.1); cursor: pointer; margin-bottom: 1.5rem; position: relative;
    }
    .file-drop-area:hover { border-color: var(--accent); background: rgba(255,255,255,0.03); }
    .fake-btn {
      background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;
      padding: 8px 14px; margin-right: 15px; font-size: 0.8rem; color: white; font-weight: 600;
    }
    .file-msg { font-size: 0.85rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px; }
    .file-input { position: absolute; left: 0; top: 0; height: 100%; width: 100%; opacity: 0; cursor: pointer; }
    .btn-group { display: flex; gap: 10px; margin-top: 20px; }
    button {
      border-radius: 12px; border: none; font-size: 1rem; font-weight: 600; color: white;
      cursor: pointer; transition: 0.3s; padding: 14px; flex: 1;
    }
    .btn-primary {
      background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
      box-shadow: 0 10px 25px -5px var(--primary-glow);
    }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 20px 35px -10px var(--primary-glow); }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
      color: #cbd5e1;
    }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); color: white; }
    .loader { display: none; width: 22px; height: 22px; border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: white; animation: spin 0.8s ease-in-out infinite; margin: 0 auto; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .footer { margin-top: 2rem; text-align: center; color: rgba(255,255,255,0.4); font-size: 0.75rem; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Update Invoice</h2>
    <p class="subtitle">Fill only the fields you want to change</p>

    <form id="invoiceForm" enctype="multipart/form-data">
      
      <div class="file-drop-area" id="dropArea">
        <span class="fake-btn" id="fakeBtn"><i class="fas fa-cloud-upload-alt"></i> Upload</span>
        <span class="file-msg" id="fileMsg">Drag & drop PDF</span>
        <input class="file-input" type="file" name="file" accept=".pdf" required onchange="updateFileName(this)">
      </div>

      <div class="row">
        <div class="col input-group">
          <label>Invoice No.</label>
          <input type="text" name="invoice" placeholder="INV-001">
          <i class="fas fa-hashtag"></i>
        </div>
        <div class="col input-group">
          <label>PO No.</label>
          <input type="text" name="po" placeholder="PO-123">
          <i class="fas fa-receipt"></i>
        </div>
      </div>

      <div class="input-group">
        <label>Invoice Date</label>
        <input type="text" name="date" placeholder="e.g. 12 Jan 2025">
        <i class="fas fa-calendar-alt"></i>
      </div>

      <div class="row">
        <div class="col input-group">
          <label>Sub Total</label>
          <input type="text" name="subtotal" placeholder="4,000.00">
          <i class="fas fa-money-bill"></i>
        </div>
        <div class="col input-group">
          <label>VAT / Tax</label>
          <input type="text" name="vat" placeholder="10%">
          <i class="fas fa-percent"></i>
        </div>
      </div>

      <div class="input-group">
        <label>Total Amount</label>
        <input type="text" name="total" placeholder="e.g. 5,000.00">
        <i class="fas fa-coins"></i>
      </div>

      <div class="btn-group">
        <button type="button" class="btn-secondary" onclick="resetForm()">
          <i class="fas fa-redo"></i> Start Over
        </button>
        
        <button type="submit" class="btn-primary" id="processBtn">
          <span class="btn-text">Process <i class="fas fa-arrow-right"></i></span>
          <div class="loader"></div>
        </button>
      </div>

    </form>
    <div class="footer">Secure AI Processing <i class="fas fa-shield-alt"></i> PDF.co & Gemini</div>
  </div>

  <script>
    function updateFileName(input) {
      const fileMsg = document.getElementById('fileMsg');
      const fakeBtn = document.getElementById('fakeBtn');
      const dropArea = document.getElementById('dropArea');
      
      if (input.files && input.files[0]) {
        fileMsg.textContent = input.files[0].name;
        fileMsg.style.color = '#fff';
        fakeBtn.innerHTML = '<i class="fas fa-check"></i> Ready';
        fakeBtn.style.background = 'var(--accent)';
        dropArea.style.borderColor = 'var(--accent)';
      }
    }

    // New Event Listener to Handle Form Submission via AJAX/Fetch
    document.getElementById('invoiceForm').addEventListener('submit', async function(e) {
        e.preventDefault(); // Stop standard page reload

        const btnText = document.querySelector('.btn-text');
        const loader = document.querySelector('.loader');
        const submitBtn = document.getElementById('processBtn');

        // 1. Show Loader
        btnText.style.display = 'none';
        loader.style.display = 'block';
        submitBtn.disabled = true; // Prevent double clicking

        try {
            const formData = new FormData(this);
            
            // 2. Send Data to Server
            const response = await fetch('/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                // If server returns error (500/400), try to read it
                const errText = await response.text();
                throw new Error(errText || "Processing failed");
            }

            // 3. Get Filename from Headers (Optional, defaults to updated_invoice.pdf)
            let filename = "updated_invoice.pdf";
            const disposition = response.headers.get('Content-Disposition');
            if (disposition && disposition.includes('filename=')) {
                filename = disposition.split('filename=')[1].replace(/['"]/g, '');
            }

            // 4. Download the Blob
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            alert("⚠️ " + error.message);
        } finally {
            // 5. STOP LOADER (Always runs, success or fail)
            btnText.style.display = 'inline';
            loader.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    function resetForm() {
        document.getElementById('invoiceForm').reset();
        const fileMsg = document.getElementById('fileMsg');
        const fakeBtn = document.getElementById('fakeBtn');
        const dropArea = document.getElementById('dropArea');
        
        fileMsg.textContent = "Drag & drop PDF";
        fileMsg.style.color = '#94a3b8';
        fakeBtn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Upload';
        fakeBtn.style.background = '';
        dropArea.style.borderColor = '';
    }
  </script>

</body>
</html>"""

# --- BACKEND LOGIC ---

def get_current_values(file_path):
    """
    Uses Gemini to extract OLD values. Updated Prompt for VAT/Table data.
    """
    try:
        pdf_file = genai.upload_file(path=file_path, mime_type="application/pdf")
        
        # Using Gemini 2.5 Flash
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        prompt = """
        Analyze this invoice image strictly. I need the EXACT text strings to perform a Find & Replace.

        CRITICAL INSTRUCTION FOR VAT:
        1. Locate the main data table.
        2. Find the column header labeled "VAT %" or "VAT".
        3. Look at the value in the first row under this header. 
        4. It is likely just a number (e.g., "20"). 
        5. Return ONLY that number. DO NOT add a "%" symbol.
        6. Example: If the cell contains "20", your JSON must contain "20", not "20%".

        Extract the following exact strings:
        1. Invoice Number
        2. PO Number
        3. Invoice Date
        4. Sub Total Amount
        5. VAT Value (The text found in the table column, e.g. "20")
        6. Total Amount
        
        Return raw JSON only:
        {
          "old_invoice": "val", 
          "old_po": "val", 
          "old_date": "val",
          "old_subtotal": "val", 
          "old_vat": "val", 
          "old_total": "val"
        }
        """
        response = model.generate_content([pdf_file, prompt])
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        print(f"DEBUG GEMINI FOUND: {clean_json}")
        return json.loads(clean_json)
    except Exception as e:
        print(f"Gemini Extraction Error: {e}")
        return {}

def update_pdf(file_path, current_data, new_data):
    """
    Uses PDF.co to Find & Replace text.
    """
    
    # Map old values (from Gemini) to new values (from User Form)
    replacements = [
        (current_data.get('old_invoice'), new_data['invoice']),
        (current_data.get('old_po'), new_data['po']),
        (current_data.get('old_date'), new_data['date']),
        (current_data.get('old_subtotal'), new_data['subtotal']),
        (current_data.get('old_vat'), new_data['vat']),
        (current_data.get('old_total'), new_data['total'])
    ]

    headers = {"x-api-key": PDF_CO_API_KEY}
    
    # 1. Get Presigned URL for Upload
    res = requests.get("https://api.pdf.co/v1/file/upload/get-presigned-url", headers=headers)
    if res.status_code != 200:
        raise Exception(f"PDF.co Upload Error: {res.text}")
        
    data = res.json()
    upload_url = data["presignedUrl"]
    working_url = data["url"]

    # 2. Upload the PDF
    with open(file_path, "rb") as f:
        requests.put(upload_url, data=f)

    # 3. Perform Replacements
    replace_api = "https://api.pdf.co/v1/pdf/edit/replace-text"
    
    for old_val, new_val in replacements:
        if not old_val or not new_val or str(new_val).strip() == "":
            continue
        
        payload = {
            "url": working_url,
            "searchString": old_val, 
            "replaceString": new_val 
        }
        
        res = requests.post(replace_api, json=payload, headers=headers)
        
        if res.status_code == 200:
            working_url = res.json()["url"]
        else:
            print(f"Replacement failed for {old_val}: {res.text}")

    # 4. Download Final PDF
    final_res = requests.get(working_url)
    safe_output_path = os.path.join(UPLOAD_FOLDER, "temp_processed_file.pdf")
    
    with open(safe_output_path, "wb") as f:
        f.write(final_res.content)
    
    original_name = os.path.basename(file_path)
    name_part, ext_part = os.path.splitext(original_name)
    user_download_name = f"{name_part}_updated{ext_part}"
        
    return safe_output_path, user_download_name

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded", 400
        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400

        input_filename = "temp_input.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(file_path)

        new_data = {
            "invoice": request.form.get('invoice'),
            "po": request.form.get('po'),
            "date": request.form.get('date'),
            "subtotal": request.form.get('subtotal'),
            "vat": request.form.get('vat'),
            "total": request.form.get('total')
        }

        try:
            current_vals = get_current_values(file_path)
            output_path, download_name = update_pdf(file_path, current_vals, new_data)
            return send_file(output_path, as_attachment=True, download_name=download_name)
        except Exception as e:
            return f"Processing Error: {str(e)}", 500

    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)