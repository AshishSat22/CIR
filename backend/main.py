from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from langchain_text_splitters import RecursiveCharacterTextSplitter
import g4f
from g4f.client import Client
import nest_asyncio
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

nest_asyncio.apply()
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from io import BytesIO
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str

class PDFRequest(BaseModel):
    markdown_text: str

def extract_video_id(url: str) -> Optional[str]:
    # Extract YouTube video ID
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

from g4f.Provider import PollinationsAI

def process_transcript_with_llm(text: str) -> str:
    # Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    
    core_text = chunks[0] if chunks else ""
    if len(core_text) == 0:
         return "No transcript content found."
    
    prompt = f"""Analyze the provided transcript. First, identify the primary subject matter and the lecturer's core thesis.
        Structure the output as follows:
        
        # Lecture Metadata
        - **Title**: [Derive a title]
        - **Speaker**: [If mentioned, else Unknown]
        - **Duration**: [Approximate or omit]
        
        # The 3-3-3 Rule
        ## 3 Essential Concepts
        1. 
        2. 
        3. 
        
        ## 3 Practical Examples
        1. 
        2. 
        3. 
        
        ## 3 Study Questions
        1. 
        2. 
        3. 
        
        # Chronological Breakdown
        [Organized notes with chronological flow]
        
        # Reference Box
        [Define any equations, jargon, or complex theories]
        
        Ensure you use clear Markdown headers (#, ##) and bolding for key vocabulary.
        
        Transcript:
        {core_text}
        """
    
    try:
        client = Client()
        response = client.chat.completions.create(
            model="openai",
            provider=PollinationsAI,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error using PollinationsAI: {e}")
        # fallback to default
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

@app.post("/api/extract")
async def extract_knowledge(request: ExtractRequest):
    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
        formatter = TextFormatter()
        formatted_transcript = formatter.format_transcript(transcript)
        
        notes = process_transcript_with_llm(formatted_transcript)
        return {"notes": notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-pdf")
async def generate_pdf(request: PDFRequest):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        
        # Add some custom academic styles
        styles.add(ParagraphStyle(name='AcademicTitle', parent=styles['Heading1'], fontName='Times-Bold', fontSize=24, spaceAfter=20, textColor=HexColor('#1a202c')))
        styles.add(ParagraphStyle(name='AcademicHeading', parent=styles['Heading2'], fontName='Times-Bold', fontSize=18, spaceAfter=14, textColor=HexColor('#2d3748')))
        styles.add(ParagraphStyle(name='AcademicSubHeading', parent=styles['Heading3'], fontName='Times-Bold', fontSize=14, spaceAfter=10, textColor=HexColor('#4a5568')))
        styles.add(ParagraphStyle(name='AcademicBody', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, spaceAfter=12, leading=16))
        
        Story = []
        
        # A very simple Markdown to PDF conversion for ReportLab
        lines = request.markdown_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                Story.append(Spacer(1, 0.1*inch))
                continue
            
            # Very basic markdown parsing for ReportLab formatting
            # ReportLab supports basic HTML-like tags: <b>, <i>
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
            
            if line.startswith('# '):
                Story.append(Paragraph(line[2:], styles['AcademicTitle']))
            elif line.startswith('## '):
                Story.append(Paragraph(line[3:], styles['AcademicHeading']))
            elif line.startswith('### '):
                Story.append(Paragraph(line[4:], styles['AcademicSubHeading']))
            elif line.startswith('- '):
                Story.append(Paragraph("• " + line[2:], styles['AcademicBody']))
            elif re.match(r'^\d+\.\s', line):
                Story.append(Paragraph(line, styles['AcademicBody']))
            else:
                Story.append(Paragraph(line, styles['AcademicBody']))
                
        doc.build(Story)
        buffer.seek(0)
        
        return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=study_materials.pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
