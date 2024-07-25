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

Following diagram shows the reference architecture for the SAP Generative AI assistanct: 


![reference architecture for Generative AI assistance](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/1.Architecture.jpeg?raw=true)

The steps shown in the diagram are as follows:

1) Use Amazon S3 to store the data extract from SAP using your favorite tool or procedure; the data can be in CSV or JSON format. This guidance uses csv 

2) Amazon Athena uses AWS Glue Data Catalog (not shown in diagram) to query the tables directly in Amazon S3

3) User interacts with StreamLit chat application to perform tasks or ask questions

4) Amazon Lex natural language chatbot curates communication to handle the response & sends the users question to AWS Lambda for processing

5) AWS Lambda sends the response back to the Chat App via Amazon Lex. Lex stores the message history in a session

6) The AWS Lambda function uses LangChain to formulate Athena query and retrieves relevant data 

7) The AWS Lambda invokes Amazon Bedrock endpoint and provides the user question and relevant data from Athena. Amazon Bedrock responds with answer in human readable format


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

![Deployment Steps](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/Deployment-Steps.jpg?raw=true)


1. **Get Access to Amazon Bedrock Models**

Go to Amazon Bedrock —> Model Access —> Modify Model Access and select Claude:

![Model Access](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/2.Amazon%20Bedrock%20Claude%20Selection.jpeg?raw=true)

Click Next and click submit. It may take few minutes for access for model to get updated then you will able to access the Model.

2. **Create AWS glue data catalog**

<TO BE REVISITED>

For data stored in Amazon S3, use AWS Glue crawler to create database. Follow the instruction as per the [blog](https://aws.amazon.com/blogs/big-data/introducing-aws-glue-crawlers-using-aws-lake-formation-permission-management/). 
You can schedule recreation of database catalogue to update database catalogue

Please make sure you are able to query the data using Amazon Athena
Please take note of: DATABASENAME and SCHEMANAME.


3. **Create AWS Lambda Layer**

**Create S3 bucket** : YOURSLAMBDALAYERS3 in your AWS Account.
Download following lambda layers to S3 bucket of your account. Rename the files to python.zip as shown in example below.

* [langchainlayer](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/langchainlayer.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip)

* [pyAthena](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/SQLAlchemy.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/pyAthena/python.zip

* [SQLAlchemy](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/deployment/pyAthena.zip) : store it in s3 as: s3://YOURSLAMBDALAYERS3/SQLAlchemy/python.zip

1. Navigate to [AWS Lambda - Layers](https://console.aws.amazon.com/lambda/#/layers), then click **Create layer**
2. Type the following in to the Lambda Layer screen, then click **Create**
3.Name: langchainlayer
4. Description: langchainlayer
5. Choose: **Upload a file from Amazon S3: s3://YOURSLAMBDALAYERS3/langchainlayer/python.zip**
6. Compatible architectures: **x86_64**
7. Compatible runtimes: **Python 3.10**

![lambda layer creation](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/3.LambdaLayerCreation.jpeg?raw=true)


Repeat above steps 1-7 for pyAthena and  SQLAlchemy



4. **Create AWS Lambda Function**

* Navigate to [AWS Lambda - Functions](https://console.aws.amazon.com/lambda/#/functions), then click **Create function**
* Type the following information, then click **Create function**
* Select **Author from scratch**
* Function Name: SAPGenAIAssitant
* Runtime: **Python 3.10**
* Architectures: **x86_64**
  
![create lambda function](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/4.%20Lambda%20Function%20Creation.jpeg?raw=true)

* Add [helpers.py](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/code/helpers.py) file in Code source and remember to change the athena connection parameters based on your AWS account configuration

![add code to lambda](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/5.LambdaHelperFileCreation.jpeg?raw=true)
 
* Add [lambda_fuction.py](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/code/lambda_function.py), then click **Deploy**


 

1. Click **Layers**
2. Click **Add a layer**
3. Type the following information, then click **Add**

    * Layer source: **Custom layers**
    * Custom layers: **LangChainLayer**
    * Version: **Choose the Latest**
  
![add layer](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/6.LambdaLayerAddition.jpeg?raw=true)

Repeat above steps to add layers for **pyAthena** and **SQLAlchemy**

   1. Go to **Configuration - General Configuration**, then click **Edit**
   2. Change timeout from 3 seconds to **10 minutes**, then click **Save**

![configuration settings](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/7.LambdaEditConfiguraitonIncreaseTimeOut.jpeg?raw=true)

**Create Role**

   * Go to **Configuration - Permissions**, then click at the role name **SAPGenAIAssistant-role-xxxxxxx**

![role name configuration](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/8.LambdaEditConfiguraitonEditRole.jpeg?raw=true)

   * Click **Add permissions**, click dropdown **Create inline policy**
   * Click **JSON**, then add [SAPGenAIPolicy](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/code/SAPGenAIPolicy) to **Policy editor**, then click **Next**

   * Type **SAPGenAIPolicy** as policy name then Click **Create policy**

<br>

**5. **Create Amazon Lex Bot****

Follow these steps to creaste Amazon Lex Bot:

1.Navigate to [Amazon Lex](https://us-east-1.console.aws.amazon.com/lexv2/home?region=us-east-1)
2.Click Create bot
3.Choose create blank bot and Provide Bot name and configurations and click Next:

![Lex Bot Creation](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/9.AmazonLexBotCreation1.jpeg?raw=true)

![Lex IAM creation](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/10.AmazonLexBotCreation2.jpeg?raw=true)

Select language as English and click Done to create Bot.

4.Provide name to NewIntent as greeting_intent and update description “this is hello intent” 

![Lex new intent](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/11.AmazonLexNewIntentCreation.jpeg?raw=true)

Provide at least one utterance as “hi” and save intent

![sample lex utterance](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/12.AmazonLexUtterance.jpeg?raw=true)

1. Navigate to Versions >Version: Draft>All languages>Language: English (US)>Intents
2. Click on FallbackIntent and Activate Fulfillment and click Save Intent and Click Build:

![lex fallback intent](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/13.AmazonLexFallBackIntent.jpeg?raw=true)

1. Click on Test
2. Select Lambda function created and select $Latest and save:

![save lambda test function](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/14.AmazonLexTestLambdaFunction.jpeg?raw=true)

Type questions to test the response:

![test response from lex](https://github.com/aws-solutions-library-samples/guidance-to-summarize-sap-supply-chain-data-using-genai-on-aws/blob/main/assets/images/15.AmazonLexTestResult.jpeg?raw=true)


6. **Create Strimlit App for Lex**

Follow [aws-lex-web-ui](https://github.com/aws-samples/aws-lex-web-ui)  guidance to create strimlit App 



## Running the Guidance



## Next Steps



## Cleanup

## FAQ

## Notices

*Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.*

## Contributors
