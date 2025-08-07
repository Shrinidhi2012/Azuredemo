import streamlit as st
import pandas as pd
import io
import zipfile
import re
import oracledb
from datetime import datetime

st.set_page_config(page_title="XML Generator Tool", layout="centered")
st.title("📄 Report XML Generator")

st.markdown("Upload the input Excel file and click the button to generate XML files in a ZIP archive.")

# Upload Input File
input_file = st.file_uploader("Upload Input Excel File", type=["xlsx"])

# Initialize Oracle client and connection (replace with actual credentials)
oracledb.init_oracle_client()
connection = oracledb.connect(user="your_user", password="your_password", dsn="your_host/your_service")

if input_file:
    input_df = pd.read_excel(input_file)

    cursor = connection.cursor()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for _, row in input_df.iterrows():
            input_report = str(row['report']).strip()
            input_fund = str(row['fund']).strip()
            input_date = row.get('date', None)

            # SQL QUERY
            query = """
                SELECT *
                FROM KIRA_STAR.REPORT_STATISTICS
                WHERE LOWER(RS_ENGINE) = 'actuate'
                  AND LOWER(RS_STATUS) = 'succeeded'
                  AND LOWER(RS_REPORT) LIKE :report_pattern
                  AND REGEXP_LIKE(RS_PARAMETERS, :fund_regex, 'i')
            """

            fund_pattern = f"pFondsMulti\s*:\s*[^;]*{re.escape(input_fund)}[^;]*"

            cursor.execute(query, {
                "report_pattern": f"%{input_report.lower()}%",
                "fund_regex": fund_pattern
            })

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            db_filtered = pd.DataFrame(rows, columns=columns)

            if not db_filtered.empty:
                db_filtered['RSDateTime'] = pd.to_datetime(db_filtered['RS_START'], errors='coerce')

                if pd.notna(input_date):
                    input_dt = pd.to_datetime(input_date, errors='coerce')
                    db_filtered = db_filtered[db_filtered['RSDateTime'].dt.date == input_dt.date()]
                else:
                    latest_datetime = db_filtered['RSDateTime'].max()
                    db_filtered = db_filtered[db_filtered['RSDateTime'].dt.date == latest_datetime.date()]

                db_filtered = db_filtered.sort_values(by='RSDateTime', ascending=False).reset_index(drop=True)

                for idx, matched_row in db_filtered.iterrows():
                    report_path = matched_row['RS_REPORT']
                    xml_path = "/".join(report_path.split("/")[:-1])

                    param_string = matched_row['RS_PARAMETERS']
                    parameters = [p.strip() for p in param_string.split(';') if ':' in p]
                    xml_params = ""

                    for p in parameters:
                        key, val = map(str.strip, p.split(':', 1))
                        if key.lower() == "pfondsmulti":
                            val = val.replace(",", "|")
                        xml_params += f'    <parameter name="{key}">\n        <value>{val}</value>\n    </parameter>\n'

                    report_format = matched_row['RS_FORMAT']
                    xml_content = (
                        '<?xml version="1.0" encoding="UTF-8"?>\n'
                        f'<reportTestcase name="{input_report}" format="{report_format}" pfad="{xml_path.rsplit(input_report,1)[0]}">\n'
                        f'{xml_params}'
                        '</reportTestcase>'
                    )

                    date_str = matched_row['RSDateTime'].strftime("%Y-%m-%d_%H-%M")
                    filename = f"{input_report}_{input_fund}_{date_str}_#{idx+1}.xml"

                    zipf.writestr(filename, xml_content)

    st.success("✅ XMLs generated!")
    st.download_button(
        label="📦 Download All XMLs as ZIP",
        data=zip_buffer.getvalue(),
        file_name="generated_xmls.zip",
        mime="application/zip"
    )

    cursor.close()
    connection.close()
