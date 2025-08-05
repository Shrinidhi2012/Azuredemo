
import pandas as pd

# --- CONFIGURATION ---
csv_file = "your_input_file.csv"  # Replace with your CSV file path
report_col = "report"             # The column name for report names

# --- STEP 1: Read CSV ---
df = pd.read_csv(csv_file)

# --- STEP 2: Identify field columns ---
field_cols = [col for col in df.columns if col.lower() not in ['path', report_col.lower()]]

# --- STEP 3: Transform ---
output_rows = []
pk = 1

for _, row in df.iterrows():
    report_name = row[report_col]
    for col in field_cols:
        val = str(row[col]).strip().lower()
        if val in ['a', 'ab', 'b']:
            table_field = col.replace('_', '.', 1)
            output_rows.append([pk, report_name, table_field, val])
            pk += 1

# --- STEP 4: Create final cleaned DataFrame ---
clean_df = pd.DataFrame(output_rows, columns=["ID", "Report Name", "Field Name", "Marker"])

# --- STEP 5: Export (optional) ---
clean_df.to_csv("cleaned_report_fields.csv", index=False)

# --- STEP 6: Show (for quick view) ---
print(clean_df)
