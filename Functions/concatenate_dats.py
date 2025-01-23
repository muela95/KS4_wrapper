import os
import glob
import shutil
import spikeinterface as si
import spikeinterface.extractors as se

def concatenate(path, xml_file_name):
    """
    Check if there are one or more .dat files in the specified path. 
    If only one .dat file is found, it is copied and renamed based on its parent folder. 
    If multiple .dat files are found, they are concatenated into a single SpikeInterface recording and saved to the basepath.

    Parameters
    ----------
    path : str
        Path to the directory containing .dat files.
    xml_file_name : str
        Name of the .xml file (e.g., "recording.xml"), required for NeuroScopeRecordingExtractor.

    Returns
    -------
    bool
        True if concatenation was performed, False if only a single file was handled.
    str
        Name of the parent folder containing the .dat files.

    Raises
    ------
    FileNotFoundError
        If no .dat files are found in the specified path.
    """

    basepath = path
    dat_files = glob.glob(os.path.join(basepath, '**', '*amplifier.dat'), recursive=True)
    print(dat_files)
    
    if not dat_files:
        raise FileNotFoundError(f"No .dat files found in {basepath}")
    
    elif len(dat_files) == 1:
        print("Only one .dat file found.")
        single_file = dat_files[0]  # Get the single file path
        parent_folder = os.path.dirname(single_file) # Get the parent folder name
        grandparent_folder = os.path.basename(os.path.dirname(parent_folder))  # Grandparent folder name
        new_file_name = f"{grandparent_folder}.dat"  # Create the new file name based on the folder name
        new_file_path = os.path.join(basepath, new_file_name)

        # Check if the copied file already exists
        if os.path.exists(new_file_path):
            print(f"Warning: The file '{new_file_path}' already exists.")
            user_input = input("Do you want to use the existing file? (y/n): ").strip().lower()
            if user_input == 'y':
                print(f"Using the existing file: {new_file_path}")
                return False, grandparent_folder  # Exit without copying or overwriting
            else:
                print("Overwriting the existing file.")

        # Copy the single .dat file to the new location
        shutil.copy(single_file, new_file_path)
        print(f"File copied to: {new_file_path}")
        return False, grandparent_folder  # Exit after handling a single .dat file
    
    # If more than one .dat file exists, proceed with concatenation
    xml_path = os.path.join(basepath, xml_file_name)
    
    # Sort files based on the last four digits in the folder name
    dat_files.sort(key=lambda x: int(os.path.basename(os.path.dirname(x)).split('_')[-1]))
    print(f"Found {len(dat_files)} .dat files: {dat_files}")
    
    recording = []
    for f in dat_files:
        recording.append(se.neuroscope.NeuroScopeRecordingExtractor(file_path=f, xml_file_path=xml_path))
    
    concatenated_recording = si.concatenate_recordings(recording)
    
    # Define parent_folder for consistency across all code paths
    parent_folder = os.path.dirname(dat_files[0])  # Use parent folder of first .dat file
    grandparent_folder = os.path.basename(os.path.dirname(parent_folder))  # Grandparent folder name

    # Check if the output file already exists
    output_path = os.path.join(basepath, 'concatenated_recording.dat')
    if os.path.exists(output_path):
        user_input = input(f"The file '{output_path}' already exists. Do you want to overwrite it? (y/n): ").strip().lower()
        if user_input != 'y':
            print("Operation canceled. Existing concatenated recording will be used.")
            return True, grandparent_folder
    
    # Save the concatenated recording to disk using write_binary_recording
    si.core.write_binary_recording(
        recording=concatenated_recording,
        file_paths=output_path,
        progress_bar=True)  # Progress bars are cool
    
    print("Concatenated recording saved.")
    return True, grandparent_folder
