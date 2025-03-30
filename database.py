import mysql.connector
import streamlit as st

_db_connected = False

def get_db_connection():
    """Connect to MySQL and return the connection and cursor."""
    global _db_connected

    required_db_configs = ["db_host", "db_port", "db_user", "db_password", "db_name"]
    missing_db_configs = [key for key in required_db_configs if not st.session_state.get(key)]

    if missing_db_configs:
        print(f"❌ Missing database configuration: {', '.join(missing_db_configs)}")
        return None, None

    try:
        conn = mysql.connector.connect(
            host=st.session_state["db_host"],
            port=int(st.session_state["db_port"]),
            user=st.session_state["db_user"],
            password=st.session_state["db_password"],
            database=st.session_state["db_name"]
        )
        cursor = conn.cursor()

        if not _db_connected:
            print("✅ Connected to MySQL successfully!")
            _db_connected = True  

        return conn, cursor
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
        return None, None

def create_table():
    """Create the 'interview_schedule' table if it does not exist."""
    conn, cursor = get_db_connection()
    if conn and cursor:
        try:
            cursor.execute("SHOW TABLES LIKE 'interview_schedule'")
            table_exists = cursor.fetchone()

            if not table_exists:
                cursor.execute("""
                    CREATE TABLE interview_schedule (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        candidate_email VARCHAR(255) NOT NULL,
                        interview_time DATETIME NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("✅ Table 'interview_schedule' is ready!")
        except mysql.connector.Error as err:
            print(f"❌ Error creating table: {err}")
        finally:
            cursor.close()
            conn.close()

def test_db_connection():
    """Test MySQL database connection."""
    try:
        conn, _ = get_db_connection()
        if conn:
            st.success("✅ Database connection successful!")
            conn.close()
        else:
            st.error("❌ Database connection failed!")
    except mysql.connector.Error as e:
        st.error(f"❌ Database connection failed: {e}")