import os
import glob
import spikeinterface.extractors as se
import spikeinterface as si

def concatenate(path, xml_file_name):
    """
    Check if there are more than one .dat file, if so, concatenates them into a single SpikeInterface recording and save it to the basepath.

    Parameters
    ----------
    path : str
        Path to the directory containing .dat files.
    xml_file_name : str
        Name of the .xml file (e.g., "recording.xml").

    Raises
    ------
    FileNotFoundError
        If no .dat files are found in the specified path.
    """
    basepath = path
    dat_files = glob.glob(os.path.join(basepath, '**', '*amplifier.dat'), recursive=True)
    
    if not dat_files:
        raise FileNotFoundError(f"No .dat files found in {basepath}")
    elif len(dat_files) == 1:
        return False
    
    
    xml_path = os.path.join(basepath, xml_file_name)
    
    # Sort files based on the last four digits in the folder name
    dat_files.sort(key=lambda x: int(os.path.basename(os.path.dirname(x)).split('_')[-1]))
    
    recording = []
    for f in dat_files:
        recording.append(se.neuroscope.NeuroScopeRecordingExtractor(file_path=f, xml_file_path=xml_path))
    
    concatenated_recording = si.concatenate_recordings(recording)
    
    # Check if the output file already exists
    output_path = os.path.join(basepath, 'concatenated_recording.dat')
    if os.path.exists(output_path):
        user_input = input(f"The file '{output_path}' already exists. Do you want to overwrite it? (y/n): ")
        if user_input.lower() != 'y':
            return False
    
    # Save the concatenated recording to disk using write_binary_recording
    si.core.write_binary_recording(
        recording=concatenated_recording,
        file_paths=output_path,
        progress_bar=True)  # Progress bars are cool
    print("Concatenated recording saved")
    return True