#db_app.py
#run "streamlit run db_app.py"
import streamlit as st
import psycopg2
import pandas as pd

# Database connection URL
DATABASE_URL = "postgresql://findmyspot_user:dtVD7Dqn587EVoWrZAWfUsvEVsxCOK35@dpg-d2e5l249c44c73ef17j0-a.singapore-postgres.render.com:5432/findmyspot"

# Connect to database
@st.cache_resource
def init_connection():
    return psycopg2.connect(DATABASE_URL)

conn = init_connection()

# Get list of all tables in the public schema
def get_all_tables():
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return [row[0] for row in cur.fetchall()]

# Sidebar: dynamic table list
st.sidebar.header("Query Options")
table_list = get_all_tables()
table_name = st.sidebar.selectbox("Select a table to view", table_list)

# Show table content
if table_name:
    df = pd.read_sql(f'SELECT * FROM "{table_name}" LIMIT 100', conn)
    st.write(f"### Showing first 100 rows from `{table_name}`")
    st.dataframe(df)

