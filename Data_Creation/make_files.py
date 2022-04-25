# Databricks notebook source
# MAGIC %run ./python_get_data_wrapper

# COMMAND ----------

# MAGIC %run ./ESG_Financial_Segment

# COMMAND ----------

# MAGIC %run ./Node2Vec

# COMMAND ----------

base_dir = "dbfs:/mnt/esg/financial_report_data"

# COMMAND ----------

def make_files(base_dir, start_date, end_date):

    # Directories
    org_types = f"Russell_top_{Fields.n_orgs}"
    org_dir = os.path.join(base_dir, f"GDELT_data_{org_types}")
    date_string = f"{start_date}__to__{end_date}"
    market = '/AUSTRAILIA'
    date_dir = os.path.join(org_dir, date_string+market)
    dbutils.fs.mkdirs(org_dir)


    # Check if file has already been created, and if not, do so
    exists = False
    subdirs = [x.name for x in dbutils.fs.ls(org_dir)]
    if date_string + "/" in subdirs:
        subsubdirs = [x.name for x in dbutils.fs.ls(date_dir)]
        if "data_as_delta/" in subsubdirs:
            exists = True
    if exists:
        print("Data already created!")
    else:
        print("Creating Data")
        _ = create_and_save_data(start_date, end_date, save_csv=True)


    # Check if ESG data has already been created, and if not, do so
    if exists and "esg_data/" in subsubdirs:
        print("\n\nESG data already created!")
    else:
        print("\n\nMaking Tables")
        make_tables(start_date, end_date)


    # Create embeddings and connections files
    print("\n\nComputing Embeddings & Connections")
    make_embeddings_and_connections(start_date, end_date)

# COMMAND ----------

start_date = "2021-12-01"
end_date = "2022-04-21"
make_files(base_dir, start_date, end_date)



