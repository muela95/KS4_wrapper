import sys
import os
from pathlib import Path
from Functions.create_map import load_xml, create_channel_map_file
from Functions.manage_xmls import find_xml_files, prompt_user_for_xml_file
from Functions.concatenate_dats import concatenate
from Functions.kilosort import kilosort_options
from Functions.kilosort import kilosort_run
from Functions.find_and_load_session_mat import findAndLoadSessionMat, extractSessionData, validate_session_structure, extractSessionData
from kilosort import io


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
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    # Error if there are too many argumenst
    if len(sys.argv) > 2:
        print("Usage: python main.py [<folder_path>]")
        sys.exit(1)
    
    # Get folder from argument or default to current directory
    elif len(sys.argv) < 2:
        folder_path = os.getcwd()

    else:
        folder_path = sys.argv[1]
        print("Path provided")
        # Check if it's a valid folder path
        if not Path(folder_path).is_dir():
            print(f"Error: {folder_path} is not a directory!")
            sys.exit(1)
        else:
            print("Valid directory, proceeding")

    print("Looking for .xml files...")
    xml_files = find_xml_files(folder_path)

    # How many xml files are there? If none, give error, if one, use it, if more than one open selection menu
    if not xml_files:
        print(f"No .xml files found in {folder_path}")
    elif len(xml_files) > 1:
        selected_xml_file = prompt_user_for_xml_file(xml_files)
    else:
        print(f"Using only xml file found, {xml_files[0]}")
        selected_xml_file = xml_files[0]

    try:
        session, dataReader = findAndLoadSessionMat(folder_path)
    except KeyError as e:
        print(f"Session can't be loaded,{e}")
    try:
        structure = validate_session_structure(session)
    except KeyError as e:
        print(f"Session does not have the necessary fields, {e}")

    if session is not None and structure == True:
        print("Session file loaded successfully")
        chanMap, xc, yc, kcoords, nChan, sampleRate, badChannels = extractSessionData(session, dataReader)
        probe = {
            'chanMap': chanMap,
            'xc': xc,
            'yc': yc,
            'kcoords': kcoords,
            'n_chan': nChan
        }
        settings = {'n_chan_bin': probe['n_chan'], 'fs': sampleRate}
        use = "session"
    else:
        print("Session is either not present or does not have the required fields. Trying to use .xml file")
        use = "xml"
        # Find all .xml files for mapping
     
        print(f"Using this .xml file: {selected_xml_file}")

        channel_groups_data, _ = load_xml(selected_xml_file)
        exclude_channels = []
        for group in channel_groups_data["ChannelGroups"]:
            exclude_channels.extend(group["SkippedChannels"])

        print("Excluded Channels:", exclude_channels)
        # Create channel map for the selected .xml file, prompt error if something wrong happens
        try:
            info, data_type = create_channel_map_file(basepath=folder_path, basename=selected_xml_file.stem)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Generating settings for KS4
        os.chdir(folder_path)
        probe = io.load_probe("chanMap.mat")
        settings = kilosort_options(folder_path, info["sampling_freq"], info["n_chan"]+ len(exclude_channels), 
                                    info["n_groups"], info["hor_dist"], info["vert_dist"], 
                                    info["electrode_type"])
    
    for key, value in settings.items():
        print(f"{key}, {value}")

    # Concatenate .dats files
    concatenation_successful, grandparent_folder = concatenate(folder_path, selected_xml_file)
    if not concatenation_successful:
        print("Concatenation skipped")
        filename = grandparent_folder + ".dat"
    else:
        filename="concatenated_recording.dat"

    kilosort_run(folder_path, settings, data_type, probe, filename=filename)


if __name__ == "__main__":
    main()
