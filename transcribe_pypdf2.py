import PyPDF2

pdf_path = "/Users/chrishsieh/Documents/DongPoCi/DongPo_HuangZou.pdf"
reader = PyPDF2.PdfReader(pdf_path)
full_text = []
for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text.append(text)
# Combine all page texts
transcript = "\n".join(full_text)
print(transcript)
# Write the transcript to a text file
output_file = "transcript_pypdf.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(transcript)
print(f"Transcript saved to {output_file}")


