from capgenie.bubble import gen_bubble_plots # See bubble.py for implementation
from capgenie.biodistribution import gen_bio_graphs # See biodistribution.py for implementation
from capgenie.motif import Motif
import os
import argparse
from capgenie.search_aav9 import search_aav9 # See search_aav9.py for implementation
from capgenie.enrichment import enrichment # See enrichment.py for implementation
from capgenie.spreadsheet import spreadsheet # See spreadsheet.py for implementation
from capgenie import mani # See mani.cpp for implementation
from capgenie import denoise # See denoise.cpp for implementation

# Currently all implemented features for pipeline

usage = "capgenie [-cf FOO] [-f FOO] [-o FOO] -unk [-s FOO] [-e FOO] -w -qual -bar -cls"

parser = argparse.ArgumentParser(description="CAPGENIE CLI")

group = parser.add_mutually_exclusive_group()

group.add_argument("-cf", "--capsidfile", help="Capsid file path")

parser.add_argument("-m", "--mismatches", help="Required flag 1 for capsid file")
parser.add_argument("-mt", "--mtype", help="Required flag 2 for capsid file")

parser.add_argument("-f", "--folder", required=True, help="Nested folder containing fastq file studies")
parser.add_argument("-o", "--output", required=False, help="Output Directory")
group.add_argument("-unk", "--unknownvariants", help="search for unknown variants", action="store_true")

parser.add_argument("-f1", "--flank1", help="Optional flag 1 for unknown variants")
parser.add_argument("-f2", "--flank2", help="Optional flag 2 for unknown variants")
parser.add_argument("-rf", "--refseq", help="Optional flag 2 for unknown variants")

parser.add_argument("-s", "--spreadsheet_extension", help="File extension of spreadsheet files (Excel or CSV)", default="Excel")
parser.add_argument("-e", "--enrichment", help="Enrichment File path")
parser.add_argument("-b", "--bubble", help="Generate bubble charts", action="store_true")
parser.add_argument("-fd", "--freq_distribution", help="Generate frequency distribution charts", action="store_true")
parser.add_argument("-qual", "--quality_threshold", help="Quality threshold for denoising fastq files", default=False)
parser.add_argument("-cls", "--clear_cache", help="This option clears all cache", action="store_true")
parser.add_argument("-ses", "--session", help="DESKTOP: overrides the session name so no command utility is asked")
parser.add_argument("-mot", "--motif", help="Find motifs in capsid file", action="store_true")

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class cap_genie:
    def __init__(self, args):
        self.args = args

        # Processes all the args

        self.nested_dir = self.args.folder
        self.output_dir = self.args.output
        self.enrichment_file = self.args.enrichment
        self.spreadsheet_extension = self.args.spreadsheet_extension
        self.quality_threshold = self.args.quality_threshold
        self.bubble = self.args.bubble
        self.freq_distribution = self.args.freq_distribution
        self.session_name = self.args.session
        self.run_motif = self.args.motif

        if self.args.clear_cache:
            mani.clear_cache_folder()
            print("Cleared Cache!")
            quit()

        if not self.args.capsidfile and not self.args.unknownvariants:
            parser.error("Either -cf/--capsidfile or -unk/--unknownvariants must be provided.")
        else:
            self.capsid_file = self.args.capsidfile
            self.unknown_variants = self.args.unknownvariants

            if self.unknown_variants:
                self.flanks = [self.args.flank1, self.args.flank2]
            elif self.capsid_file:
                if self.args.mismatches:
                    self.mismatches = int(self.args.mismatches)
                    self.mismatch_type = self.args.mtype
                else:
                    self.mismatches = 0
            self.known_variants = not self.unknown_variants

        self.SEPERATOR = "----------------------------------------"

        self.dirs = []

        self.denoised_dirs = []

    """
    get_files: None --> list
    -- Gets all FASTQ files from the nested directory structure
    * @param [out] files (list) - List of FASTQ file paths
    ** Recursively finds all FASTQ files in the nested directory
    """
    def get_files(self):

        if not self.session_name:
            file_map = {}
            idx = 1
            print(color.BOLD + "Counting Reads" + color.END)
            print("You currently have these folders in your project folder: \n")
            print(color.BOLD + self.nested_dir + color.END)
            for file in os.listdir(self.nested_dir):
                if file != ".DS_Store":
                    print("-- " + file + " [" + str(idx) + "] ")
                    file_map[str(idx)] = os.path.join(self.nested_dir, file) # Map file to a specific index
                    idx += 1
            print("All Fastq files in these folders will be counted for reads.")
            
            folders = input("Select which folders to process: ")
            if folders == "all":
                self.dirs = [os.path.basename(v) for k,v in file_map.items()]
            else:
                # Gets folder basenames
                self.dirs = [os.path.basename(file_map[str(folder)]) for folder in list(folders)]
        else:
            self.dirs = [os.path.basename(dir) for dir in os.listdir(self.nested_dir) if dir != ".DS_Store"]
    """
    denoise_files: search_aav9 --> None
    -- Denoises FASTQ files using quality threshold
    * @param [in] instance (search_aav9) - Search AAV9 instance
    * @param [out] None - Denoises files and saves results
    ** Filters low-quality reads from FASTQ files
    """
    def denoise_files(self, instance):
        for dir in self.dirs:
            for file in os.listdir(os.path.join(self.nested_dir, dir)):
                if file.endswith(".fastq"):
                    file_path = os.path.join(self.nested_dir, dir, file)
                    new_dir = os.path.join(instance._cache_folder, instance.save_dir, "denoised_"+ dir)
                    print(new_dir)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                        self.denoised_dirs.append(new_dir)
                    
                    result = denoise.denoise(file.encode(), file_path.encode(), new_dir.encode(), int(self.quality_threshold))
                    spliced_enrichment_file = os.path.normpath(self.enrichment_file).split(os.sep)
                    if os.path.join(*spliced_enrichment_file[-2:]) == os.path.join(dir, file):
                        self.enrichment_file = result.output_filename
                    instance.save_denoise_result(result, file)
                    print(f"Denoised {file}, saved under {os.path.join(new_dir, file)}.")
    """
    run_pipeline: None --> None
    -- Main pipeline execution method that processes all selected files
    * @param [out] None - Executes the complete pipeline workflow
    ** Orchestrates the entire CAPGENIE pipeline workflow
    """
    def run_pipeline(self):
        instance = search_aav9()

        if self.session_name:
            instance._override_session(self.session_name)
        else:
            instance.init_session()

        if self.unknown_variants:
            if None in self.flanks:
                self._run_flank = False
                self.ref_seq = self.args.refseq
            else:
                self._run_flank = True
                upstream = self.flanks[0]
                downstream = self.flanks[1]

        session_folder = instance.save_dir

        new_dirs = []

        self.sheets_dir = os.path.join(instance._cache_folder, session_folder, "spreadsheets")
        self.bubble_dir = os.path.join(instance._cache_folder, session_folder, "bubble")
        self.freq_dir = os.path.join(instance._cache_folder, session_folder, "freq_distribution")

        new_dirs.extend([self.sheets_dir, self.bubble_dir, self.freq_dir])

        spreadsheet_instance = spreadsheet(session_folder, self.sheets_dir, instance._cache_folder)
        enrichment_instance = enrichment(session_folder, self.sheets_dir, instance._cache_folder)

        for new_dir in new_dirs:
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
                print(f"Created {new_dir}")

        self.get_files()

        if self.quality_threshold:
            self.denoise_files(instance)

        instructions_link = ""

        if self.capsid_file:
            instructions_link = "count_known_reads"
            peptide_map = search_aav9.create_peptide_map(self.capsid_file)
            print("Here's the capsid file imported: ")
            mani.pprint_csv(self.capsid_file)
            #input("Press enter to run pipeline: ")
            print(self.run_motif)
            if self.run_motif:
                print(color.BOLD + "Finding Motifs" + color.END)
                save_dir = os.path.join(instance._cache_folder, instance._save_dir)
                motif = Motif(list(peptide_map.values()), True)
                motif.get_motifs(save_dir)
                print(color.BOLD + "Creating Motif Logo" + color.END)
                motif.createMotifLogo(f"{save_dir}")
                print(f"Motif Logo saved to: {save_dir}")
            print(color.BOLD + "Searching for known reads" + color.END)

        else:
            instructions_link = "unknown_reads"
            print(color.BOLD + "Searching for Unknown reads" + color.END)

        dirs_to_use = self.denoised_dirs if self.quality_threshold else self.dirs

        for dir in dirs_to_use: # Goes through every directory
            files = []
            data_directory = os.path.basename(dir)
            for file in os.listdir(os.path.join(self.nested_dir, dir)):
                if file.endswith(".fastq"):
                    file_path = os.path.join(self.nested_dir, dir, file)
                    print(f"Currently processing {file} ({mani.fastq_file_size(file_path)})")
                    if self.capsid_file:
                        if self.mismatches:
                            instance.count_known_reads(peptide_map, file_path, data_directory)
                        else:
                            instance._cpp_fuzzy_match(peptide_map, file_path, data_directory, 0, subOnly=True)
                    else:
                        if self._run_flank:
                            instance.search_by_flank(upstream, downstream, file_path, data_directory)
                        else:
                            instance._cpp_filter_count(data_directory, file_path, self.ref_seq)
                    print(f"Finished {file}")
                    files.append(file)
                    spreadsheet_instance.save_file(instance.pkl_file_path, file, data_directory, instructions_link)
            if len(files) > 1:
                avg_file = instance.create_avg_pkl(data_directory, files, instructions_link)
                print(f"Created average pkl/xlsx: {data_directory}")
                spreadsheet_instance.save_file(instance.pkl_file_path, avg_file, data_directory, instructions_link, avg_file=True)
            if self.enrichment_file:
                print(self.enrichment_file)
                avg_enrichment_file = enrichment_instance.calc_enrichment(self.enrichment_file, session_folder, files, data_directory, instructions_link)
                print(f"Calculated enrichment: {data_directory}")
                spreadsheet_instance.save_file(instance.pkl_file_path, avg_enrichment_file, data_directory, instructions_link, avg_file=True)
                print(f"Created average enrichment pkl/xlsx: {data_directory}")
            if self.bubble:
                gen_bubble_plots(self.bubble_dir, session_folder, data_directory, instance._cache_folder)
                print(f"Created bubble charts: {data_directory}")
            if self.freq_distribution:
                gen_bio_graphs(self.freq_dir, session_folder, data_directory, instance._cache_folder)
                print(f"Created frequency distribution charts: {data_directory}")
            
        instance._serialize_pkl()
        if self.args.output:
            instance.save_to_output(self.output_dir)

def main():
    args = parser.parse_args()
    cap_genie(args).run_pipeline()
    
if __name__ == "__main__":
    main()