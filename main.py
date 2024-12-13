import sys
from pathlib import Path
from Functions.create_map import load_xml, create_channel_map_file
from Functions.manage_xmls import find_xml_files, prompt_user_for_xml_file
from Functions.concatenate_dats import concatenate
from Functions.kilosort import kilosort_options
from Functions.kilosort import kilosort_run


def main():
    """
    Main function to orchestrate the pipeline for creating a channel map, concatenating .dat files,
    and running Kilosort.

    Parameters
    ----------
    folder_path : str
        Path to the directory containing the data and .xml files.

    Raises
    ------
    SystemExit
        Exits the program if the provided folder path is invalid or if an error occurs during processing.
    """
    # Check if a path is provided, give instructions if not
    if len(sys.argv) != 2:
        print("Usage: python main.py <folder_path>")
        sys.exit(1)
    
    # Get folder from argument
    folder_path = sys.argv[1]

    # Check if it's a valid folder path
    if not Path(folder_path).is_dir():
        print(f"Error: {folder_path} is not a directory!")
        sys.exit(1)
    else:
        print("Valid directory, proceeding")

    # Find all .xml files for mapping
    xml_files = find_xml_files(folder_path)

    # How many xml files are there? If none, give error, if one, use it, if more than one open selection menu
    if not xml_files:
        print(f"No .xml files found in {folder_path}")
    elif len(xml_files) > 1:
        selected_xml_file = prompt_user_for_xml_file(xml_files)
    else:
        selected_xml_file = xml_files[0]

    print(f"Using the following .xml file: {selected_xml_file}")

    # Create channel map for the selected .xml file, prompt error if something wrong happens
    try:
        info, data_type = create_channel_map_file(basepath=folder_path, basename=selected_xml_file.stem)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Concatenate .dats files
    concatenation_successful = concatenate(folder_path, selected_xml_file)
    if not concatenation_successful:
        print("Concatenation skipped")

    # Generating settings for KS4
    for key, value in info.items():
        print(f"{key}, {value}")
    settings = kilosort_options(folder_path, info["sampling_freq"], info["n_chan"], info["n_groups"], info["hor_dist"], info["vert_dist"], info["electrode_type"])
    kilosort_run(folder_path, settings, data_type)


if __name__ == "__main__":
    main()
