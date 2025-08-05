
import streamlit as st
import pandas as pd
import io

# Set Streamlit page config
st.set_page_config(page_title="Report Field Extractor", layout="centered")
st.title("📄 Report to DVH Field Extractor")

st.markdown("""
Upload a CSV file where:
- The **first column** is `report` (report names)
- All other columns are **data warehouse fields**
- Only cells with values `S`, `SF`, or `F` will be kept

This tool will convert the wide CSV format into a clean 3-column table:
1. Report Name
2. Data Warehouse Field
3. Marker (S / SF / F)
""")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    try:
        # Read uploaded CSV
        df = pd.read_csv(uploaded_file)

        if df.columns[0].lower() != 'report':
            st.error("❌ The first column must be 'report'.")
        else:
            report_col = df.columns[0]
            field_cols = df.columns[1:]  # Skip the 'report' column

            # Prepare the cleaned output
            cleaned_rows = []
            for _, row in df.iterrows():
                report_name = row[report_col]
                for col in field_cols:
                    value = str(row[col]).strip().upper()
                    if value in ['S', 'SF', 'F']:
                        cleaned_rows.append([report_name, col, value])

            cleaned_df = pd.DataFrame(cleaned_rows, columns=["Report Name", "DVH Field", "Marker"])

            if not cleaned_df.empty:
                st.success(f"✅ Extracted {len(cleaned_df)} valid rows.")

                st.dataframe(cleaned_df.head(50))

                # Download button
                csv_output = cleaned_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Cleaned CSV",
                    data=csv_output,
                    file_name="cleaned_report_fields.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No valid 'S', 'SF', or 'F' values found in the uploaded file.")

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
