
import pdfplumber
pdf_path = "/Users/chrishsieh/Documents/DongPoCi/DongPo_HuangZou.pdf"
transcript_pages = []
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text()
        if text:
            transcript_pages.append(text)
full_transcript = "\n".join(transcript_pages)
# Output the full transcript
print(full_transcript)

output_file = "transcript_pdfplumber.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_transcript)
print(f"Transcript saved to {output_file}")