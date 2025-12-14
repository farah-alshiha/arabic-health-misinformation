# Multimodal Detection of Arabic Health Misinformation

This repository contains the codebase for a multimodal deep-learning pipeline
that detects health misinformation in Arabic social-media posts by jointly
analyzing tweet text, OCR-extracted image text, and visual content.

## Pipeline Overview
1. Tweet collection via TwitterAPI.io
2. Image filtering and download
3. OCR extraction (Tesseract / EasyOCR)
4. LLM-assisted labeling (true / false / misleading)
5. Multimodal feature extraction using CLIP and AraBERT
6. Supervised classification and evaluation

## Repository Structure
- `src/`: data collection, preprocessing, OCR, labeling, and pipeline execution
- `notebooks/`: embedding extraction and classification experiments
- `data/`: intermediate datasets (not tracked by git)
- `tweet_images/`: downloaded images (not tracked by git)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt