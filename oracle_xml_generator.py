
import streamlit as st
import pandas as pd
import os
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from sqlalchemy import create_engine, text

# ------------------ DATABASE CONFIGURATION ------------------

DB_USER = "your_oracle_user"
DB_PASS = "your_oracle_password"
DB_HOST = "your_oracle_host"
DB_PORT = "1521"
DB_SERVICE = "your_oracle_service_name"  # Changed from SID to SERVICE_NAME

# DSN format using service name
dsn = f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={DB_HOST})(PORT={DB_PORT}))(CONNECT_DATA=(SERVICE_NAME={DB_SERVICE})))"
engine = create_engine(f"oracle+cx_oracle://{DB_USER}:{DB_PASS}@{dsn}")

# ------------------ STREAMLIT UI SETUP ------------------

st.set_page_config(page_title="📄 Oracle XML Generator Tool", layout="centered")
st.title("📄 Oracle-based Report XML Generator")
st.markdown("Upload the input Excel file to generate XML files for selected reports and download as ZIP.")

input_file = st.file_uploader("📥 Upload Input Excel File", type=["xlsx"])

# ------------------ CORE FUNCTION ------------------

def generate_xml_from_oracle(report, fund, date=None):
    try:
        with engine.connect() as conn:
            query = """
                SELECT * FROM report_data
                WHERE report_name = :report
                  AND fund_name = :fund
            """
            params = {'report': report, 'fund': fund}

            if date:
                query += " AND TO_DATE(run_date, 'YYYY-MM-DD') = TO_DATE(:date, 'YYYY-MM-DD')"
                params['date'] = date

            result = conn.execute(text(query), params)
            rows = result.fetchall()

            if not rows:
                return []

            columns = result.keys()
            records = [dict(zip(columns, row)) for row in rows]
            return records

    except Exception as e:
        st.error(f"❌ Error querying Oracle DB: {e}")
        return []

def parse_parameters(param_str):
    param_dict = {}
    if pd.isna(param_str):
        return param_dict

    for pair in str(param_str).split('|'):
        if '=' in pair:
            key, values = pair.split('=', 1)
            value_list = [v.strip() for v in values.split(',') if v.strip()]
            param_dict[key.strip()] = value_list
    return param_dict

def create_xml(report, fund, run_date, param_dict, row_idx):
    root = ET.Element("report")
    ET.SubElement(root, "reportName").text = report
    ET.SubElement(root, "fundName").text = fund
    ET.SubElement(root, "runDate").text = str(run_date)

    params_el = ET.SubElement(root, "parameters")

    for key, values in param_dict.items():
        for value in values:
            param_el = ET.SubElement(params_el, "parameter")
            ET.SubElement(param_el, "key").text = key
            ET.SubElement(param_el, "value").text = value

    tree = ET.ElementTree(root)
    file_io = io.BytesIO()
    tree.write(file_io, encoding='utf-8', xml_declaration=True)
    return file_io.getvalue()

# ------------------ MAIN PROCESSING ------------------

if input_file:
    df_input = pd.read_excel(input_file, engine="openpyxl")

    required_cols = {"Report", "Fund", "Run Date", "Parameters"}
    if not required_cols.issubset(df_input.columns):
        st.error(f"❌ Input Excel must contain columns: {', '.join(required_cols)}")
    else:
        with st.spinner("🔍 Processing... Please wait."):
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, row in df_input.iterrows():
                    report = row["Report"]
                    fund = row["Fund"]
                    run_date = row["Run Date"]
                    param_str = row.get("Parameters", "")
                    param_dict = parse_parameters(param_str)

                    records = generate_xml_from_oracle(report, fund, run_date)

                    if not records:
                        st.warning(f"⚠️ No data found for Report: {report}, Fund: {fund}, Date: {run_date}")
                        continue

                    for j, record in enumerate(records):
                        xml_bytes = create_xml(report, fund, run_date, param_dict, j)
                        xml_filename = f"{report}_{fund}_{str(run_date).replace(' ', '_')}_{j+1}.xml"
                        zip_file.writestr(xml_filename, xml_bytes)

            st.success("✅ XML files generated successfully.")
            st.download_button(
                label="📦 Download All XMLs as ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"report_xmls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
