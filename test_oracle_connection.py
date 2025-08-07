import oracledb

# Replace with your actual credentials
username = "your_username"
password = "your_password"
dsn = "your_host:your_port/your_service_name"  # e.g., "localhost:1521/XEPDB1"

try:
    # Connect to Oracle DB
    connection = oracledb.connect(user=username, password=password, dsn=dsn)
    print("✅ Connection to Oracle DB was successful!")

    # Optional: get Oracle version
    print("Oracle DB version:", connection.version)

    # Close connection
    connection.close()

except oracledb.Error as error:
    print("❌ Error connecting to Oracle DB:", error)
