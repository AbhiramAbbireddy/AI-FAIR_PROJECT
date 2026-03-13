import pandas as pd

skills_path = "data/raw/skills/Skills.txt"
knowledge_path = "data/raw/skills/Knowledge.txt"

# Read O*NET skills data (tab-separated)
skills_df = pd.read_csv(skills_path, sep="\t", encoding='utf-8', on_bad_lines='skip')
knowledge_df = pd.read_csv(knowledge_path, sep="\t", encoding='utf-8', on_bad_lines='skip')

# Extract unique skill names from Element Name column
# Remove leading/trailing whitespace and convert to lowercase
skills = skills_df["Element Name"].dropna().str.strip().str.lower().unique()
knowledge = knowledge_df["Element Name"].dropna().str.strip().str.lower().unique()

print(f"✓ Raw skills extracted: {len(skills)}")
print(f"✓ Raw knowledge extracted: {len(knowledge)}")

# Combine and deduplicate
all_skills = sorted(set(skills) | set(knowledge))

# Add common technical skills that may not be in O*NET
# This ensures we catch modern tech skills
additional_skills = [
    "python", "java", "javascript", "c++", "c#", "sql", "html", "css",
    "react", "angular", "vue", "node.js", "django", "flask", "tensorflow",
    "pytorch", "machine learning", "deep learning", "artificial intelligence",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "agile", "scrum", "jira", "rest api", "microservices", "devops",
    "data analysis", "statistics", "excel", "tableau", "power bi",
    "project management", "team leadership", "problem solving",
    "communication", "collaboration", "time management"
]

# Add these if not already present
for skill in additional_skills:
    if skill not in all_skills:
        all_skills.append(skill)

all_skills = sorted(all_skills)

vocab_df = pd.DataFrame(all_skills, columns=["skill"])
vocab_df.to_csv("data/processed/skills_vocabulary.csv", index=False)

print(f"\n✅ Total vocabulary size: {len(vocab_df)}")
print(f"✅ Saved to: data/processed/skills_vocabulary.csv")
print(f"\nSample skills:")
for i, skill in enumerate(vocab_df.head(10)["skill"]):
    print(f"  {i+1}. {skill}")