# NFS-e Extractor

Automatically extracts data from Brazilian electronic service invoices (NFS-e) in PDF format and consolidates everything into an Excel spreadsheet.

Reads both text-based PDFs and scanned invoices (images), using OCR.

## What it does

Given a folder of invoice PDFs, the program generates a spreadsheet with one row per invoice, containing the invoice number, dates, service provider, customer, municipality, amounts, taxes, and the information extracted from the service description (measurement, contract, period, lot).

The spreadsheet also includes a **revisar** (review) column, which flags invoices where the reading may have failed — a required field left empty or an incomplete authenticity code. These rows are highlighted in yellow for manual checking.

### Supported invoice formats

| Format | Examples |
|---|---|
| National standard (DANFSe) | Rio de Janeiro |
| Municipal ABRASF standard | Goiânia, Aparecida de Goiânia |

The program identifies the format on its own, invoice by invoice — a single PDF may contain both.

## Installation

### 1. Python

Install [Python 3.10 or higher](https://www.python.org/downloads/). On Windows, check the **"Add Python to PATH"** option during installation.

### 2. Tesseract (required)

Tesseract is the OCR engine used to read scanned invoices. It is a separate program and must be installed on its own.

- **Windows:** download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-por`
- **macOS:** `brew install tesseract tesseract-lang`

> **Important:** during installation on Windows, under *Additional language data*, select the **Portuguese** language. OCR will not work without it.

The program locates Tesseract on its own in the default installation paths. If you installed it elsewhere, create a `TESSERACT_PATH` environment variable pointing to `tesseract.exe`.

### 3. Project dependencies

In the project folder:

```bash
pip install -r requirements.txt
```

## Usage

### With the graphical interface (recommended)

```bash
python interface.py
```

Add the PDFs using the buttons and click **Gerar Excel** (Generate Excel). The spreadsheet is saved to `resultado/`.

To create a Desktop shortcut and stop needing the terminal, run this once:

```bash
python criar_atalho.py
```

For drag-and-drop support in the window, also install `tkinterdnd2` (optional — the buttons work fine without it).

### From the command line

Place the PDFs in the `notas/` folder and run:

```bash
python main.py
```

## Project structure

```
main.py               command-line entry point
interface.py          graphical interface
criar_atalho.py       creates the Desktop shortcut
config.py             paths and Tesseract detection

processador.py        walks through the PDFs page by page
leitor_pdf.py         chooses between native text and OCR
ocr.py                OCR for scanned pages
ocr_utils.py          tolerance for common OCR errors

normalizador.py       standardizes the text (accents, spacing)
limpeza.py            line-break cleanup
parser_nfse.py        identifies the format and splits it into blocks
extrator.py           fields for the municipal format
extrator_nacional.py  fields for the national format
interpretador.py      reads measurement, contract, period and lot
nota_fiscal.py        assembles everything into one invoice

excel.py              generates the spreadsheet and flags what to review
```

## Note on data

The `notas/` and `resultado/` folders are **not version-controlled**. Invoices contain tax IDs, amounts, contracts and third-party banking details, and must not be published.

Before pushing any changes, verify that no real PDF or spreadsheet is included in the commit.

## Known limitations

- OCR may misread digits on low-quality invoices. That is why the `revisar` column exists — **values should be spot-checked** before any formal use.
- The authenticity code is sometimes read with 49 digits instead of 50, when OCR loses a character in the image. Those invoices are flagged.
- When the invoice number cannot be read from the header, it is inferred from the authenticity code. This is an inference based on an observed pattern, not an officially documented rule.
- Only the two formats listed above are supported. Other municipal layouts would require their own extractor.

## License

Personal and educational use.
