import os
from dotenv import load_dotenv

# Try to load the .env file
loaded = load_dotenv()

print(f"Did Python find a .env file? {loaded}")

pdf_key = os.getenv("PDF_CO_API_KEY")

if pdf_key:
    print(f"SUCCESS: Key found! It starts with: {pdf_key[:5]}...")
else:
    print("FAILURE: Python sees the key as Empty/None.")
    print("-------------------------------------------------")
    print("POSSIBLE CAUSES:")
    print("1. Your file is named '.env.txt' (rename it to just '.env')")
    print("2. You didn't save the .env file in this exact folder.")
    print("3. You formatted the line wrong (e.g. used spaces around '=').")