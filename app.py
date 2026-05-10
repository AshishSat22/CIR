import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2
import io
import re
import json

load_dotenv()

# Configure Gemini
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

app = Flask(__name__)

# Keyword Mapping for Resume Parsing
SKILL_KEYWORDS = {
    "Programming": ["python", "java", "c++", "javascript", "rust", "go", "typescript", "backend", "frontend"],
    "AI/ML": ["pytorch", "tensorflow", "scikit-learn", "nlp", "computer vision", "llm", "neural networks", "machine learning"],
    "System Design": ["microservices", "distributed systems", "scalability", "load balancer", "caching", "database design", "api"],
    "Cybersecurity": ["penetration testing", "firewall", "encryption", "siem", "ethical hacking", "soc", "network security"],
    "Cloud Computing": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "serverless", "cloud native"]
}

# Industry Standards Benchmarks (Scale 1-5)
INDUSTRY_STANDARDS = {
    "AI/ML Engineer": {
        "Programming": 5, "AI/ML": 5, "System Design": 3, "Cybersecurity": 2, "Cloud Computing": 4,
        "Leadership": 3, "Communication": 4, "Teamwork": 5
    },
    "Full-Stack Developer": {
        "Programming": 5, "AI/ML": 2, "System Design": 4, "Cybersecurity": 3, "Cloud Computing": 3,
        "Leadership": 3, "Communication": 5, "Teamwork": 5
    },
    "Frontend Developer": {
        "Programming": 5, "AI/ML": 1, "System Design": 3, "Cybersecurity": 2, "Cloud Computing": 2,
        "Leadership": 2, "Communication": 5, "Teamwork": 5
    },
    "Backend Developer": {
        "Programming": 5, "AI/ML": 2, "System Design": 5, "Cybersecurity": 3, "Cloud Computing": 4,
        "Leadership": 3, "Communication": 4, "Teamwork": 5
    },
    "DevOps Engineer": {
        "Programming": 3, "AI/ML": 1, "System Design": 4, "Cybersecurity": 4, "Cloud Computing": 5,
        "Leadership": 4, "Communication": 4, "Teamwork": 5
    },
    "Cloud Architect": {
        "Programming": 3, "AI/ML": 2, "System Design": 5, "Cybersecurity": 4, "Cloud Computing": 5,
        "Leadership": 5, "Communication": 5, "Teamwork": 4
    },
    "Cybersecurity Specialist": {
        "Programming": 3, "AI/ML": 2, "System Design": 3, "Cybersecurity": 5, "Cloud Computing": 4,
        "Leadership": 3, "Communication": 4, "Teamwork": 4
    },
    "Data Scientist": {
        "Programming": 4, "AI/ML": 5, "System Design": 2, "Cybersecurity": 1, "Cloud Computing": 3,
        "Leadership": 2, "Communication": 5, "Teamwork": 4
    },
    "Data Engineer": {
        "Programming": 5, "AI/ML": 3, "System Design": 4, "Cybersecurity": 2, "Cloud Computing": 4,
        "Leadership": 3, "Communication": 4, "Teamwork": 5
    },
    "MLOps Engineer": {
        "Programming": 4, "AI/ML": 4, "System Design": 4, "Cybersecurity": 2, "Cloud Computing": 5,
        "Leadership": 4, "Communication": 4, "Teamwork": 5
    },
    "Security Architect": {
        "Programming": 4, "AI/ML": 2, "System Design": 5, "Cybersecurity": 5, "Cloud Computing": 5,
        "Leadership": 5, "Communication": 5, "Teamwork": 4
    }
}

RECOMMENDATIONS = {
    "Programming": {
        "Project": "Build a Concurrent Web Scraper in Go/Rust",
        "Certification": "Meta Back-End Developer Professional Certificate",
        "Course": "CS50's Introduction to Computer Science",
        "CourseraLink": "https://www.coursera.org/professional-certificates/meta-back-end-developer",
        "RoadmapSH": "https://roadmap.sh/backend",
        "Books": "Clean Code (Robert C. Martin), Pragmatic Programmer",
        "YouTube": "The Cherno, Traversy Media",
        "Prep": "LeetCode (Focus: Data Structures)"
    },
    "AI/ML": {
        "Project": "Develop a Custom LLM Fine-tuning Pipeline",
        "Certification": "Deep Learning Specialization",
        "Course": "Deep Learning Specialization (Andrew Ng)",
        "CourseraLink": "https://www.coursera.org/specializations/deep-learning",
        "RoadmapSH": "https://roadmap.sh/ai-engineer",
        "Books": "Hands-On Machine Learning (Aurélien Géron)",
        "YouTube": "Sentdex, 3Blue1Brown (Neural Networks)",
        "Prep": "Kaggle Competitions, StatQuest"
    },
    "System Design": {
        "Project": "Design a Distributed Key-Value Store",
        "Certification": "Software Design and Architecture",
        "Course": "Grokking the System Design Interview",
        "CourseraLink": "https://www.coursera.org/specializations/software-design-architecture",
        "RoadmapSH": "https://roadmap.sh/system-design",
        "Books": "Designing Data-Intensive Applications (Martin Kleppmann)",
        "YouTube": "Success in Tech, Gaurav Sen",
        "Prep": "System Design Primer (GitHub)"
    },
    "Cybersecurity": {
        "Project": "Set up a Home Lab for Penetration Testing",
        "Certification": "Google Cybersecurity Professional Certificate",
        "Course": "Google Cybersecurity Professional Certificate",
        "CourseraLink": "https://www.coursera.org/professional-certificates/google-cybersecurity",
        "RoadmapSH": "https://roadmap.sh/cyber-security",
        "Books": "The Web Application Hacker's Handbook",
        "YouTube": "NetworkChuck, David Bombal",
        "Prep": "TryHackMe, Hack The Box"
    },
    "Cloud Computing": {
        "Project": "Deploy a Multi-Region Serverless App on AWS",
        "Certification": "Google Associate Cloud Engineer",
        "Course": "Cloud Computing Specialization",
        "CourseraLink": "https://www.coursera.org/specializations/cloud-computing",
        "RoadmapSH": "https://roadmap.sh/devops",
        "Books": "Cloud Native Patterns (Cornelia Davis)",
        "YouTube": "TechWorld with Nana, AWS Official",
        "Prep": "Cloud Academy, A Cloud Guru"
    }
}

ROLE_ROADMAP_STEPS = {
    "AI/ML Engineer": ["Master Linear Algebra & Calculus", "Advanced Deep Learning with PyTorch", "LLM Fine-tuning & Prompt Engineering", "MLOps & Model Deployment"],
    "Full-Stack Developer": ["Advanced React/Next.js Patterns", "Distributed Backend with Go/Node", "System Scalability & Caching", "CI/CD & Cloud Deployment"],
    "DevOps Engineer": ["Container Orchestration with Kubernetes", "Infrastructure as Code (Terraform)", "Security & Compliance Automation", "Observability & SRE Principles"],
    "Data Engineer": ["Big Data Processing (Spark/Flink)", "Data Warehousing (Snowflake/Redshift)", "ETL Orchestration (Airflow)", "Data Governance & Quality"],
    "Cybersecurity Specialist": ["Network Traffic Analysis", "Cloud Security Posture (CSPM)", "Digital Forensics & Incident Response", "Offensive Security & Pentesting"],
    "Data Scientist": ["Advanced Statistical Modeling", "Exploratory Data Analysis (EDA) at Scale", "Data Visualization & Storytelling", "A/B Testing & Causal Inference"]
}

@app.route('/')
def index():
    return render_template('index.html', roles=INDUSTRY_STANDARDS.keys())

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not model:
        return jsonify({"error": "AI Model not configured. Please set GOOGLE_API_KEY."}), 500

    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Gemini Prompt for Semantic Parsing
        prompt = f"""
        Analyze the following resume text and provide a JSON response evaluating the candidate's skill levels on a scale of 1-5 for the following categories:
        1. Programming
        2. AI/ML
        3. System Design
        4. Cybersecurity
        5. Cloud Computing
        6. Leadership (Extract from project lead roles, team management, etc.)
        7. Communication (Extract from presentations, documentation, public speaking)
        8. Teamwork (Extract from collaborative projects)

        Also provide a short 'message' summarizing the resume's strength.

        Rules:
        - If a skill is not mentioned at all, score it 1.
        - Look for semantic context (e.g., 'Kubernetes' implies Cloud Computing).
        - Be objective and critical.

        Resume Text:
        {text}

        Return ONLY valid JSON.
        """

        response = model.generate_content(prompt)
        
        # Clean response text (remove markdown code blocks if present)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)
        
        # Format for frontend
        extracted_skills = {
            "Programming": result.get("Programming", 1),
            "AI/ML": result.get("AI/ML", 1),
            "System Design": result.get("System Design", 1),
            "Cybersecurity": result.get("Cybersecurity", 1),
            "Cloud Computing": result.get("Cloud Computing", 1),
            "Leadership": result.get("Leadership", 1),
            "Communication": result.get("Communication", 1),
            "Teamwork": result.get("Teamwork", 1)
        }

        return jsonify({
            "extracted_skills": extracted_skills, 
            "message": result.get("message", "High-Precision AI Analysis Complete!")
        })
    except Exception as e:
        return jsonify({"error": f"Failed to parse resume: {str(e)}"}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    user_skills = {
        "Programming": int(request.form.get('Programming', 1)),
        "AI/ML": int(request.form.get('AI/ML', 1)),
        "System Design": int(request.form.get('System Design', 1)),
        "Cybersecurity": int(request.form.get('Cybersecurity', 1)),
        "Cloud Computing": int(request.form.get('Cloud Computing', 1)),
        "Leadership": int(request.form.get('Leadership', 1)),
        "Communication": int(request.form.get('Communication', 1)),
        "Teamwork": int(request.form.get('Teamwork', 1))
    }
    
    target_role = request.form.get('target_role', 'AI/ML Engineer')
    standards = INDUSTRY_STANDARDS.get(target_role)
    
    if not model:
        return jsonify({"error": "AI Model not configured."}), 500

    try:
        # Prompt for Dynamic Roadmap and Match Score
        prompt = f"""
        Act as a high-end career coach. Compare the following user skill levels against the industry standard for the role: {target_role}.
        
        User Skills: {json.dumps(user_skills)}
        Industry Standard: {json.dumps(standards)}

        Tasks:
        1. Calculate a 'match_percentage' (0-100) based on how close the user is to the standard.
        2. Generate a 3-phase 'roadmap' (Foundation, Advanced Mastery, Expert Excellence) with specific, non-generic steps to bridge the gaps. 
           Each step should have 'phase', 'skill', 'duration', and 'action'.
        3. Provide 3 'action_cards' for the top 3 gaps. Each card should have 'skill' and 'details'. 
           'details' must include: 'Project' (a specific project to build), 'Course' (a specific recommended course), 'Books', 'CourseraLink', and 'RoadmapSH'.
        4. Provide 'resume_advice' (a personalized tip).

        Return ONLY valid JSON.
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)

        return jsonify({
            "role": target_role,
            "match_percentage": result.get("match_percentage", 0),
            "user_skills": user_skills,
            "industry_skills": standards,
            "roadmap": result.get("roadmap", []),
            "action_cards": result.get("action_cards", []),
            "resume_advice": result.get("resume_advice", "Keep learning!")
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate roadmap: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
