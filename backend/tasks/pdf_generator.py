import os
from fpdf import FPDF
from datetime import datetime

class PDFReportGenerator:
    @staticmethod
    def generate_summary(task_id: str, transcript: list, properties: list, legal_notes: list) -> str:
        """
        Generates a PDF summary of the conversation and saves it.
        Returns the relative URL to access the PDF.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font("Helvetica", style="B", size=18)
        pdf.cell(0, 10, "Mycel Real Estate - Consultation Summary", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(0, 10, f"Task ID: {task_id}", ln=True)
        pdf.ln(10)
        
        # Properties
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 10, "Properties Discussed", ln=True)
        pdf.set_font("Helvetica", size=10)
        if properties:
            for p in properties:
                pdf.multi_cell(0, 8, f"- {p.get('name', 'Property')}: {p.get('description', '')} ({p.get('price', '')})")
        else:
            pdf.cell(0, 8, "No properties were discussed in this session.", ln=True)
        pdf.ln(5)
        
        # Legal Notes
        if legal_notes:
            pdf.set_font("Helvetica", style="B", size=14)
            pdf.cell(0, 10, "Legal Consulations", ln=True)
            pdf.set_font("Helvetica", size=10)
            for note in legal_notes:
                pdf.multi_cell(0, 8, f"Q: {note.get('question', '')}\nA: {note.get('answer', '')}")
            pdf.ln(5)
            
        # Transcript
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 10, "Conversation Transcript", ln=True)
        pdf.set_font("Helvetica", size=10)
        if transcript:
            for line in transcript:
                speaker = line.get("speaker", "Unknown")
                text = line.get("text", "")
                
                # Replace unicode characters that might break standard fonts
                text = text.encode('ascii', 'ignore').decode('ascii')
                pdf.multi_cell(0, 8, f"[{speaker}]: {text}")
        else:
            pdf.cell(0, 8, "No conversation recorded.", ln=True)
            
        # Save to static directory
        static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "reports")
        os.makedirs(static_dir, exist_ok=True)
        
        filename = f"consultation_{task_id}.pdf"
        filepath = os.path.join(static_dir, filename)
        pdf.output(filepath)
        
        return f"/static/reports/{filename}"
