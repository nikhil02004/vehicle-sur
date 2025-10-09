#!/usr/bin/env python3
"""
Script to execute mock pollution data insertion
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv('backend/.env')

def connect_to_db():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'numberplates_speed'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

def execute_mock_data_insertion():
    """Execute the mock pollution data insertion"""
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        print("ERROR: Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        print("Step 1: Getting unique numberplates from my_data...")
        
        # Step 1: Get unique numberplates
        cursor.execute("""
            SELECT DISTINCT numberplate 
            FROM my_data 
            WHERE numberplate IS NOT NULL 
            AND numberplate != ''
            AND LENGTH(numberplate) > 2
        """)
        
        unique_plates = cursor.fetchall()
        print(f"Found {len(unique_plates)} unique numberplates")
        
        if len(unique_plates) == 0:
            print("ERROR: No valid numberplates found in my_data table")
            return False
        
        # Show first few numberplates
        print("Sample numberplates:")
        for i, (plate,) in enumerate(unique_plates[:5]):
            print(f"   {i+1}. {plate}")
        if len(unique_plates) > 5:
            print(f"   ... and {len(unique_plates) - 5} more")
        
        print("\nStep 2: Inserting mock pollution data...")
        
        # Step 2: Insert mock pollution data
        insert_query = """
            INSERT IGNORE INTO vehicle_pollution (numberplate, fuel_type, emission_rate)
            SELECT DISTINCT 
                numberplate,
                -- Assign fuel types based on numberplate patterns
                CASE 
                    WHEN numberplate LIKE '%E%' OR numberplate LIKE '%EV%' THEN 'electric'
                    WHEN numberplate LIKE '%D%' OR numberplate LIKE '%DL%' THEN 'diesel'
                    WHEN numberplate LIKE '%C%' OR numberplate LIKE '%CNG%' THEN 'CNG'
                    WHEN numberplate LIKE '%H%' OR numberplate LIKE '%HY%' THEN 'hybrid'
                    ELSE 'petrol'
                END as fuel_type,
                -- Assign emission rates based on fuel type
                CASE 
                    WHEN numberplate LIKE '%E%' OR numberplate LIKE '%EV%' THEN 0
                    WHEN numberplate LIKE '%D%' OR numberplate LIKE '%DL%' THEN 180 + (RAND() * 40)
                    WHEN numberplate LIKE '%C%' OR numberplate LIKE '%CNG%' THEN 120 + (RAND() * 30)
                    WHEN numberplate LIKE '%H%' OR numberplate LIKE '%HY%' THEN 90 + (RAND() * 30)
                    ELSE 150 + (RAND() * 50)
                END as emission_rate
            FROM my_data 
            WHERE numberplate IS NOT NULL 
            AND numberplate != ''
            AND LENGTH(numberplate) > 2
        """
        
        cursor.execute(insert_query)
        rows_inserted = cursor.rowcount
        conn.commit()
        
        print(f"SUCCESS: Inserted {rows_inserted} records into vehicle_pollution table")
        
        print("\nStep 3: Verifying insertion...")
        
        # Step 3: Verify insertion
        cursor.execute("""
            SELECT 
                fuel_type,
                COUNT(*) as vehicle_count,
                ROUND(AVG(emission_rate), 2) as avg_emission_rate,
                ROUND(MIN(emission_rate), 2) as min_emission_rate,
                ROUND(MAX(emission_rate), 2) as max_emission_rate
            FROM vehicle_pollution
            GROUP BY fuel_type
            ORDER BY vehicle_count DESC
        """)
        
        summary = cursor.fetchall()
        
        print("Fuel Type Distribution:")
        print("=" * 80)
        print(f"{'Fuel Type':<12} {'Count':<8} {'Avg Emission':<12} {'Min':<8} {'Max':<8}")
        print("=" * 80)
        
        for fuel_type, count, avg_rate, min_rate, max_rate in summary:
            print(f"{fuel_type:<12} {count:<8} {avg_rate:<12} {min_rate:<8} {max_rate:<8}")
        
        print("\nStep 4: Sample inserted data:")
        cursor.execute("SELECT * FROM vehicle_pollution LIMIT 10")
        samples = cursor.fetchall()
        
        print("=" * 60)
        print(f"{'ID':<5} {'Numberplate':<15} {'Fuel Type':<10} {'Emission Rate':<12}")
        print("=" * 60)
        
        for record in samples:
            id_val, plate, fuel, emission = record
            print(f"{id_val:<5} {plate:<15} {fuel:<10} {emission:<12.2f}")
        
        print(f"\nSUCCESS: Mock pollution data insertion completed!")
        print(f"Total records processed: {len(unique_plates)}")
        print(f"Total records inserted: {rows_inserted}")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"ERROR: Database error: {err}")
        conn.rollback()
        return False
    except Exception as err:
        print(f"ERROR: Unexpected error: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Starting mock pollution data insertion...")
    print("=" * 60)
    
    success = execute_mock_data_insertion()
    
    print("=" * 60)
    if success:
        print("SUCCESS: Script completed successfully!")
    else:
        print("ERROR: Script failed. Please check the error messages above.")