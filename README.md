# chinese_vertical_ocr_for_exam_craming

## Adjustable Parameters
lang = "chi_tra_vert" (vertical chinese) \
--psm 5 (vertical layout OCR) \
--oem 1 (LSTM)

## Execution
Some routes are given by my mac system

### For Chinese vertical OCR
```shell
python3 pdf_pro_parser_chinese_vertical.py <input_file> -o <output_file>
```
ex:
```shell
python3 pdf_pro_parser_chinese_vertical.py DongPo_HuangZou.pdf -o dongpo_analysis.json
```

### For Chinese horizontal OCR
```shell
python3 pdf_pro_parser_chinese_horizontal.py <input_file> -o <output_file>
```
ex:
```shell
python3 pdf_pro_parser_chinese_horizontal.py DongPo_HuangZou.pdf -o dongpo_analysis.json
```

### For English OCR
```shell
python3 pdf_pro_parser.py <input_file> -o <output_file>
```
ex:
```shell
python3 pdf_pro_parser.py DongPo_HuangZou.pdf -o dongpo_analysis.json
```

### Run.sh is not working for converting pdf to txt
(Not working...)
(Including three files: transcribe_pypdf2.py, transcribe_pdfplumber.py, transcribe_pymupdf.py)
```shell
bash run.sh # Not working...
```


