# Guidance to create Generative AI Assistant for SAP Data

This guidance demonstrates how to improve business user productivity and experience using real-time data summaries, task automation, seamless natural language interactions.

## Table of Contents  

1. [Overview](#overview)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)
8. [FAQ, known issues, additional considerations, and limitations](#faq)
9. [Notices](#notices)
10. [Contributors](#Contributors)

## Overview

SAP business users across industries analyze data, write executive summaries, and perform repetitive tasks such as creating reports. These tasks usually take long time and effort, are error prone, and are depenednent on an individual's interpretation of data since we are working with large data sets. It also need specific skillsets related to understanding of data and reporting structure.

Generative AI assistant for SAP data improves productivity by enabling natural language quering for personas such as C-Suite executives, managers, auditors, and field users. This Guidance demonstrates how to improve business user experience and productivity by providing following:

* Natural language interaction
* Real-time data summary
* Task automation

The solution uses Amazon Bedrock for generative AI and Amazon Lex for conversational AI assistant. This Guidance enables you to start your Generative AI journey with SAP data, allowing you to seamlessly incorporate additional components or integrate with other AWS services.

Following diagram shows the reference architecture for the SAP Generative AI assistant: 


![reference architecture for Generative AI assistance](assets/images/1.Architecture.jpeg?raw=true)

Follwing are the steps for the solution as shown in the architecture:

1) Extract or federate data from SAP ERP (or SAP Datasphere) using [AWS SAP Data integration solutions](https://aws.amazon.com/solutions/enterprise-resource-planning/data-integration-management-for-sap/) 

2) Amazon Athena uses AWS Glue Data Catalog to query the tables directly in Amazon S3

3) User interacts with chat application of choice to perform tasks or answer questions.

4) Amazon Lex natural language chatbot curates communication to handle the response & sends the users question to AWS Lambda for processing

5) AWS Lambda sends the response along with message history back to the Chat App via Amazon Lex. Lex stores the message history in a session

6) The AWS Lambda function invokes Amazon Bedrock endpoint to formulate Athena query using [LangChain framework](https://aws.amazon.com/what-is/langchain/)

7) The AWS Lambda executes generated Athena query and retrieves data

8) The data is then interpreted by Bedrock  and generate response for data retrieved from Athena query to provide human readable response


## Cost

_We recommend creating a [Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) through [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this Guidance._

### Sample Cost breakdown

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month.


|AWS service	|Dimensions	|Cost [USD]	|
|---	|---	|---	|
|Amazon Lex	| 2000 text requests	| 0.75	|
|AWS Lambda	|	1000 invocations| 0	|
|Amazon Athena	| 3041 query executions	| 1	|
|Amazon Bedrock | 1000 input/output tokens	|18	|
|Amazon S3	|1 TB standard	|24	|
|AWS Glue	|1 stored object accessed 1000 times	|1	|
|	|	|	|

## Prerequisites

To deploy this solution in your AWS account, you need acces to deploy and configure following AWS services from console: 

  * Amazon Lex
  * AWS lambda
  * Amazon Athena
  * Amazon Bedrock
  * AWS Glue
  * Amazon S3 bucket
    
This guidance assumes SAP data is extracted in an Amazon S3 bucket; you can use one of the approaches highlighted in the [Guidance for SAP Data Integration and Management on AWS](https://aws.amazon.com/solutions/guidance/sap-data-integration-and-management-on-aws/?did=sl_card&trk=sl_card) to extract data from your SAP system.
[Note: Make a note of s3 path where data is stored; for example: s3://YOURSLAMBDALAYERS3/PATHtoData/]


## Deployment Steps

Following diagram shows the deployment steps for the solution and we discuss each step in this section:

![Deployment Steps](assets/images/Deployment-Steps.jpg?raw=true)


1. **Get Access to Amazon Bedrock Models**

To get access to Claude foundation model (FM), go to Amazon Bedrock —> Model Access —> Modify Model Access and select Claude:

![Model Access](assets/images/2.Amazon%20Bedrock%20Claude%20Selection.jpeg?raw=true)

Click Next and click submit. It may take few minutes for access for model to get updated then you will able to access the Model.

2. **Create AWS glue data catalog**

<TO BE REVISITED>

For data stored in Amazon S3, use AWS Glue crawler to create database; you can use [Amazon documentation Tutorial](https://docs.aws.amazon.com/glue/latest/dg/tutorial-add-crawler.html). 
You can also schedule recreation of database catalog to keep it upto date.

Tip: make sure you are able to query the data using Amazon Athena and note the DATABASENAME and SCHEMANAME.


3. **Create AWS Lambda Layer**

Following steps show how to create Lambda layer:

1. Create S3 bucket: Assuming name YOURSLAMBDALAYERS3 (replace with any name of your choice) in your AWS Account. Then download following lambda layers to S3 bucket of your account (rename the files to python.zip as shown in example below)

   * [langchainlayer](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/langchainlayer.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip)

   * [pyAthena](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/SQLAlchemy.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/pyAthena/python.zip

   * [SQLAlchemy](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/pyAthena.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/SQLAlchemy/python.zip

2. Navigate to [AWS Lambda - Layers](https://console.aws.amazon.com/lambda/#/layers), then click **Create layer**
   * Type the following in to the Lambda Layer screen, then click Create Name: langchainlayer
   * Description: langchainlayer
   * Choose: **Upload a file from Amazon S3: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip**
   * Compatible architectures: **x86_64**
   * Compatible runtimes: **Python 3.10**

![lambda layer creation](assets/images/3.LambdaLayerCreation.jpeg?raw=true)


      **Repeat step 2 above for pyAthena and  SQLAlchemy**



4. **Create AWS Lambda Function**

Follow the steps below to create the Lambda function (as shown in the screenshot below): 

* Navigate to [AWS Lambda - Functions](https://console.aws.amazon.com/lambda/#/functions), then click **Create function**
* Type the following information, then click **Create function**
* Select **Author from scratch**
* Function Name: SAPGenAIAssitant
* Runtime: **Python 3.10**
* Architectures: **x86_64**
  
![create lambda function](assets/images/4.%20Lambda%20Function%20Creation.jpeg?raw=true)

* Add [helpers.py](assets/code/helpers.py) file in Code source (as shown in the following screenshot) and remember to change the athena connection parameters in the code (.py file) based on your AWS account configuration

![add code to lambda](assets/images/5.LambdaHelperFileCreation.jpeg?raw=true)
 
* Add [lambda_fuction.py](assets/code/lambda_function.py), then click **Deploy**

**Add Layers to Lambda Function**

Follow these steps to add layers to the Lambda function:

1. Click **Layers** button in your Lambda function 
2. Click **Add a layer**
3. Type the following information, then click **Add**

    * Layer source: **Custom layers**
    * Custom layers: **LangChainLayer**
    * Version: **Choose the Latest**
  
![add layer](assets/images/6.LambdaLayerAddition.jpeg?raw=true)

      Repeat above steps to add layers for **pyAthena** and **SQLAlchemy**

**Changing Default configuration of Lambda Function**

Follow these steps to change the default configuration in your lambda function (as shown in the following screenshot):

   1. Go to **Configuration - General Configuration**, then click **Edit**
   2. Change timeout from 3 seconds to **10 minutes**, then click **Save**

![configuration settings](assets/images/7.LambdaEditConfiguraitonIncreaseTimeOut.jpeg?raw=true)

**Update Role for the Lambda Function**

Follow these steps to update the role in the Lambda function to get right access to services in this guidance(as shown in the following screenshot):


   * Go to **Configuration - Permissions**, then click at the role name **SAPGenAIAssistant-role-xxxxxxx**

![role name configuration](assets/images/8.LambdaEditConfiguraitonEditRole.jpeg?raw=true)

   * Click **Add permissions**, click dropdown **Create inline policy**
   * Click **JSON**, then add [SAPGenAIPolicy](assets/code/SAPGenAIPolicy) to **Policy editor**, then click **Next**

   * Type **SAPGenAIPolicy** as policy name then Click **Create policy**

<br>

**5. **Create Amazon Lex Bot****

Follow these steps to create Amazon Lex Bot (as shown in next 2 screenshots):

* Navigate to [Amazon Lex](https://us-east-1.console.aws.amazon.com/lexv2/home?region=us-east-1)
* Click Create bot
* Choose create blank bot and Provide Bot name and configurations and click Next:

![Lex Bot Creation](assets/images/9.AmazonLexBotCreation1.jpeg?raw=true)

![Lex IAM creation](assets/images/10.AmazonLexBotCreation2.jpeg?raw=true)

* Select language as English and click Done to create Bot.

* Provide name to NewIntent as greeting_intent and update description “this is hello intent” 

![Lex new intent](assets/images/11.AmazonLexNewIntentCreation.jpeg?raw=true)

* Provide at least one utterance as “hi” and save intent

![sample lex utterance](assets/images/12.AmazonLexUtterance.jpeg?raw=true)

* Navigate to Versions >Version: Draft>All languages>Language: English (US)>Intents
* Click on FallbackIntent and Activate Fulfillment and click Save Intent and Click Build:

![lex fallback intent](assets/images/13.AmazonLexFallBackIntent.jpeg?raw=true)

* Click on Test
* Select Lambda function created and select $Latest and save:

![save lambda test function](assets/images/14.AmazonLexTestLambdaFunction.jpeg?raw=true)

* Type questions to test the response:

![test response from lex](assets/images/15.AmazonLexTestResult.jpeg?raw=true)

<br>

6. **Create Lex Web UI**

You can use any frontend application of your choice such as SAP BTP Build Apps. This guidance uses Web UI for Lex as shown in [this guidance](https://github.com/aws-samples/aws-lex-web-ui).


## Next Steps

This guidance provides the zip files for Lambda layer, which are compatible with Python 3.10; for future releases, you can create layers by downloading libraries for following sources:

* [SQL Alchemy](https://www.sqlalchemy.org/download.html)
* [PyAthena](https://pypi.org/project/PyAthena/#files)
* [Langchain](https://python.langchain.com/v0.2/docs/integrations/platforms/aws/)


## Notices

*Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.*
