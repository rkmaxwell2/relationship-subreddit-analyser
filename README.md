# Relationship Subreddit Analyser

## Overview

This project aims to analyze submissions on the Relationships subreddit by processing the original and update submissions. The project is divided into three main stages:

1. **Sample Generation**: Create a sample dataset of original and update submissions from a chosen subreddit. (1_generate_sample.py)
2. **Comment Extraction**: Extract and analyze comments and replies for each case, generating datasets with relevant metrics. (2_process_sample.py)
3. **JSON Generation**: Process all case files in the data folder to produce HTML reports summarizing the findings. (3_generate_html.py)


## Setup

To set up the project, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/rkmaxwell2/relationship-subreddit-analyser.git
   cd relationship-subreddit-analyser

2. **Create a virtual environment**:
python -m venv venv
source venv/bin/activate

3. **Install dependencies**:
pip install -r requirements.txt

4. **Create data directory**:
mkdir data


## Usage

1. Sample Generation
To create a sample dataset of original and update submissions, run:
python scripts/1_generate_sample.py

2. Comment Extraction
To extract and analyze comments and replies for each case and generate datasets with metrics, run:
python scripts/2_process_sample.py

File: scripts/process_data.py

3. JSON Generation
To process all case files and generate HTML reports summarizing the findings, run:
python scripts/3_generate_html.py

## Contact
For any questions or further information, please contact your-email@example.com.