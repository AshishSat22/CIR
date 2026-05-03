"use client";

import React, { useState } from 'react';
import { Search, Loader2, BookOpen, Download, FileText, CheckCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<"idle" | "scanning" | "synthesizing" | "preview" | "generating_pdf">("idle");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    try {
      setError("");
      setStatus("scanning");
      
      // Simulate Antigravity scanning indicator delay for effect
      await new Promise(resolve => setTimeout(resolve, 1500));
      setStatus("synthesizing");
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/extract`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "bypass-tunnel-reminder": "true" 
        },
        body: JSON.stringify({ url }),
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to process video");
      }
      
      const data = await response.json();
      setNotes(data.notes);
      setStatus("preview");
      
    } catch (err: any) {
      setError(err.message);
      setStatus("idle");
    }
  };

  const handleDownloadPDF = async () => {
    try {
      setStatus("generating_pdf");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/generate-pdf`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "bypass-tunnel-reminder": "true" 
        },
        body: JSON.stringify({ markdown_text: notes }),
      });
      
      if (!response.ok) {
        throw new Error("Failed to generate PDF");
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = "YTScholar_Study_Materials.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      setStatus("preview");
    } catch (err: any) {
      setError(err.message);
      setStatus("preview");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-serif text-slate-800">
      <header className="bg-white border-b border-slate-200 py-4 sm:py-6 px-4 sm:px-8 flex items-center justify-between shadow-sm sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <BookOpen className="text-white w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">YT<span className="font-light text-slate-500">Scholar</span></h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-8 sm:mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4 text-slate-900 leading-tight">Transform Lectures into <br className="hidden sm:block"/><span className="text-blue-600">Exam-Ready Materials</span></h2>
          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto font-sans">
            Input any educational YouTube link and our AI will synthesize the transcript into structured, high-yield study notes.
          </p>
        </div>

        <form onSubmit={handleGenerate} className="mb-12 max-w-2xl mx-auto">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1 flex items-center bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 transition-all">
              <div className="pl-4 text-slate-400">
                <Search className="w-5 h-5" />
              </div>
              <input
                type="url"
                required
                placeholder="Paste YouTube URL here..."
                className="w-full py-4 px-4 outline-none font-sans text-slate-700 bg-transparent"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={status !== "idle" && status !== "preview"}
              />
            </div>
            <button
              type="submit"
              disabled={status !== "idle" && status !== "preview"}
              className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl shadow-lg font-sans font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2"
            >
              {status === "idle" || status === "preview" ? "Generate Notes" : "Processing..."}
            </button>
          </div>
          {error && <p className="mt-3 text-red-500 text-sm font-sans text-center">{error}</p>}
        </form>

        {/* Progress Indicators */}
        {(status === "scanning" || status === "synthesizing" || status === "generating_pdf") && (
          <div className="max-w-md mx-auto bg-white p-6 rounded-xl shadow-md border border-slate-100 mb-12">
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                {status === "scanning" ? <Loader2 className="w-5 h-5 animate-spin text-blue-500" /> : <CheckCircle className="w-5 h-5 text-green-500" />}
                <span className={`font-sans font-medium ${status === "scanning" ? 'text-blue-700' : 'text-slate-600'}`}>Scanning Audio & Fetching Transcript...</span>
              </div>
              <div className="flex items-center gap-3">
                {status === "scanning" ? <div className="w-5 h-5 rounded-full border-2 border-slate-200" /> : 
                 status === "synthesizing" ? <Loader2 className="w-5 h-5 animate-spin text-blue-500" /> : <CheckCircle className="w-5 h-5 text-green-500" />}
                <span className={`font-sans font-medium ${status === "synthesizing" ? 'text-blue-700' : 'text-slate-500'}`}>Synthesizing Concepts & Extracting Knowledge...</span>
              </div>
              <div className="flex items-center gap-3">
                {status !== "generating_pdf" ? <div className="w-5 h-5 rounded-full border-2 border-slate-200" /> : <Loader2 className="w-5 h-5 animate-spin text-blue-500" />}
                <span className={`font-sans font-medium ${status === "generating_pdf" ? 'text-blue-700' : 'text-slate-500'}`}>Generating High-Fidelity PDF...</span>
              </div>
            </div>
          </div>
        )}

        {/* Preview Section */}
        {status === "preview" && notes && (
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden transition-all print:shadow-none print:border-none">
            <div className="bg-slate-50 border-b border-slate-200 px-4 sm:px-8 py-4 flex flex-col sm:flex-row gap-4 justify-between items-center print:hidden">
              <div className="flex items-center gap-2">
                <FileText className="text-slate-500 w-5 h-5" />
                <h3 className="font-sans font-semibold text-slate-700">Study Guide Preview</h3>
              </div>
              <button 
                onClick={handleDownloadPDF}
                className="w-full sm:w-auto flex justify-center items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg font-sans text-sm font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                Download PDF
              </button>
            </div>
            
            <div className="p-6 sm:p-10 prose prose-sm sm:prose-base prose-slate max-w-none prose-headings:font-serif prose-headings:text-slate-900 prose-h1:text-2xl sm:prose-h1:text-3xl prose-h2:text-xl sm:prose-h2:text-2xl prose-h3:text-lg sm:prose-h3:text-xl prose-a:text-blue-600 print:p-0">
              <ReactMarkdown>{notes}</ReactMarkdown>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
