from transformers import pipeline

model_name = "jjzha/jobbert_skill_extraction"

ner = pipeline(
    "token-classification",
    model=model_name,
    aggregation_strategy="simple"
)

text = """
Software engineer with 5 years of experience in Python development,
machine learning, deep learning, TensorFlow, PyTorch, and data analysis.
Experienced in building REST APIs using Flask and deploying applications
with Docker and AWS cloud services.
"""

results = ner(text)

print("\nExtracted Entities:\n")

for r in results:
    print(r)