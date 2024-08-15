# Relationship Subreddit Analyser

## Overview

This project aims to analyse submissions on the Relationships subreddit by processing the original and update submissions. The project is divided into three main stages:

1. **Sample Generation**: Create a sample dataset of original and update submissions from a chosen subreddit.
2. **Comment Extraction**: Extract and analyse comments and replies for each case, generating datasets with relevant metrics.
3. **HTML Generation**: Process all case files in the data folder to produce HTML reports summarising the findings.


## Setup

To set up the project, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/rkmaxwell2/relationship-subreddit-analyser.git
   cd relationship-subreddit-analyser
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create data directory**:
   ```bash
   mkdir data
   ```

4. **Update the client config with your API credentials**:

   The client_config.py file in the client directory contains the following variables
   ```bash
   client_id=
   client_secret=
   user_agent=
   ```
   These need to be replaced with your access secrets in order to access the reddit client via PRAW.

## Usage

1. Sample Generation
To create a sample dataset of original and update submissions, run:
   ```bash
   python scripts/1_generate_sample.py
   ```

2. Comment Extraction
To extract and analyse comments and replies for each case and generate datasets with metrics, run:
   ```bash
   python scripts/2_process_sample.py
   ```

3. HTML Generation
To process all case files and generate HTML reports summarising the findings, run:
```bash
   python scripts/3_generate_html.py
   ```
