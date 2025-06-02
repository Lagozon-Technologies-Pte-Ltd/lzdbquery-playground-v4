import pandas as pd
import os, json
import configure
from operator import itemgetter
from langchain.chains.openai_tools import create_extraction_chain_pydantic 
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI 
#from  langchain_openai.chat_models import with_structured_output

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(model=configure.selected_models, temperature=0)
from typing import List
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

def get_table_details(selected_subject='Demo', table_name=None):
    """
    Returns details for one or more tables from a subject-specific CSV file.
    - selected_subject: base name of CSV file (without .csv)
    - table_name: string or list of strings (table names to filter on)
    """
    # Build the path to the CSV file
    select_database_table_desc_csv = selected_subject + ".csv"
    path = f'table_files/{select_database_table_desc_csv}'
    
    try:
        table_description = pd.read_csv(path)
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"

    table_details = ""
    print("path for csv: ", path)

    # Check if 'data_type' column exists
    has_data_type = 'data_type' in table_description.columns

    # Normalize table_name(s) for filtering
    table_names = []
    if table_name:
        if isinstance(table_name, str):
            table_names = [t.strip().lower() for t in table_name.split(';') if t.strip()]
        elif isinstance(table_name, list):
            table_names = [t.strip().lower() for t in table_name if t.strip()]
        else:
            return "Invalid table_name argument."
        filtered = table_description[table_description['table_name'].str.lower().isin(table_names)]
        if filtered.empty:
            return f"No details found for table(s): {', '.join(table_names)}"
        grouped = filtered.groupby(['table_name', 'table_description'])
    else:
        grouped = table_description.groupby(['table_name', 'table_description'])

    for (table, desc), group in grouped:
        table_details += f"Table Name: {table}\n"
        table_details += f"Table Description: {desc}\n"
        table_details += "Columns:\n"
        for i, row in group.iterrows():
            # Parse column_name&description
            col_info = row.get('column_name&description', '')
            if ':' in col_info:
                col_name, col_desc = col_info.split(':', 1)
                col_name = col_name.strip()
                col_desc = col_desc.strip()
            else:
                col_name = col_info.strip()
                col_desc = ""
            # Add data type if present
            if has_data_type:
                data_type = row['data_type']
                table_details += f"  - {col_name} ({data_type}): {col_desc}\n"
            else:
                table_details += f"  - {col_name}: {col_desc}\n"
        table_details += "\n"

    if not table_details:
        table_details = "No tables found in the CSV."
    
    return table_details
class Table(BaseModel):
    """Table in SQL database."""

    name: str = Field(description="Name of table in SQL database.")

def get_tables(tables: List[Table]) -> List[str]:
    tables  = [table.name for table in tables]
    return tables

def get_table_metadata(selected_subject='Demo'):
    """
    Returns a list of table names and their descriptions from a subject-specific JSON file.
    - selected_subject: base name of JSON file (without .json)
    """
    path = f'tables_details.json'
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"

    if 'tables' not in data or not isinstance(data['tables'], list):
        return "JSON must contain a 'tables' list."

    table_info = ""
    seen = set()
    for table in data['tables']:
        table_name = table.get('table_name')
        table_description = table.get('table_description')
        if not table_name or not table_description:
            continue
        if table_name not in seen:
            seen.add(table_name)
            table_info += f"Table Name: {table_name}\nDescription: {table_description}\n\n"

    return table_info.strip()
# table_names = "\n".join(db.get_usable_table_names())
# table_details = get_table_details()
# print("testinf details",table_details, type(table_details))
# table_details_prompt = f"""Return the names of ALL the SQL tables that MIGHT be relevant to the user question. \
#     The permissible tables names are listed below and must be strictly followed:

#     {table_details}

#     Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed."""
# table_details_set_prompt = os.getenv('TABLE_DETAILS_SET_PROMPT')
# table_details_prompt=table_details_set_prompt.format(table=table_details)
# # print("Table_details_prompt: ", table_details_prompt)
# table_chain = {"input": itemgetter("question")} | create_extraction_chain_pydantic(Table, llm, system_message=table_details_prompt) | get_tables
# mock_question_test = "How many product view by products in last week"
# table_chain_check = table_chain.invoke({"question":mock_question_test})
# print("test table chain  first mock_question  :" , mock_question_test ,"  Now tables selected:... ",table_chain_check)
