import fitz

pdf_path = "/Users/chrishsieh/Documents/DongPoCi/DongPo_HuangZou.pdf"
doc = fitz.open(pdf_path)
transcript = []
for page in doc:
    text = page.get_text()
    if text:
        transcript.append(text)
full_transcript = "\n".join(transcript)
print(full_transcript)

output_file = "transcript_pymupdf.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_transcript)
print(f"Transcript saved to {output_file}")
