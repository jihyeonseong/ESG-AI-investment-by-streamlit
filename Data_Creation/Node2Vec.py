# Databricks notebook source
import pandas as pd
import numpy as np
import networkx as nx
from nodevectors import Node2Vec as NVVV
from sklearn.decomposition import PCA
import os
import itertools
import pickle

spark.conf.set("spark.databricks.delta.properties.defaults.autoOptimize.optimizeWrite", "true")
spark.conf.set("spark.databricks.delta.properties.defaults.autoOptimize.autoCompact", "true")

# COMMAND ----------

def load_data(save_path, file_name): 
  df = (spark.read.format("delta")
                      .option("header", "true")
                      .option("inferSchema", "true")
                      .load(os.path.join(save_path, file_name))
           )
  return df.toPandas()


def filter_non_esg(df): 
    return df[(df['E']==True) | (df['S'] == True) | (df['G'] == True)]

# COMMAND ----------

class graph_creator:
    def __init__(self, df):
        self.df = df

    def create_graph(self):
        # Find Edges
        df_edge = pd.DataFrame(self.df.groupby("URL").Organization.apply(list)
                               ).reset_index()

        get_tpls = lambda r: (list(itertools.combinations(r, 2)) if
                              len(r) > 1 else None)
        df_edge["SourceDest"] = df_edge.Organization.apply(get_tpls)
        df_edge = df_edge.explode("SourceDest").dropna(subset=["SourceDest"])

        # Get Weights
        source_dest = pd.DataFrame(df_edge.SourceDest.tolist(),
                                   columns=["Source", "Dest"])
        sd_mapping = source_dest.groupby(["Source", "Dest"]).size()
        get_weight = lambda r: sd_mapping[r.Source, r.Dest]
        source_dest["weight"] = source_dest.apply(get_weight, axis=1)

        # Get
        self.organizations = set(source_dest.Source.unique()).union(
                             set(source_dest.Dest.unique()))
        self.G = nx.from_pandas_edgelist(source_dest, source="Source",
            target="Dest", edge_attr="weight", create_using=nx.Graph)
        return self.G

# COMMAND ----------

def get_embeddings(G, organizations):
    # Fit graph
    g2v = NVVV()
    g2v.fit(G)
    
    # Embeddings
    print("NVVVstart")
    embeddings = g2v.model.wv.vectors
    print("NVVVend")
    pca = PCA(n_components=3)
    principalComponents = pca.fit_transform(embeddings)
    d_e = pd.DataFrame(principalComponents)
    d_e["company"] = organizations
    return d_e, g2v

# COMMAND ----------

def get_connections(g2v, organizations, topn=25):
    if len(organizations)>25:
        topn = 25
    else:
        topn = len(organizations)        
    l = [g2v.model.wv.most_similar(org, topn=topn)
         for org in organizations]
    
    if len(organizations)>25:
        topn_ = 25
    else:
        topn_ = len(organizations)-1
    df_sim = pd.DataFrame(l, columns=[f"n{i}" for i in range(topn_)])
    for col in df_sim.columns:
        new_cols = [f"{col}_rec", f"{col}_conf"]
        df_sim[new_cols] = pd.DataFrame(df_sim[col].tolist(), 
                                        index=df_sim.index)
    df_sim = df_sim.drop(columns=[f"n{i}" for i in range(topn_)])
    df_sim.insert(0, "company", list(organizations))
    return df_sim


# COMMAND ----------

def make_embeddings_and_connections(start, end):
    base_dir = f"dbfs:/mnt/esg/financial_report_data/GDELT_data_Russell_top_300"
    market = '/USA'
    save_dir = os.path.join(base_dir, f"{start}__to__{end}"+market)
    csv_file = "data_as_csv.csv"

    # Load data
    print("Loading Data")
    df = pd.read_csv(os.path.join(save_dir, csv_file).replace("dbfs:/", "/dbfs/"))
    df = filter_non_esg(df)

    # Create graph
    print("Creating Graph")
    creator = graph_creator(df)
    G = creator.create_graph()
    organizations = list(creator.organizations)

    # Save graph as pkl
    fp = os.path.join(save_dir, "organization_graph.pkl").replace("dbfs:/", "/dbfs/")
    with open(fp, "wb") as f:
        pickle.dump(G, f)
        
    # Create embeddings
    print("Creating embeddings")
    emb_path = os.path.join(save_dir, "pca_embeddings.csv").replace("dbfs:/", "/dbfs/")
    d_e, g2v = get_embeddings(G, organizations)
    d_e.to_csv(emb_path, index=False)
    
    # Create connections
    print("Creating connections")
    df_sim = get_connections(g2v, organizations)
    sim_path = os.path.join(save_dir, "connections.csv")
    df_sim.to_csv(sim_path.replace("dbfs:/", "/dbfs/"))
    
    # Save organizations as delta
    conn_path = os.path.join(save_dir, "CONNECTIONS")
    conn_data = spark.createDataFrame(df_sim)
    conn_data.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(conn_path)


# COMMAND ----------


