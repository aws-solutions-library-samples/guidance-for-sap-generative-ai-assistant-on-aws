# Guidance to create Generative AI Assistant for SAP Data

## Table of Contents (required)

1. [Overview](#overview)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites-required)
    - [Operating System](#operating-system-required)
3. [Deployment Steps](#deployment-steps-required)
4. [Deployment Validation](#deployment-validation-required)
5. [Running the Guidance](#running-the-guidance-required)
6. [Next Steps](#next-steps-required)
7. [Cleanup](#cleanup-required)

### Required

## Overview

SAP business users across every industry manually analyze data, write executive summaries, and perform repetitive tasks. SAP Business User Productivity solutions on AWS improve productivity by querying business data in natural language, making it easy to query, removing the need to understand SAP data structures, navigate complex reports and remember SAP transaction codes. With the use of natural language, personas like C-Suite executives, managers, auditors and on-the-go users can effortlessly gain valuable insights, retrieve summaries, or perform ad-hoc tasks such as e-mail generation and status checks.
This Guidance demonstrates how to improve business user productivity and experience using real-time data summaries, task automation, seamless natural language interactions. It uses Amazon Bedrock for generative AI and Amazon Lex for conversational AI assistant. This Guidance is designed to be extensible, allowing you to seamlessly incorporate additional components or integrate with other AWS services

Below is the reference architecture for Generative AI assistance: 

### Cost

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.


|AWS service	|Dimensions	|Cost [USD]	|
|---	|---	|---	|
|Amazon Lex	|	|	|
|AWS Lambda	|	|	|
|Amazon Athena	|	|	|
|Amazon Bedrock	|	|	|
|Amazon S3	|	|	|
|AWS Glue	|	|	|
|	|	|	|

## Prerequisites

Access to set-up AWS services: Amazon Lex, AWS lambda, Amazon Athena, Amazon Bedrock, Amazon S3 and AWS Glue from AWS Console
Amazon S3 bucket is created to store SAP data.
SAP source data is extracted in Amazon S3 bucket. The source data can be extracted using different approaches highlighted in the [Guidance for SAP Data Integration and Management on AWS](https://aws.amazon.com/solutions/guidance/sap-data-integration-and-management-on-aws/?did=sl_card&trk=sl_card).
Please take note of s3 path where data is stored example: s3://amazonjr-covid-glue-databucket/athenaresults/



## Deployment Steps



1. **Creation of glue database catalogue**

For data stored in Amazon S3, use AWS Glue crawler to create dabase catalogue. Follow the instruction as per the [blog](https://aws.amazon.com/blogs/big-data/introducing-aws-glue-crawlers-using-aws-lake-formation-permission-management/). 
You can schedule recreation of database catalogue to update database catalogue

Please make sure you are able to query the data using Amazon Athena
Please take note of: DATABASENAME and SCHEMANAME.

1. **Creating access for Amazon Bedrock**

Go to Amazon Bedrock — Model Access — Modify Model Access and select Claude:
Click Next and click submit.
It may take few minutes for access for model to get updated.
Once updated, you will able to access the Model.


1. **AWS Lambda Layer Creation**

Create S3 bucket : YOURSLAMBDALAYERS3 in your AWS Account.
Download following lambda layers to S3 bucket of your account.
langchainlayer
store it in s3 as: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip

Download following lambda layers to S3 bucket of your account.
pyAthena
store it in s3 as: s3://YOURSLAMBDALAYERS3/pyAthena/python.zip

Download following lambda layers to S3 bucket of your account.
SQLAlchemy
store it in s3 as: s3://YOURSLAMBDALAYERS3/SQLAlchemy/python.zip

1. Navigate to [AWS Lambda - Layers](https://console.aws.amazon.com/lambda/#/layers), then click **Create layer**
2. Type the following in to the Lambda Layer screen, then click **Create**
3.Name: langchainlayer
4. Description: langchainlayer
5. Choose: **Upload a file from Amazon S3: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip**
6. Compatible architectures: **x86_64**
7. Compatible runtimes: **Python 3.10**
Amazon S3 link URL: **s3://sagemaker-us-west-2-AWSAccountNumber/lambda_layer/python.zip**


Repeat above steps 1-7 for pyAthena and  SQLAlchemy



1. **Create Lambda Function**



* Navigate to [AWS Lambda - Functions](https://console.aws.amazon.com/lambda/#/functions), then click **Create function**
* Type the following information, then click **Create function**
* Select **Author from scratch**
* Function Name: SAPGenAIAssitant
* Runtime: **Python 3.10**
* Architectures: **x86_64**


Create  helpers.py file in Code source:

Copy paste the code below to **helpers.py**
Please change the athena connection parameters based on your AWS account configuration


```
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
```


Copy paste the code below to **lambda_fuction.py**, then click **Deploy**


```
#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import logging
import json
import helpers
import config
import boto3
import sqlalchemy
import os
from sqlalchemy import create_engine

from langchain.docstore.document import Document
from langchain import PromptTemplate,SagemakerEndpoint,SQLDatabase,LLMChain #,SQLDatabaseChain,
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts.prompt import PromptTemplate
#from langchain.chains import SQLDatabaseSequentialChain

from langchain.chains.api.prompt import API_RESPONSE_PROMPT
from langchain.chains import APIChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models import ChatAnthropic
from langchain.chains.api import open_meteo_docs
from typing import Dict
from typing import List


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    print("intent_request: ", intent_request)
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']
    return {}

def lambda_handler(event, context):
    logger.info('<help_desk_bot>> Lex event info = ' + json.dumps(event))

    session_attributes = get_session_attributes(event)

    logger.debug('<<help_desk_bot> lambda_handler: session_attributes = ' + json.dumps(session_attributes))
    
    currentIntent = event['sessionState']['intent']['name']
    
    if currentIntent is None:
        response_string = 'Sorry, I didn\'t understand.'
        return helpers.close(session_attributes,currentIntent, 'Fulfilled', {'contentType': 'PlainText','content': response_string})
    intentName = currentIntent
    if intentName is None:
        response_string = 'Sorry, I didn\'t understand.'
        return helpers.close(session_attributes,intentName, 'Fulfilled', {'contentType': 'PlainText','content': response_string})

    # see HANDLERS dict at bottom
    if HANDLERS.get(intentName, False):
        return HANDLERS[intentName]['handler'](event, session_attributes)   # dispatch to the event handler
    else:
        response_string = "The intent " + intentName + " is not yet supported."
        return helpers.close(session_attributes,intentName, 'Fulfilled', {'contentType': 'PlainText','content': response_string})

def hello_intent_handler(intent_request, session_attributes):
    # clear out session attributes to start new
    session_attributes = {}

    response_string = "Hello! How can we help you today?"
    return helpers.close(intent_request,session_attributes, 'Fulfilled', {'contentType': 'PlainText','content': response_string})   

def fallback_intent_handler(intent_request, session_attributes):

    sessionId = intent_request['sessionId']
    print("sessionId: ", sessionId)

    query_string = ""
    #if intent_request.get('inputTranscript', None) is not None:
    query_string += intent_request['transcriptions'][0]['transcription']

    logger.debug('<<help_desk_bot>> fallback_intent_handler(): calling get_kendra_answer(query="%s")', query_string)
    print("query_string: ", query_string)   
    helper_response = helpers.simple_orchestrator(query_string, sessionId)
    print("helper_response: ", helper_response)
    if helper_response is None:
        response = "Sorry, I was not able to understand your question."
        return helpers.close(intent_request,session_attributes,'Fulfilled', {'contentType': 'PlainText','content': response})
    else:
        logger.debug('<<help_desk_bot>> "fallback_intent_handler(): helper_response = %s', helper_response)
        #return helpers.close(intent_request,session_attributes, 'Fulfilled', {'contentType': 'PlainText','content': helper_response})
        #return_intent = helpers.close(intent_request,session_attributes, 'Fulfilled', {'contentType': 'CustomPayload','content': helper_response})
        #print("return_intent_jr: ", return_intent)
        return helpers.close(intent_request,session_attributes, 'Fulfilled', {'contentType': 'CustomPayload','content': helper_response})


    

# list of intent handler functions for the dispatch proccess
HANDLERS = {
    'greeting_intent':              {'handler': hello_intent_handler},
    'FallbackIntent':           {'handler': fallback_intent_handler}
}
```



1. Click **Layers**
2. Click **Add a layer**
3. Type the following information, then click **Add**

* Layer source: **Custom layers**
* Custom layers: **LangChainLayer**
* Version: **Choose the Latest**

Repeat above steps to add layers for **pyAthena** and **SQLAlchemy**


1. Go to **Configuration - General Configuration**, then click **Edit**
2. Change timeout from 3 seconds to **10 minutes**, then click **Save**



1. Go to **Configuration - Permissions**, then click at the role name **SAPGenAIAssistant-role-xxxxxxx**


1. Click **Add permissions**, click dropdown **Create inline policy**
2. Click **JSON**, then copy paste the below to **Policy editor**, then click **Next**



```
123456789101112131415{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Statement2",
            "Effect": "Allow",
            "Action": [
                "bedrock:*"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "Statement3",
            "Effect": "Allow",
            "Action": [
                "athena:*"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "Statement4",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "Statement5",
            "Effect": "Allow",
            "Action": [
                "glue:GetDatabase",
                "glue:GetTable",
                 "glue:GetDatabases",
                "glue:GetTables"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
    
}
```



    1. Type **SAPGenAIPolicy** as policy name then Click **Create policy**



1. **Create Amazon Lex Bot**

1.Navigate to [Amazon Lex](https://us-east-1.console.aws.amazon.com/lexv2/home?region=us-east-1)
2.Click Create bot
3.Choose create blank bot and Provide Bot name and configurations and click Next:

Select language as English and click Done to create Bot.

4.Provide name to NewIntent as greeting_intent and update description “this is hello intent” 

Proivde at least one utterance as “hi” and save intent


1. Navigate to Versions >Version: Draft>All languages>Language: English (US)>Intents
2. Click on FallbackIntent and Activate Fulfillment and click Save Intent and Click Build:


1. Click on Test
2. Select Lambda function created and select $Latest and save:


Type questions to test the response:


1. **Create Strimlit App for Lex**

Follow [aws-lex-web-ui](https://github.com/aws-samples/aws-lex-web-ui)  guidance to create strimlit App 



## Running the Guidance



## Next Steps



## Cleanup



## FAQ



## Authors




----





***Optional***

8. [FAQ, known issues, additional considerations, and limitations](#faq-known-issues-additional-considerations-and-limitations-optional)
9. [Revisions](#revisions-optional)
10. [Notices](#notices-optional)
11. [Authors](#authors-optional)

## Overview (required)

1. Provide a brief overview explaining the what, why, or how of your Guidance. You can answer any one of the following to help you write this:

    - **Why did you build this Guidance?**
    - **What problem does this Guidance solve?**

2. Include the architecture diagram image, as well as the steps explaining the high-level overview and flow of the architecture. 
    - To add a screenshot, create an ‘assets/images’ folder in your repository and upload your screenshot to it. Then, using the relative file path, add it to your README. 

### Cost ( required )

This section is for a high-level cost estimate. Think of a likely straightforward scenario with reasonable assumptions based on the problem the Guidance is trying to solve. Provide an in-depth cost breakdown table in this section below ( you should use AWS Pricing Calculator to generate cost breakdown ).

Start this section with the following boilerplate text:

_You are responsible for the cost of the AWS services used while running this Guidance. As of <month> <year>, the cost for running this Guidance with the default settings in the <Default AWS Region (Most likely will be US East (N. Virginia)) > is approximately $<n.nn> per month for processing ( <nnnnn> records )._

Replace this amount with the approximate cost for running your Guidance in the default Region. This estimate should be per month and for processing/serving resonable number of requests/entities.

Suggest you keep this boilerplate text:
_We recommend creating a [Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) through [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this Guidance._

### Sample Cost Table ( required )

**Note : Once you have created a sample cost table using AWS Pricing Calculator, copy the cost breakdown to below table and upload a PDF of the cost estimation on BuilderSpace. Do not add the link to the pricing calculator in the ReadMe.**

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.

| AWS service  | Dimensions | Cost [USD] |
| ----------- | ------------ | ------------ |
| Amazon API Gateway | 1,000,000 REST API calls per month  | $ 3.50month |
| Amazon Cognito | 1,000 active users per month without advanced security feature | $ 0.00 |

## Prerequisites (required)

### Operating System (required)

- Talk about the base Operating System (OS) and environment that can be used to run or deploy this Guidance, such as *Mac, Linux, or Windows*. Include all installable packages or modules required for the deployment. 
- By default, assume Amazon Linux 2/Amazon Linux 2023 AMI as the base environment. All packages that are not available by default in AMI must be listed out.  Include the specific version number of the package or module.

**Example:**
“These deployment instructions are optimized to best work on **<Amazon Linux 2 AMI>**.  Deployment in another OS may require additional steps.”

- Include install commands for packages, if applicable.


### Third-party tools (If applicable)

*List any installable third-party tools required for deployment.*


### AWS account requirements (If applicable)

*List out pre-requisites required on the AWS account if applicable, this includes enabling AWS regions, requiring ACM certificate.*

**Example:** “This deployment requires you have public ACM certificate available in your AWS account”

**Example resources:**
- ACM certificate 
- DNS record
- S3 bucket
- VPC
- IAM role with specific permissions
- Enabling a Region or service etc.


### aws cdk bootstrap (if sample code has aws-cdk)

<If using aws-cdk, include steps for account bootstrap for new cdk users.>

**Example blurb:** “This Guidance uses aws-cdk. If you are using aws-cdk for first time, please perform the below bootstrapping....”

### Service limits  (if applicable)

<Talk about any critical service limits that affect the regular functioning of the Guidance. If the Guidance requires service limit increase, include the service name, limit name and link to the service quotas page.>

### Supported Regions (if applicable)

<If the Guidance is built for specific AWS Regions, or if the services used in the Guidance do not support all Regions, please specify the Region this Guidance is best suited for>


## Deployment Steps (required)

Deployment steps must be numbered, comprehensive, and usable to customers at any level of AWS expertise. The steps must include the precise commands to run, and describe the action it performs.

* All steps must be numbered.
* If the step requires manual actions from the AWS console, include a screenshot if possible.
* The steps must start with the following command to clone the repo. ```git clone xxxxxxx```
* If applicable, provide instructions to create the Python virtual environment, and installing the packages using ```requirement.txt```.
* If applicable, provide instructions to capture the deployed resource ARN or ID using the CLI command (recommended), or console action.

 
**Example:**

1. Clone the repo using command ```git clone xxxxxxxxxx```
2. cd to the repo folder ```cd <repo-name>```
3. Install packages in requirements using command ```pip install requirement.txt```
4. Edit content of **file-name** and replace **s3-bucket** with the bucket name in your account.
5. Run this command to deploy the stack ```cdk deploy``` 
6. Capture the domain name created by running this CLI command ```aws apigateway ............```



## Deployment Validation  (required)

<Provide steps to validate a successful deployment, such as terminal output, verifying that the resource is created, status of the CloudFormation template, etc.>


**Examples:**

* Open CloudFormation console and verify the status of the template with the name starting with xxxxxx.
* If deployment is successful, you should see an active database instance with the name starting with <xxxxx> in        the RDS console.
*  Run the following CLI command to validate the deployment: ```aws cloudformation describe xxxxxxxxxxxxx```



## Running the Guidance (required)

<Provide instructions to run the Guidance with the sample data or input provided, and interpret the output received.> 

This section should include:

* Guidance inputs
* Commands to run
* Expected output (provide screenshot if possible)
* Output description



## Next Steps (required)

Provide suggestions and recommendations about how customers can modify the parameters and the components of the Guidance to further enhance it according to their requirements.


## Cleanup (required)

- Include detailed instructions, commands, and console actions to delete the deployed Guidance.
- If the Guidance requires manual deletion of resources, such as the content of an S3 bucket, please specify.



## FAQ, known issues, additional considerations, and limitations (optional)


**Known issues (optional)**

<If there are common known issues, or errors that can occur during the Guidance deployment, describe the issue and resolution steps here>


**Additional considerations (if applicable)**

<Include considerations the customer must know while using the Guidance, such as anti-patterns, or billing considerations.>

**Examples:**

- “This Guidance creates a public AWS bucket required for the use-case.”
- “This Guidance created an Amazon SageMaker notebook that is billed per hour irrespective of usage.”
- “This Guidance creates unauthenticated public API endpoints.”


Provide a link to the *GitHub issues page* for users to provide feedback.


**Example:** *“For any feedback, questions, or suggestions, please use the issues tab under this repo.”*

## Revisions (optional)

Document all notable changes to this project.

Consider formatting this section based on Keep a Changelog, and adhering to Semantic Versioning.

## Notices (optional)

Include a legal disclaimer

**Example:**
*Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.*


## Authors (optional)

Name of code contributors
