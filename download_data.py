import pandas as pd
import numpy as np
import os


class Data:

    def paths(self, data_path, flag='USA'):
        # Paths to data files
        self.connections = os.path.join(data_path, "connections.csv")
        self.data = os.path.join(data_path, "data_as_csv.csv")
        self.embeddings = os.path.join(data_path, "pca_embeddings.csv")
        esg_path = os.path.join(data_path, "esg_scores")
        self.avg_esg = os.path.join(esg_path, "average_esg_scores.csv")
        self.daily_esg = os.path.join(esg_path, "overall_daily_esg_scores.csv")
        self.e_score = os.path.join(esg_path, "daily_E_score.csv")
        self.s_score = os.path.join(esg_path, "daily_S_score.csv")
        self.g_score =os.path.join(esg_path, "daily_G_score.csv")
        if flag == 'USA':
            self.portfolio = os.path.join(data_path, "portfolio.csv")



    def read(self, start_day="jan6", end_day="jan12", flag='USA'):
        data_dir = os.path.join("./Data", f"{start_day}__to__{end_day}")
        dir_name = flag

        if dir_name not in os.listdir(data_dir):
            raise NameError(f"There isn't data for {dir_name}")

        data_path = os.path.join(data_dir, dir_name)
        self.paths(data_path, flag)
        if flag == 'USA':
            data = {"conn": pd.read_csv(self.connections),
                    "data": pd.read_csv(self.data, parse_dates=["DATE"],
                                     infer_datetime_format=True),
                    "embed": pd.read_csv(self.embeddings),
                    "overall_score": pd.read_csv(self.daily_esg,
                                      index_col="date", parse_dates=["date"],
                                     infer_datetime_format=True),
                    "E_score": pd.read_csv(self.e_score, parse_dates=["date"],
                                     infer_datetime_format=True, index_col="date"),
                    "S_score": pd.read_csv(self.s_score, parse_dates=["date"],
                                     infer_datetime_format=True, index_col="date"),
                    "G_score": pd.read_csv(self.g_score, parse_dates=["date"],
                                     infer_datetime_format=True, index_col="date"),
                    "ESG": pd.read_csv(self.avg_esg),
                    "Portfolio": pd.read_csv(self.portfolio),
                    }
        else:
            data = {"conn": pd.read_csv(self.connections),
                    "data": pd.read_csv(self.data, parse_dates=["DATE"],
                                     infer_datetime_format=True),
                    "embed": pd.read_csv(self.embeddings),
                    "overall_score": pd.read_csv(self.daily_esg,
                                      index_col="date", parse_dates=["date"],
                                     infer_datetime_format=True),
                    "E_score": pd.read_csv(self.e_score, parse_dates=["date"],
                                     infer_datetime_format=True, index_col="date"),
                    "S_score": pd.read_csv(self.s_score, parse_dates=["date"],
                                     infer_datetime_format=True, index_col="date"),
                    "G_score": pd.read_csv(self.g_score, parse_dates=["date"],
                                     infer_datetime_format=True, index_col="date"),
                    "ESG": pd.read_csv(self.avg_esg),
                    }
        # Dat column to date (not timestamp)
        data["data"]["DATE"] = data["data"]["DATE"].dt.date

        # Multiply tones by large number
        esg_tables = ["E_score", "S_score", "G_score", "overall_score", "ESG"]
        for t in esg_tables:
            num_cols = data[t].select_dtypes(include=["number"]).columns
            data[t][num_cols] *= 10000

        return data
