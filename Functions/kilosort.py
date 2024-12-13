from kilosort import run_kilosort, io
import os
import torch
from math import sqrt



def kilosort_options(basepath, sampling_freq, n_chan, n_groups, hor_dist, vert_dist, electrode_type):
    """
    Generate Kilosort configuration settings based on probe geometry and user inputs.

    Parameters
    ----------
    basepath : str
        Path to the data directory.
    sampling_freq : float
        Sampling frequency of the recording in Hz.
    n_chan : int
        Number of channels in the probe.
    n_groups : int
        Number of channel groups for block processing.
    hor_dist : float
        Horizontal distance between adjacent electrodes in microns.
    vert_dist : float
        Vertical distance between adjacent electrodes in microns.
    electrode_type : str
        Type of electrode array (e.g., "staggered", "neurogrid", "poly3", "poly5").

    Returns
    -------
    dict
        A dictionary containing all Kilosort configuration settings, including:
        - nt : Number of timepoints for spike detection.
        - n_chan_bin : Number of channels for binning.
        - batch_size : Size of data batches in samples.
        - dmin : Minimum vertical distance for clustering.
        - dminx : Minimum horizontal distance for clustering.
        - data_dir : Path to the data directory.
        - probe_name : Name of the probe channel map file.
        - min_template_size : Minimum template size in microns.
        - nblocks : Number of blocks for processing.
        - acg : Autocorrelogram threshold for labeling clusters.
        - ccg : Crosscorrelogram threshold for merging clusters.

    Notes
    -----
    - The function calculates the minimum template size based on the electrode type and geometry.
    - User inputs for autocorrelogram (acg) and crosscorrelogram (ccg) thresholds are collected interactively.
    """

    # Initialize the settings dictionary
    settings = {}

    # Pre-defined settings
    settings["nt"] = int(sampling_freq / 500 + 1)  # 30kHz 2ms should have a nt of 61
    settings["n_chan_bin"] = int(n_chan)
    settings["batch_size"] = int(3 * sampling_freq)
    settings["dmin"] = int(vert_dist)
    settings["dminx"] = int(hor_dist)
    settings["data_dir"] = basepath
    settings["probe_name"] = "chanMap.mat"


    # Determine min_template_size based on electrode type
    if electrode_type == "staggered":
        # For staggered probes, use half the diagonal distance
        settings["min_template_size"] = sqrt(hor_dist ** 2 + vert_dist ** 2) / 2
    elif electrode_type == "neurogrid":
        settings["min_template_size"] = 15
    elif electrode_type in ["poly3", "poly5"]:
        settings["min_template_size"] = float(input("Electrode type not tested, set half of the diagonal distance manually: "))

    # Determine nblocks
    if n_chan < 64:
        settings["nblocks"] = 0
    else:
        settings["nblocks"] = n_groups

    # Collect user inputs for acg and ccg
    while True:
        try:
            acg = input("Autocorrelogram threshold, maximum percentage of ISI violations to label a cluster good/mua. Leave blank for default 0.2: ")
            if acg == "":
                settings["acg_threshold"] = 0.2
            else:
                settings["acg_threshold"] = float(acg)

            ccg = input("Crosscorrelogram threshold, maximum percentage of ISI violations allowed for merging clusters. Leave blank for default 0.25, lower this if you find overmerging of clusters: ")
            if ccg == "":
                settings["ccg_threshold"] = 0.25
            else:
                settings["ccg_threshold"] = float(ccg)

            # Return the settings dictionary
            return settings

        except ValueError:
            print("Invalid input. Please enter a number or leave blank.")

def kilosort_run(path, settings, data_type):
    # Set the working directory and probe file
    os.chdir(path)
    probe = io.load_probe("chanMap.mat")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(device)
    try:
        run_kilosort(settings=settings, probe=probe, data_dtype=data_type)
    except Exception as e:
        print(f"Error encountered: {e}")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(device)
