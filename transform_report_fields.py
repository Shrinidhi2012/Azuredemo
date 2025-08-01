import pandas as pd

df = pd.read_excel("your_input_file.xlsx")

report_col = 'Report'
field_cols = [col for col in df.columns if col not in ['Path', report_col]]

output_rows = []
pk = 1

for _, row in df.iterrows():
    report_name = row[report_col]
    for col in field_cols:
        value = str(row[col]).strip().lower()
        if value in ['a', 'ab', 'b']:
            table_field = col.replace('_', '.', 1)
            output_rows.append([pk, report_name, table_field, value])
            pk += 1

output_df = pd.DataFrame(output_rows, columns=['ID', 'Report Name', 'Field Name', 'Marker'])

output_df.to_csv("transformed_report_fields.csv", index=False)
