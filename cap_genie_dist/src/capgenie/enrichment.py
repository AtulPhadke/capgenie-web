
from pandas import DataFrame
import pandas as pd
import os
import pickle as pkl

class enrichment:

    def __init__(self, session_folder, sheets_dir, cache_folder):
        self.session_folder = session_folder
        self.sheets_dir = sheets_dir
        self.cache_folder = cache_folder

    """
    process_dict: dict --> dict
    -- Takes a dictionary and makes sure to return float values
    of each count
    * @param [in] dic (dict) - Dictionary with percentage values
    * @param [out] result (dict) - Dictionary with converted float values
    ** Converts percentage strings to float values
    """

    def process_dict(self, dic):
        return {x:self.p2f(y) for x,y in dic.items() if self.p2f(y)!=0}

    """
    p2f: any --> float
    -- Takes a percentage number and converts into a python
    float type
    * @param [in] x (any) - Percentage number (string or numeric)
    * @param [out] result (float) - Converted float value
    ** Converts percentage to float (divides by 100)
    """

    def p2f(self,x):
        return float(x.strip('%'))/100

    """
    calc_enrichment: str, str, list, str, str --> str
    -- Calculates the enrichment of all fastq files and saves them into 
    excel sheets and .pkl
    * @param [in] pre_insert (str) - The pre insert file used for calculating enrichment
    * @param [in] session_folder (str) - Session folder path
    * @param [in] files (list) - List of files to process
    * @param [in] data_directory (str) - Data directory path
    * @param [in] instruction_name (str) - Instruction name for file extension
    * @param [out] result (str) - Name of the generated enrichment file
    ** Calculates enrichment factors for peptide data
    """

    def calc_enrichment(self, pre_insert, session_folder, files, data_directory, instruction_name):
        if instruction_name == "count_known_reads":
            file_ext = "variants_"
        else:
            file_ext = "unknown_variants_"
        pre_insert_path = os.path.join(os.path.basename(os.path.dirname(pre_insert)), f"{file_ext}{os.path.basename(pre_insert)}").replace(".fastq", ".pkl")
        pre_insert_dict = pkl.load(open(os.path.join(self.cache_folder, session_folder, "pkl_files", pre_insert_path), "rb"))
        pre_insert_dict = dict(zip(pre_insert_dict.Peptide, pre_insert_dict.Decimal))
        pre_insert_dict = {x:y for x,y in pre_insert_dict.items() if y != 0}

        new_enrichment_dict = {}
        columns = []

        for file in files:
            if os.path.basename(pre_insert).replace(".fastq", "") not in file:
                file_dict = pd.read_pickle(os.path.join(self.cache_folder, session_folder, "pkl_files", data_directory, f"{file_ext}{file}").replace(".fastq", ".pkl"))
                obj_dict = dict(zip(file_dict.Peptide, file_dict.Decimal))

                for key, pre_insert_value in pre_insert_dict.items():
                    if key not in obj_dict:
                        pass
                    else:
                        if key not in new_enrichment_dict:
                            new_enrichment_dict[key] = [obj_dict[key]/pre_insert_value]
                        else:
                            new_enrichment_dict[key].append(obj_dict[key]/pre_insert_value)
                columns.append(file)
                

        df = DataFrame.from_dict(new_enrichment_dict, orient='index', columns = columns)
        df.index.name = "Peptide"
        cols = df.columns.tolist()
        df = df[cols]
        df['Average_Enrichment'] = df[cols].mean(axis=1)
        df = df.sort_values("Average_Enrichment", ascending=False)
        df.to_pickle(os.path.join(self.cache_folder, session_folder, "pkl_files", data_directory, f"average_enrichment_{data_directory}.pkl")) 
        return f"average_enrichment_{data_directory}.fastq"
