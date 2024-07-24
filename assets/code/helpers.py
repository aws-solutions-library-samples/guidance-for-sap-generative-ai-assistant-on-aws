#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import boto3
import time
import logging
import json
import pprint
import os
import config
from io import BytesIO


from langchain.agents.tools import Tool
from langchain.agents.conversational.base import ConversationalAgent
from langchain.agents import AgentExecutor
from datetime import datetime

import sqlalchemy
from sqlalchemy import create_engine

from langchain.docstore.document import Document
from langchain import PromptTemplate,SagemakerEndpoint,SQLDatabase,LLMChain#,SQLDatabaseChain
from langchain.chains.sql_database.base import SQLDatabaseChain #20240222 change
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.llms import bedrock
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts.prompt import PromptTemplate

from langchain.chains.api.prompt import API_RESPONSE_PROMPT
from langchain.chains import APIChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatAnthropic
from langchain.chains.api import open_meteo_docs
from typing import Dict
from typing import List


logger = logging.getLogger()
logger.setLevel(logging.INFO)


connathena=f"athena.us-east-1.amazonaws.com"#Update, if region is different
portathena='443' #Update, if port is different
schemaathena='SCHEMANAME'#'cfn_covid_lake' #glue_database_name #from cfn params
s3stagingathena=f's3://sap-analytics-glue-databucket/athenaresults/'#from cfn params
wkgrpathena='primary'#Update, if workgroup is different
connection_string = f"awsathena+rest://@{connathena}:{portathena}/{schemaathena}?s3_staging_dir={s3stagingathena}/&work_group={wkgrpathena}"
print("connection_string: ",connection_string)
engine_athena = create_engine(connection_string, echo=False)
dbathena = SQLDatabase(engine_athena)
gdc = [schemaathena]


def parse_catalog():
    columns_str=''
    
    #define glue cient
    glue_client = boto3.client('glue')
    
    for db in gdc:
        response = glue_client.get_tables(DatabaseName =db)
        for tables in response['TableList']:
            if tables['StorageDescriptor']['Location'].startswith('s3'):  classification='s3' 
            else:  classification = tables['Parameters']['classification']
            for columns in tables['StorageDescriptor']['Columns']:
                    dbname,tblname,colname=tables['DatabaseName'],tables['Name'],columns['Name']
                    columns_str=columns_str+f'\n schema name: {dbname}, table name: {tblname}, column name: {colname}'

    return columns_str



boto3_bedrock = boto3.client('bedrock-runtime')


#define a function that infers the channel/database/table and sets the database for querying
def run_query(query,glue_catalog,dialect,connectionId):
    channel='db'
    db=dbathena
    model_parameter = {"temperature": 0, "max_tokens_to_sample": 4000}
    llm = bedrock.Bedrock(model_id="anthropic.claude-v2:1", client=boto3_bedrock, model_kwargs=model_parameter, region_name="us-east-1")

    
    prompt_template = """\n\nHuman:
     From the table below, find the database (in column database) which will contain the data (in corresponding column_names) to answer the question 
     {query} \n
     """+glue_catalog +""" 
     Only provide answers in following format without any other text, preamble or additional text:
     database.table == 
     database.table.column == \n\nAssistant:
     """
    ##define prompt 1
    PROMPT_channel = PromptTemplate( template=prompt_template, input_variables=["query"]  )

    # define llm chain
    llm_chain = LLMChain(prompt=PROMPT_channel, llm=llm)
    #run the query and save to generated texts
    generated_texts = llm_chain.run(query)
    print("generated_texts_jr: ",generated_texts)

    
    QUERY1 = """\n\nHuman: Given an input question, first create a syntactically correct {dialect} query to run based on the question useing only following tables:\n
     """+generated_texts +""" 
    then look at the results of the query and return the answer like a human. Do not provide any information about SQL
    Question:\n
     """+query +"""\n\nAssistant:"""

    db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, verbose=True)
    context=db_chain.run(QUERY1)
    
    return context


def simple_orchestrator(question, sessionId):
    
    glue_catalog = parse_catalog()
    dialect = 'athena sql'
    context =  run_query(question,glue_catalog,dialect,sessionId )    

    print("context: ", context)
    return context 
