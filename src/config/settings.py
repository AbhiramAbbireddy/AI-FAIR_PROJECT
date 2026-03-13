"""
Central configuration for FAIR-PATH AI Career Intelligence Platform.
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Load .env file (if present) so API keys persist across sessions ────
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _key, _, _val = _line.partition("=")
            _key, _val = _key.strip(), _val.strip()
            if _val and _key not in os.environ:
                os.environ[_key] = _val

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

SKILLS_VOCAB_PATH = PROCESSED_DIR / "skills_vocabulary.csv"
RESUME_SKILLS_PATH = PROCESSED_DIR / "resume_skills.csv"
JOBS_PARSED_PATH = PROCESSED_DIR / "jobs_parsed.csv"
SKILL_TRENDS_PATH = PROCESSED_DIR / "skill_trends.csv"
JOBS_DB_PATH = PROCESSED_DIR / "jobs_collected.csv"

# ── Model settings ─────────────────────────────────────────────────────
ROBERTA_MODEL = "jjzha/jobbert_skill_extraction"
SBERT_MODEL = "all-MiniLM-L6-v2"
NER_CONFIDENCE = 0.65
NER_CHUNK_SIZE = 500
DEVICE = -1  # -1 = CPU, 0 = GPU

# ── Matching weights ───────────────────────────────────────────────────
SEMANTIC_WEIGHT = 0.50
SKILL_OVERLAP_WEIGHT = 0.30
EXPERIENCE_WEIGHT = 0.20
REQUIRED_SKILL_W = 0.70
PREFERRED_SKILL_W = 0.30

# ── Job API configuration ─────────────────────────────────────────────
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")
JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com"
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
REMOTIVE_BASE_URL = "https://remotive.com/api/remote-jobs"
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# ── Fairness settings ─────────────────────────────────────────────────
FAIRNESS_BIAS_CATEGORIES = {
    "Gender Bias": {
        "indicators": [
            "male", "female", "gender", "mr.", "mrs.", "ms.",
            "he/him", "she/her", "man", "woman",
        ],
        "penalty": 10,
    },
    "Age Bias": {
        "indicators": [
            "age", "years old", "born in", "date of birth", "dob",
            "young", "senior citizen",
        ],
        "penalty": 10,
    },
    "Ethnicity / Nationality Bias": {
        "indicators": [
            "nationality", "race", "ethnicity", "religion", "caste",
            "country of origin",
        ],
        "penalty": 10,
    },
    "Marital / Family Bias": {
        "indicators": [
            "marital status", "married", "single", "divorced",
            "children", "family", "spouse",
        ],
        "penalty": 8,
    },
    "Photo / Appearance Bias": {
        "indicators": ["photo", "picture", "image", "headshot", "portrait"],
        "penalty": 8,
    },
    "Education Prestige Bias": {
        "indicators": ["ivy league", "top university", "tier 1", "tier-1"],
        "penalty": 5,
    },
}

# ── Skill category taxonomy (for UI grouping) ─────────────────────────
SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "javascript", "c++", "c#", "c", "go", "rust",
        "typescript", "ruby", "php", "swift", "kotlin", "scala", "r",
        "sql", "html", "css", "perl", "matlab", "shell", "shell scripting",
        "powershell", "dart", "lua", "elixir", "haskell", "solidity",
        "vhdl", "verilog", "systemverilog", "assembly language", "assembly",
        "embedded c", "latex",
    ],
    "ML / AI": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "tensorflow", "pytorch", "keras",
        "neural networks", "reinforcement learning", "computer vision",
        "generative ai", "llm", "langchain", "llamaindex", "transformers",
        "hugging face", "prompt engineering", "fine-tuning",
        "stable diffusion", "multimodal ai", "blip", "openai", "groq",
        "ollama", "vllm", "rag", "retrieval-augmented generation",
        "scikit-learn", "xgboost", "lightgbm", "catboost",
        "opencv", "yolo", "object detection", "image classification",
        "text classification", "named entity recognition", "sentiment analysis",
        "recommendation systems", "time series", "feature engineering",
        "model deployment", "onnx", "tensorrt", "triton", "mlops",
        "cnn", "rnn", "lstm", "gan", "autoencoder", "attention mechanism",
        "bert", "gpt", "llama", "image processing", "digital image processing",
    ],
    "Electrical / Electronics": [
        "analog circuits", "digital circuits", "digital electronics",
        "signal processing", "digital signal processing", "dsp",
        "power electronics", "power systems", "electric machines",
        "electromagnetic", "em waves", "antenna design", "rf engineering",
        "communication systems", "wireless communication",
        "network theory", "circuit analysis", "circuit design",
        "information theory", "coding theory",
        "pwm", "pid", "pid controller", "control systems",
        "motor control", "dc motor", "stepper motor", "servo motor",
        "fourier transform", "fft", "wavelet transform", "z transform",
        "laplace transform", "radar", "sar", "synthetic aperture radar", "lidar",
        "semiconductor physics", "solid state physics",
        "optics", "photonics", "spectroscopy",
        "telecommunications", "5g", "lte", "fiber optics",
    ],
    "Embedded / Hardware": [
        "embedded systems", "fpga", "vlsi", "asic", "rtos", "firmware",
        "microcontroller", "microprocessor", "arduino", "raspberry pi",
        "stm32", "8051", "arm", "avr", "pic microcontroller",
        "cpld", "soc", "system on chip", "tiva", "msp430",
        "esp32", "esp8266", "nrf52",
        "pcb design", "pcb layout", "eagle", "kicad", "altium",
        "i2c", "spi", "uart", "can bus", "usb", "pcie",
        "soldering", "prototyping", "breadboard",
        "oscilloscope", "multimeter", "logic analyzer",
        "data acquisition", "instrumentation", "sensors",
        "signal conditioning", "adc", "dac",
    ],
    "IoT / Robotics": [
        "iot", "internet of things", "mqtt", "lora",
        "bluetooth", "wifi", "zigbee",
        "robotics", "ros", "robot operating system",
        "plc", "scada", "industrial automation",
    ],
    "EDA / Simulation Tools": [
        "spice", "ngspice", "ltspice", "pspice", "hspice",
        "cadence", "synopsys", "xilinx", "vivado", "quartus",
        "modelsim", "questasim", "simulink", "labview",
    ],
    "Mechanical Engineering": [
        "cad", "cam", "solidworks", "autocad", "catia", "creo",
        "unigraphics", "nx", "solidedge", "inventor", "freecad",
        "ansys", "abaqus", "comsol", "fluent", "cfd",
        "finite element analysis", "fea", "fem",
        "thermodynamics", "heat transfer", "fluid mechanics",
        "manufacturing", "cnc", "cnc machining", "3d printing",
        "additive manufacturing", "gd&t", "mechanical design",
        "materials science", "metallurgy", "composites",
        "vibration analysis", "structural analysis",
        "hvac", "piping", "pneumatics", "hydraulics",
        "strength of materials", "statics", "dynamics",
    ],
    "Civil Engineering": [
        "staad pro", "etabs", "revit", "primavera",
        "structural engineering", "geotechnical engineering",
        "surveying", "gis", "remote sensing",
        "concrete technology", "steel design",
        "construction management", "quantity surveying",
        "transportation engineering", "water resources",
        "environmental engineering", "soil mechanics",
        "building information modeling", "bim",
    ],
    "Chemical / Biomedical": [
        "aspen plus", "chemcad", "hysys",
        "process engineering", "process control",
        "chemical engineering", "reaction engineering",
        "biomedical engineering", "bioinformatics",
        "genomics", "proteomics", "molecular biology",
        "cell biology", "biochemistry", "microbiology",
        "drug discovery", "pharmacology",
    ],
    "Vector Databases / RAG": [
        "vector database", "chromadb", "pinecone", "weaviate",
        "faiss", "qdrant", "milvus",
    ],
    "Cloud / DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
        "ci/cd", "terraform", "ansible", "linux", "nginx", "grafana",
        "prometheus", "helm", "github actions", "gitlab ci",
        "istio", "elk stack", "cloudformation", "pulumi", "vagrant",
        "digitalocean", "vercel", "netlify", "apache",
    ],
    "Data Engineering / Science": [
        "data analysis", "statistics", "pandas", "numpy", "scipy",
        "data visualization", "tableau", "power bi", "spark", "hadoop",
        "kafka", "airflow", "etl", "big data", "snowflake", "dbt",
        "prefect", "dagster", "data pipeline", "data modeling",
        "data warehouse", "databricks", "matplotlib", "seaborn", "plotly",
        "looker", "spss", "minitab", "mathematica", "maple",
    ],
    "Web / Mobile": [
        "react", "angular", "vue", "node.js", "django", "flask",
        "android", "ios", "flutter", "next.js", "express", "graphql",
        "rest api", "fastapi", "streamlit", "gradio",
        "nuxt.js", "spring boot", "spring", "hibernate", ".net core",
        "blazor", "celery", "rabbitmq",
        "tailwind", "sass", "less", "webpack", "vite", "babel",
        "websockets", "oauth", "jwt", "three.js", "svelte", "remix",
        "astro", "react native", "swiftui", "jetpack compose",
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "oracle", "sql server", "neo4j",
        "supabase", "firebase", "influxdb", "timescaledb",
        "cockroachdb", "mariadb", "dbms",
    ],
    "CS Fundamentals": [
        "data structures", "algorithms", "object oriented programming",
        "operating systems", "computer networks", "system design",
        "design patterns", "solid principles", "clean architecture",
        "distributed systems", "microservices", "event driven architecture",
    ],
    "Math / Science": [
        "numerical methods", "linear algebra", "calculus",
        "differential equations", "probability", "optimization",
        "complex analysis", "quantum mechanics", "classical mechanics",
    ],
    "Tools": [
        "git", "github", "postman", "swagger", "jira", "notion", "figma",
        "vs code", "intellij", "pycharm", "vim", "neovim",
        "selenium", "cypress", "playwright", "jest", "pytest", "junit",
        "beautifulsoup", "scrapy", "puppeteer", "web scraping",
        "pygame", "tkinter", "qt", "electron",
        "bash", "cmake", "makefile", "gdb", "svn", "mercurial",
        "microsoft office", "excel", "overleaf",
        "android studio",
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "project management",
        "problem solving", "critical thinking", "time management",
        "presentation", "negotiation", "agile", "scrum", "kanban",
        "technical documentation", "code review", "technical writing",
        "operations research", "supply chain", "lean manufacturing",
        "six sigma", "quality control",
    ],
    "Energy / Sustainability": [
        "renewable energy", "solar energy", "wind energy",
        "energy storage", "battery technology",
        "electric vehicles", "ev",
        "aerospace engineering", "aerodynamics",
    ],
}

# ── Skill alias map (abbreviations → canonical) ───────────────────────
SKILL_ALIASES = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "dl": "deep learning",
    "nn": "neural networks",
    "cv": "computer vision",
    "rl": "reinforcement learning",
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "aws": "aws",
    "gcp": "gcp",
    "devops": "devops",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "restapi": "rest api",
    "rest apis": "rest api",
    "postgres": "postgresql",
    "mongo": "mongodb",
    # New aliases
    "oop": "object oriented programming",
    "oops": "object oriented programming",
    "llms": "llm",
    "large language model": "llm",
    "large language models": "llm",
    "rag": "retrieval-augmented generation",
    "retrieval augmented generation": "retrieval-augmented generation",
    "dsa": "data structures",
    "ds": "data structures",
    "os": "operating systems",
    "cn": "computer networks",
    "rdbms": "dbms",
    "database management": "dbms",
    "bs4": "beautifulsoup",
    "beautiful soup": "beautifulsoup",
    "sk learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "sci kit learn": "scikit-learn",
    "vscode": "vs code",
    "visual studio code": "vs code",
    "sb": "spring boot",
    "springboot": "spring boot",
    "dotnet": ".net",
    "dot net": ".net",
    # Engineering aliases
    "dsp": "digital signal processing",
    "emw": "em waves",
    "pid": "pid controller",
    "iot": "internet of things",
    "fea": "finite element analysis",
    "fem": "finite element analysis",
    "bim": "building information modeling",
    "cfd": "computational fluid dynamics",
    "ev": "electric vehicles",
    "rpi": "raspberry pi",
    "raspi": "raspberry pi",
    "raspberry": "raspberry pi",
    "autocadd": "autocad",
    "solidwork": "solidworks",
    "labview": "labview",
    "ros2": "ros",
    "pcb": "pcb design",
}

# ── Deduplication groups (keep canonical form) ─────────────────────────
SKILL_DEDUP_GROUPS = {
    "java": ["core java", "java programming", "java se", "java ee"],
    "python": ["python3", "python 3", "python programming", "cpython"],
    "javascript": ["js", "ecmascript", "es6"],
    "machine learning": ["ml", "machine-learning"],
    "deep learning": ["dl", "deep-learning"],
    "natural language processing": ["nlp", "text mining"],
    "docker": ["docker containers", "dockerized"],
    "kubernetes": ["k8s", "kube"],
    "sql": ["structured query language"],
    "rest api": ["restful api", "rest apis", "restful", "restapi"],
    "ci/cd": ["ci cd", "cicd", "continuous integration"],
    "react": ["reactjs", "react.js"],
    "node.js": ["nodejs", "node"],
    "angular": ["angularjs", "angular.js"],
    "vue": ["vuejs", "vue.js"],
    "tensorflow": ["tf", "tensor-flow"],
    "pytorch": ["py-torch"],
}

# ── Experience-level keywords ──────────────────────────────────────────
EXPERIENCE_KEYWORDS = {
    "entry": ["entry level", "junior", "intern", "fresh", "0-1 year", "0-2 year"],
    "mid": ["mid level", "2-5 year", "3-5 year", "2+ year", "3+ year"],
    "senior": ["senior", "lead", "5+ year", "7+ year", "principal", "staff"],
    "executive": ["director", "vp", "cto", "cio", "head of", "10+ year"],
}

# ── Proficiency keywords ──────────────────────────────────────────────
PROFICIENCY_KEYWORDS = {
    "advanced": [
        "expert", "advanced", "proficient", "extensive experience",
        "deep knowledge", "mastery", "specialist", "5+ years",
    ],
    "intermediate": [
        "intermediate", "working knowledge", "competent",
        "familiar", "hands-on", "2+ years", "3+ years",
    ],
    "basic": [
        "basic", "beginner", "novice", "exposure", "introductory",
        "coursework", "academic", "learning",
    ],
}
