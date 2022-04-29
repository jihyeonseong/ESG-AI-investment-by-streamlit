# ESG-investment with AI
***This repository is referenced by [ESG_AI](https://github.com/hannahawalsh/ESG_AI) 
which is [Hack to the Future 2020](https://devpost.com/software/esg-ai) 
Winner: Best Environmental Impact & Best User Experience***
<br></br>
**Demonstrating the power of Streamlit.** [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/monouns/esg-ai-investment/main.py)  

![visual_demo](https://user-images.githubusercontent.com/56622667/163711185-8fea43e6-0a1b-4145-95a4-b755cf915dbe.png)

## Project Flow
### This project's flow is,
- s&p500's 90% of enterprises reveal sustainability report every year.
- But we do not have standard evaluation format to get score of ESG.
- So crawlling the article from gdelt, and analyze tone of article about ESG and then scoring with the word that used in article 
- At scoring, gdelt databse is used.
- At porfolio creation, Node2Vec and Markowitz portfolio theory are used. 
<br></br>

## Data Crawling & Creation with Databricks 
Firstly, You have to sign up or sign in Databricks. You can use free trial for 14 days.
In Databricks, you can use pyspark very easily which can makes data crawling really fast!
 - Create your own workspace
 - Go to setting - Admin Console - Workspace Settings and set whatever you like to (I recommend Git, Web Terminal, DBGS File Browser enable)
 - Go to Compute and Create your own Cluster (If you are connected with AWS, it will create EC2 automatically)
 - Go to Repos and Create your own folder and notebooks (You can use Data_Creation folder!). Then run with your own cluster.
 - Go to Data and Select DFBS folder. You can see Data is created as csv!
<br></br>

Here are some magic codes for using Databricks for no conflict with python packages :)
1. If you get error with pip install gdelt
   ```bash
   python -m pip install gdelt --use-deprecated=backtrack-on-build-failures
   ```
2. If you get pkg version error, then reinstall it!
   ```bash
   pip install [pkg==ver] --force-reinstall
   ```

Also, You can download DBFS data files that you created at your local computer!
 - Go to User Settings - Access Tokens, then Generate New Token
 - In your local computer, install [Anaconda](https://www.anaconda.com/)
 - Open Anaconda prompt and install [databricks-cli](https://docs.databricks.com/dev-tools/cli/index.html)
   ```bash
   python -m pip install databricks-cli
   ```
 - You have to define your host and token
   ```bash
   databricks configure --token
   ```
   - You have to copy workspace url
   - You can generate token at your databricks workspace "user setting"
 - To check databricks-cli is well installed, type this command
   ```bash
   databricks fs -h
   ```
 - If databricks-cli is well installed, you can now download(=copy) DBFS folder to your local computer
   ```bash
   databricks fs cp -r [spark file path] [your local directory path] 
   ```
 - Then you can now access your data at your local computer to make streamlit web!
<br></br>

### Why we use databricks?
Databricks is an American enterprise software company founded by the creators of Apache Spark.
Databricks develops a web-based platform for working with Spark, that provides automated cluster management and IPython-style notebooks. 
[Wikipedia](https://en.wikipedia.org/wiki/Databricks)

***We can Create and Manage Data parallely with PySpark and this is really fast!***

### Why we need data crawlling and important rule to follow!
1. You must have to include December or January when crawling data!
   - This is important point, because year end and start is the evaluation period of company.
   - So you can get superior quality and quantity of article.

2. The number of article that crawled means the power or influence of company to society (ex. 551 press make article about MSFT)
   - This means, you can get rough information like company's trending degree from number of article
<br></br>

### What method is used to Scoring ESG?
***Node2Vec is used!***

you can see more detail explanation at [here](https://snap.stanford.edu/node2vec/)
<br></br>

### What method is used to form Portfolio?
***Markowitz Portfolio Theory is used!***

you can see more detail explanation at [here](https://towardsdatascience.com/efficient-frontier-portfolio-optimisation-in-python-e7844051e7f)
<br></br>


## Streamlit for Web demo
### Let's move to streamlit!

1. In your local computer,
   - Firstly download Pycharm and connect with Anaconda! (Of course, you have to install streamlit and requirements.txt in your Anaconda)
   - You can copy Graph.py, download_data.py, plt_setup.py, main.py to launch streamlit.
   - In your Anaconda Prompt, type below command to launch web!
     ```bash
     cd [your directory path]
     streamlit run main.py
     ```

2. Directly with your Github,
   - Firstly, you need requirements.txt and .py file to launch streamlit!
     - To make requirements.txt, use this command
       ```bash
       pip freeze > requirements.txt
       ```
   - Sign in or Sign up to [streamlit.io](https://streamlit.io/)
   - Click "New app" and connect to your github repository.
   - Then you can make URL in few seconds!


### What we can get from this web?
- You can get enough detailed information from graph and chart in web
   - Several metrics such as Tone, ESG score and graphs such as chart, rader are provided for detailed evaluation!
<br></br>

## Detail information for technical stack
1. What we usel for data?
   - gdelt
   - The GDELT Project, or Global Database of Events, Language, and Tone, created by Kalev Leetaru of Yahoo! and Georgetown University, along with Philip Schrodt and others, describes itself as "an initiative to construct a catalog of human societal-scale behavior and beliefs across all countries of the world, connecting every person, organization, location, count, theme, news source, and event across the planet into a single massive network that captures what's happening around the world, what its context is and who's involved, and how the world is feeling about it, every single day." Early explorations leading up to the creation of GDELT were described by co-creator Philip Schrodt in a conference paper in January 2011. The dataset is available on Google Cloud Platform. [wikipedia](https://en.wikipedia.org/wiki/GDELT_Project)

2. How can we reach data and create web demo?

   ![technical_stack](https://user-images.githubusercontent.com/56622667/162120751-d62c3a62-bbce-4098-acc7-bbad93d6fd0c.png)
   
   ![technical_stack2](https://user-images.githubusercontent.com/56622667/162120810-ec823d9e-745c-43c0-98e3-5890eeb5c60f.png)
   
   ![technical_stack_detail](https://user-images.githubusercontent.com/56622667/162120824-b49f86a4-7d10-4917-9f4f-f55616095815.png) 
   
3. We can get reasonable stock index from iShares!
   - [Russell 1000 etf](https://www.ishares.com/us/products/239707/ishares-russell-1000-etf)
   - [MSCI UK etf](https://www.ishares.com/us/products/239690/ishares-msci-united-kingdom-etf)
   - [MSCI Canada etf](https://www.ishares.com/us/products/239615/ishares-msci-canada-etf)
   - [MSCI Australia etf](https://www.ishares.com/us/products/239607/ishares-msci-australia-etf)
   - You can get stock index whatever you want in ishares.com and just change url in DataCreation/python_get_data_wrapper
<br></br>

## Note
I'm sorry for foreigners, the technical stack explanation slide is in Korean. But you can understand via images and icons!! :)
