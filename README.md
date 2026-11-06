# 🌾 AgriData Explorer: Understanding Indian Agriculture with EDA

A data analysis and visualization project that explores **crop production, yield and area under cultivation** across Indian states and districts, combining a full data pipeline (cleaning, EDA, SQL) with an interactive Power BI report and a Streamlit dashboard.

The application is built with **Python and Streamlit** and gives farmers, policymakers and researchers a simple way to explore 50+ years of agricultural data, compare crops and regions, and see how trends have changed over time.

## 🚀 Live Demo

**Streamlit App:** _add your Streamlit link here after deploying_

## 📌 Project Overview

India's agricultural data is complex, fragmented and hard to access, which makes it difficult to make informed decisions. The **AgriData Explorer** project brings district-level data from **20 states and 311 districts (1966–2017)** into one place, so that trends, gaps and regional differences are easy to identify.

The project covers the complete pipeline:

* 🧹 Data Cleaning & Standardization (Python)
* 📊 Exploratory Data Analysis (15 analyses)
* 🗄️ SQL Analysis in MySQL (10 business questions)
* 📈 Interactive Power BI Report
* 🖥️ Streamlit Dashboard with Year and State Filters

## 👥 Who It Helps

| Audience | How the project helps |
| -------- | --------------------- |
| **Farmers** | See how crops have performed over time and where regional productivity can improve |
| **Policymakers** | Find low-productivity regions and crops with fluctuating yields, to plan subsidies and crop insurance |
| **Researchers** | Study agricultural trends and spot areas for innovation |

## ✨ Features

* User-friendly Streamlit interface with left sidebar navigation
* **All Crops** page with total production and area, crop comparison, crop-group trends and a land-use treemap
* **Crop Explorer** page to view one crop at a time by production, area or yield
* **EDA** page showing all 15 exploratory analyses in one scrolling page
* **SQL Questions** page showing all 10 business questions with charts and result tables
* Year-range slider pinned at the top of every page, filtering all analyses
* State filter for the All Crops and Crop Explorer pages
* Yield calculated as total production ÷ total area, never as an average of yields
* SQL results verified against the original MySQL queries
* Power BI report included for download

## 📊 Analyses Included

### Exploratory Data Analysis (`2_EDA.ipynb`)

* Top rice, wheat, sunflower and groundnut producing states
* Wheat production share among the top 5 states
* Oilseed production in major states
* Sugarcane, millet, and rice vs wheat production over 50+ years
* Rice production by West Bengal districts, and top wheat years in Uttar Pradesh
* Sorghum production (Kharif and Rabi) by state
* Soybean production and yield efficiency
* Impact of area on production (rice, wheat, maize)
* Rice vs wheat yield across states

### SQL Business Questions (`3_SQL.ipynb`)

1. Year-wise trend of rice production across the top 3 states
2. Top 5 districts by wheat yield increase over the last 5 years
3. States with the highest growth in oilseed production (5-year growth rate)
4. District-wise correlation between area and production (rice, wheat, maize)
5. Yearly production growth of cotton in the top 5 cotton-producing states
6. Districts with the highest groundnut production in the latest year
7. Annual average maize yield across all states
8. Total area cultivated for oilseeds in each state
9. Districts with the highest rice yield
10. Wheat vs rice production for the top 5 states over 10 years

### Files Included

| Component | File |
| --------- | ---- |
| Cleaned Dataset | `data/clean_agri_data.xlsx` |
| Power BI Report | `powerbi/Indian Agriculture Analysis.pbix` |

## 🔄 Project Workflow

The general workflow followed in the project is:

```text
Raw ICRISAT District-Level Dataset
   ↓
Data Cleaning & Standardization
   ↓
Exploratory Data Analysis (EDA)
   ↓
SQL Analysis (MySQL)
   ↓
Power BI Report
   ↓
Streamlit Dashboard
   ↓
Streamlit Community Cloud Deployment
```

## 🗃️ Dataset

The data comes from **ICRISAT district-level data** for India: 16,146 rows covering 311 districts in 20 states from 1966 to 2017.

| Measure | Unit |
| ------- | ---- |
| Area | 1000 hectares |
| Production | 1000 tons |
| Yield | kg per hectare |

It includes cereals (rice, wheat, maize, sorghum, millets, barley), pulses, oilseeds, sugarcane and cotton, plus area-only data for fruits, vegetables, potatoes, onion and fodder.

## 🛠️ Technologies Used

### Programming

* Python
* SQL

### Data Science

* Pandas
* NumPy

### Visualization

* Plotly
* Matplotlib
* Seaborn
* Power BI

### Database

* MySQL (`mysql-connector-python`)

### Deployment

* Streamlit
* OpenPyXL (reading the Excel dataset)

### Development Tools

* Jupyter Notebook
* VS Code
* GitHub

## 📂 Project Structure

```text
AgriData-Explorer/
│
├── 1_data_cleaning.ipynb
├── 2_EDA.ipynb
├── 3_SQL.ipynb
│
├── app.py
│
├── data/
│   └── clean_agri_data.xlsx
│
├── powerbi/
│   └── Indian Agriculture Analysis.pbix
│
├── .streamlit/
│   └── config.toml
│
├── requirements.txt
├── .env.example
├── .gitignore
│
└── README.md
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repository-name.git
```

### 2. Navigate to the project directory

```bash
cd your-repository-name
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Mac/Linux:**

```bash
source .venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Streamlit application

```bash
streamlit run app.py
```

The application will open in your browser.

## 📦 Requirements

The `requirements.txt` for the Streamlit app:

```text
streamlit>=1.50
pandas>=2.0
plotly>=5.20
openpyxl>=3.1
```

To run the notebooks as well, also install:

```text
jupyter
numpy
matplotlib
seaborn
mysql-connector-python
```

## 🗄️ Running the SQL Notebook

`3_SQL.ipynb` connects to a local MySQL database named `indian_agriculture`. The password is never stored in the notebook:

1. Copy `.env.example` to `.env` and fill in your password (this file is ignored by Git and must never be uploaded):

```text
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_HOST=localhost
MYSQL_DATABASE=indian_agriculture
```

2. The notebook reads `MYSQL_PASSWORD` from the environment, or asks for it when you run the connection cell.

A hosted app cannot reach a local database, so the SQL page in the Streamlit app recomputes each query's result with pandas, using the same logic as the SQL.

## 🌐 Deployment

The application can be deployed using **Streamlit Community Cloud**.

Basic deployment steps:

1. Push the project to GitHub (do not upload the `.env` file).
2. Open Streamlit Community Cloud.
3. Connect your GitHub account.
4. Select this repository.
5. Select `app.py` as the main file.
6. Deploy the application.

The Power BI report cannot be embedded in the app (it needs a paid account to publish), so the `.pbix` file is included in the repository to open with Power BI Desktop.

## ⚠️ Disclaimer

This project is intended **for educational and demonstration purposes only**.

The data ends in 2017, so all figures describe historical trends and should not be treated as current. A few data-handling choices are documented in the notebooks and the app rather than hidden:

* The source marks missing values as `-1`, which are replaced with 0 during cleaning.
* The source `OILSEEDS` column is mostly 0 from 2016 onward, so oilseed figures are rebuilt from their 8 component crops.
* Combined production in tons mixes sugarcane (raw cane weight) with grains, so cropped area is the fairer combined comparison.

Results are **illustrative, not authoritative**, and should not be used as the sole basis for real-world agricultural or policy decisions.

## 👨‍💻 Author

Yoga Prabhu

Data Science | Machine Learning | Python

Portfolio: https://sybersage.github.io/Portfolio/

GitHub: https://github.com/sybersage

LinkedIn: https://www.linkedin.com/in/yoga-prabhu

---

⭐ If you found this project useful, consider giving the repository a star!
