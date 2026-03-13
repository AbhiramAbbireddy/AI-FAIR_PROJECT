import os
import pdfplumber
import pandas as pd
from tqdm import tqdm

BASE_DIR = "data/raw/resumes/Resume"
records = []

for category in os.listdir(BASE_DIR):

    category_path = os.path.join(BASE_DIR, category)

    if not os.path.isdir(category_path):
        continue

    for file in tqdm(os.listdir(category_path), desc=category):

        if file.endswith(".pdf"):

            file_path = os.path.join(category_path, file)

            text = ""

            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + " "

            except Exception as e:
                print("Error reading:", file_path)

            records.append({
                "file_name": file,
                "category": category,
                "resume_text": text
            })

df = pd.DataFrame(records)

os.makedirs("data/processed", exist_ok=True)

df.to_csv("data/processed/resumes_text.csv", index=False)

print("Total resumes processed:", len(df))