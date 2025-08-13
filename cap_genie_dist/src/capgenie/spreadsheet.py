# File that processses read data and saves them into spreadsheets
# calculations for extra fields: mean, range, std, outlier // WIP

import pandas as pd
import os


class spreadsheet:
    def __init__(self, session_dir, sheets_dir, cache_folder):
        self.session_dir = session_dir
        self.sheets_dir = sheets_dir
        self.cache_folder = cache_folder

    """
    save_file: str, str, str, str, bool, bool --> None
    -- Saves file into an excel spreadsheet
    * @param [in] pkl_file_path (str) - Path to pickle file directory
    * @param [in] file (str) - File name to save
    * @param [in] data_directory (str) - Data directory path
    * @param [in] instruction_link (str) - Instruction link for file extension
    * @param [in] avg_file (bool) - Whether this is an average file
    * @param [in] barcode (bool) - Whether to include barcode processing
    * @param [out] None - Saves Excel file to sheets directory
    ** Saves processed data to Excel spreadsheet format
    """
    def save_file(self, pkl_file_path, file, data_directory, instruction_link, avg_file=False, barcode=True):
        if instruction_link == "count_known_reads":
            file_ext = "variants_"
        else:
            file_ext = "unknown_variants_"

        if not os.path.exists(os.path.join(self.sheets_dir, data_directory)):
            os.mkdir(os.path.join(self.sheets_dir, data_directory))

        if not avg_file:
            df = pd.read_pickle(os.path.join(pkl_file_path, data_directory, f"{file_ext}{file}").replace(".fastq", ".pkl"))
            # Ensure all expected peptides are present, fill missing with 0
            if "Peptide" in df.columns and "Count" in df.columns:
                all_peptides = df["Peptide"].unique().tolist()
                df = df.set_index("Peptide")
                for peptide in all_peptides:
                    if peptide not in df.index:
                        df.loc[peptide] = {"Count": 0, "Decimal": 0.0}
                df = df.reset_index()
            df.to_excel(os.path.join(self.sheets_dir, data_directory, f"{file_ext}{file}").replace(".fastq", ".xlsx"))
        else:
            df = pd.read_pickle(os.path.join(pkl_file_path, data_directory, file).replace(".fastq", ".pkl"))
            #extra_columns = ["_".join(column.split("_")[0:2]) for column in df.columns.to_list()[:-1]]
            #extra_columns.append(df.columns.to_list()[-1])
            #df.columns = extra_columns
            df.to_excel(os.path.join(self.sheets_dir, data_directory, file).replace(".fastq", ".xlsx"))



        
                
        
        
        