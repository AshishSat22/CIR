from flask import Flask, render_template, request, jsonify

import PyPDF2
import io
import re

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
        "Programming": 5, "AI/ML": 5, "System Design": 3, "Cybersecurity": 2, "Cloud Computing": 4
    },
    "Full-Stack Developer": {
        "Programming": 5, "AI/ML": 2, "System Design": 4, "Cybersecurity": 3, "Cloud Computing": 3
    },
    "Frontend Developer": {
        "Programming": 5, "AI/ML": 1, "System Design": 3, "Cybersecurity": 2, "Cloud Computing": 2
    },
    "Backend Developer": {
        "Programming": 5, "AI/ML": 2, "System Design": 5, "Cybersecurity": 3, "Cloud Computing": 4
    },
    "DevOps Engineer": {
        "Programming": 3, "AI/ML": 1, "System Design": 4, "Cybersecurity": 4, "Cloud Computing": 5
    },
    "Cloud Architect": {
        "Programming": 3, "AI/ML": 2, "System Design": 5, "Cybersecurity": 4, "Cloud Computing": 5
    },
    "Cybersecurity Specialist": {
        "Programming": 3, "AI/ML": 2, "System Design": 3, "Cybersecurity": 5, "Cloud Computing": 4
    },
    "Data Scientist": {
        "Programming": 4, "AI/ML": 5, "System Design": 2, "Cybersecurity": 1, "Cloud Computing": 3
    },
    "Data Engineer": {
        "Programming": 5, "AI/ML": 3, "System Design": 4, "Cybersecurity": 2, "Cloud Computing": 4
    },
    "MLOps Engineer": {
        "Programming": 4, "AI/ML": 4, "System Design": 4, "Cybersecurity": 2, "Cloud Computing": 5
    },
    "Security Architect": {
        "Programming": 4, "AI/ML": 2, "System Design": 5, "Cybersecurity": 5, "Cloud Computing": 5
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
    # ... (existing code for upload_resume)
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text().lower()

        # Section Extraction (Experience, Projects, Internships)
        sections = {
            "experience": re.findall(r'(experience|work history|employment)(.*?)(projects|skills|education|internships|$)', text, re.S),
            "projects": re.findall(r'(projects|academic projects)(.*?)(experience|skills|education|internships|$)', text, re.S),
            "internships": re.findall(r'(internships|training)(.*?)(experience|skills|education|projects|$)', text, re.S)
        }
        
        # Flatten section text
        exp_text = " ".join([s[1] for s in sections['experience']])
        proj_text = " ".join([s[1] for s in sections['projects']])
        intern_text = " ".join([s[1] for s in sections['internships']])
        high_value_text = exp_text + " " + proj_text + " " + intern_text
        
        # New Parameters
        complexity_keywords = ["distributed", "scalable", "high-performance", "real-time", "end-to-end", "optimized", "concurrency"]
        achievement_keywords = ["winner", "rank", "award", "scholarship", "first place", "certified"]
        leadership_keywords = ["led", "managed", "mentored", "coordinated", "architected"]

        extracted_skills = {}
        for skill_cat, keywords in SKILL_KEYWORDS.items():
            unique_found = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text)]
            total_mentions = sum(len(re.findall(r'\b' + re.escape(kw) + r'\b', text)) for kw in keywords)
            hv_mentions = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', high_value_text))
            
            complexity_found = 0
            leadership_found = 0
            for kw in unique_found:
                context_pattern = rf'.{{0,60}}\b{re.escape(kw)}\b.{{0,60}}'
                contexts = re.findall(context_pattern, text)
                for ctx in contexts:
                    if any(c in ctx for c in complexity_keywords): complexity_found += 1
                    if any(l in ctx for l in leadership_keywords): leadership_found += 1

            global_achievements = sum(1 for a in achievement_keywords if re.search(r'\b' + re.escape(a) + r'\b', text))

            score = 1 # Base
            if len(unique_found) >= 1: score += 1
            if total_mentions > 3: score += 1
            if hv_mentions >= 2: score += 0.5
            if complexity_found >= 1: score += 1
            if leadership_found >= 1: score += 0.5
            if global_achievements >= 1: score += 0.5
            extracted_skills[skill_cat] = min(5, round(score))

        return jsonify({"extracted_skills": extracted_skills, "message": "High-Precision Analysis Complete!"})
    except Exception as e:
        return jsonify({"error": f"Failed to parse PDF: {str(e)}"}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    user_skills = {
        "Programming": int(request.form.get('Programming', 1)),
        "AI/ML": int(request.form.get('AI/ML', 1)),
        "System Design": int(request.form.get('System Design', 1)),
        "Cybersecurity": int(request.form.get('Cybersecurity', 1)),
        "Cloud Computing": int(request.form.get('Cloud Computing', 1))
    }
    
    target_role = request.form.get('target_role', 'AI/ML Engineer')
    standards = INDUSTRY_STANDARDS.get(target_role)
    
    # Calculate Gaps
    gaps = {}
    total_match = 0
    for skill, value in standards.items():
        gap = max(0, value - user_skills[skill])
        gaps[skill] = gap
        total_match += (1 - (gap / 5)) * 20 
        
    # ROLE-SPECIFIC ROADMAP GENERATION
    role_steps = ROLE_ROADMAP_STEPS.get(target_role, ["Master Core Fundamentals", "Build Industry Projects", "Prepare for Technical Interviews", "Get Certified"])
    sorted_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)
    
    roadmap = []
    phases = ["Foundation", "Advanced Mastery", "Expert Excellence"]
    for i, step_text in enumerate(role_steps):
        phase_idx = min(i // 2, 2)
        # Link the step to the highest remaining gap
        relevant_gap_skill = sorted_gaps[min(i, len(sorted_gaps)-1)][0]
        gap_val = gaps[relevant_gap_skill]
        
        roadmap.append({
            "phase": phases[phase_idx],
            "skill": step_text,
            "duration": f"{max(2, gap_val * 2)} Weeks",
            "action": f"Critical step for {target_role} readiness. Focuses on bridging your {relevant_gap_skill} gap."
        })

    # Action Cards
    action_cards = []
    for skill, gap_val in sorted_gaps[:3]:
        if skill in RECOMMENDATIONS:
            action_cards.append({
                "skill": skill,
                "details": RECOMMENDATIONS[skill]
            })

    # Dynamic Resume Advice
    top_gap_skill = sorted_gaps[0][0] if sorted_gaps else "General"
    advice = f"To excel as a {target_role}, your priority should be {top_gap_skill}. "
    if gaps.get(top_gap_skill, 0) > 2:
        advice += f"Follow the official roadmap.sh/{RECOMMENDATIONS[top_gap_skill]['RoadmapSH'].split('/')[-1]} path to master this domain."
    else:
        advice += "Your profile is highly competitive! Focus on high-level system design to reach the Architect tier."

    return jsonify({
        "role": target_role,
        "match_percentage": round(total_match, 1),
        "user_skills": user_skills,
        "industry_skills": standards,
        "roadmap": roadmap,
        "action_cards": action_cards,
        "resume_advice": advice
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
