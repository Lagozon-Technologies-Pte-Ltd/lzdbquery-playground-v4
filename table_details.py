import pandas as pd
import os, json
import configure
from operator import itemgetter
from langchain.chains.openai_tools import create_extraction_chain_pydantic 
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI 
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI



AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', "2024-02-01")
AZURE_DEPLOYMENT_NAME = os.environ.get('AZURE_DEPLOYMENT_NAME')

llm = AzureChatOpenAI(
    openai_api_version=AZURE_OPENAI_API_VERSION,
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    temperature=0
)

from typing import List
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

def get_table_details(selected_subject='Demo', table_name=None):
    """
    Returns details for one or more tables from a subject-specific JSON file.
    - selected_subject: base name of JSON file (without .json)
    - table_name: string or list of strings (table names to filter on)
    """
    # Build the path to the JSON file
    select_database_table_desc_json = selected_subject + ".json"
    path = os.path.join('table_files', select_database_table_desc_json)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"

    if 'tables' not in json_data:
        return "Invalid JSON format: missing 'tables' key."

    tables = json_data['tables']
    table_details = ""
    print("path for json: ", path)

    # Normalize table_name(s) for filtering
    table_names = []
    if table_name:
        if isinstance(table_name, str):
            table_names = [t.strip().lower() for t in table_name.split(';') if t.strip()]
        elif isinstance(table_name, list):
            table_names = [t.strip().lower() for t in table_name if t.strip()]
        else:
            return "Invalid table_name argument."
        filtered_tables = [t for t in tables if t['table_name'].lower() in table_names]
        if not filtered_tables:
            return f"No details found for table(s): {', '.join(table_names)}"
    else:
        filtered_tables = tables

    for table in filtered_tables:
        table_details += f"Table Name: {table['table_name']}\n"
        table_details += f"Table Description: {table['table_description']}\n"
        table_details += "Columns:\n"
        for col in table['columns']:
            col_name = col.get('column_name', '')
            data_type = col.get('data_type', '')
            nullable = col.get('nullable', False)
            description = col.get('description', '')
            table_details += f"  - {col_name} ({data_type})"
            if nullable:
                table_details += " [NULLABLE]"
            table_details += f": {description}\n"
        table_details += "\n"

    if not table_details:
        table_details = "No tables found in the JSON."
    
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
    path = f'table_files/Azure-SQL-DB.json'
    
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
