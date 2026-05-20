import clickhouse_connect
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == '__main__':
    try:
        # Get connection details from environment variables
        client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST'),
            user=os.getenv('CLICKHOUSE_USER'),
            password=os.getenv('CLICKHOUSE_PASSWORD'),
            secure=os.getenv('CLICKHOUSE_SECURE') == 'True'
        )
        
        # Test the connection
        result = client.query("SELECT 1 as test").result_set[0][0]
        print(f"[OK] Connection successful! Test query result: {result}")
        
        # Get ClickHouse version
        version = client.query("SELECT version()").result_set[0][0]
        print(f"[OK] ClickHouse version: {version}")
        
        # List existing databases
        databases = client.query("SHOW DATABASES").result_set
        print(f"\n[OK] Existing databases:")
        for db in databases:
            print(f"  - {db[0]}")
            
        print("\n[OK] All checks passed! ClickHouse Cloud connection is working.")
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
