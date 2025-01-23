import xml.etree.ElementTree as ET
import numpy as np
import scipy.io as sio
from pathlib import Path


import xml.etree.ElementTree as ET

def load_xml(file_path):
    """
    Load XML and extract data for channel map creation.

    Parameters
    ----------
    file_path : str
        Path to the XML file.

    Returns
    -------
    dict
        Parsed data containing channel groups with classified channels.
    xml_tree
        Parsed XML tree.
    """

    tree = ET.parse(file_path)
    root = tree.getroot()

    # Parse channel groups from anatomicalDescription
    channel_groups = []
    
    # Extract groups from anatomicalDescription
    for group in root.findall(".//anatomicalDescription/channelGroups/group"):
        channels = []
        skipped_channels = []

        for ch in group.findall("channel"):
            channel_number = int(ch.text)
            skip_value = ch.get("skip", "0")  # Default to "0" if attribute is missing
            
            if skip_value == "0":
                channels.append(channel_number)
            elif skip_value == "1":
                skipped_channels.append(channel_number)

        channel_groups.append({
            "Channels": channels,
            "SkippedChannels": skipped_channels
        })

    return {"ChannelGroups": channel_groups}, root


def create_channel_map_file(basepath=None, basename=None, electrode_type=None, reject_channels=None):
    """
    Create a channel map file for neural recordings and save it as a .mat file.

    Parameters
    ----------
    basepath : str, optional
        Directory path where the XML and channel map will be stored.
        If None, the current working directory is used.
    basename : str, optional
        Name of the base file without extension.
        If None, the stem of the basepath is used.
    electrode_type : str, optional
        Type of electrode ('staggered', 'neurogrid', 'poly3', 'poly5', etc.).
        If None, the electrode type is inferred from the XML file.
    reject_channels : list of int, optional
        List of channel indices to exclude from the channel map.
        If None, no channels are excluded.

    Returns
    -------
    dict
        A dictionary containing the following keys:
        - 'n_groups' : int, Number of channel groups.
        - 'n_chan' : int, Total number of unique channels.
        - 'sampling_freq' : float, Sampling frequency in Hz (extracted from the XML file).
        - 'electrode_type' : str, Electrode type (e.g., 'staggered', 'neurogrid').
        - 'hor_dist' : float, Horizontal distance between adjacent electrodes in microns.
        - 'vert_dist' : float, Vertical distance between adjacent electrodes in microns.

    Notes
    -----
    - The function reads the electrode type and sampling rate from the XML file if not provided.
    - The channel map is saved as a .mat file in the specified basepath.
    - The function supports the following electrode types:
        - 'staggered': Staggered probe layout.
        - 'neurogrid': Neurogrid probe layout.
        - 'poly3', 'poly5': Poly3 and Poly5 probe layouts (not fully tested).
    - Rejected channels are marked as disconnected in the channel map.
    - The channel map file ('chanMap.mat') contains the following variables:
        - 'chanMap': 1-based channel map.
        - 'connected': Boolean array indicating whether each channel is connected.
        - 'xcoords': X-coordinates of the channels.
        - 'ycoords': Y-coordinates of the channels.
        - 'kcoords': Group indices for each channel.
        - 'chanMap0ind': 0-based channel map.

    Raises
    ------
    FileNotFoundError
        If the XML file is not found in the specified basepath.
    ValueError
        If the electrode type is not supported or not found in the XML file.
    """
    if basepath is None:
        basepath = Path.cwd()
    else:
        basepath = Path(basepath)

    if basename is None:
        basename = basepath.stem

    if reject_channels is None:
        reject_channels = []


    xml_path = basepath / f"{basename}.xml"

    # Check if the XML file exists
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    # Load XML data
    par, xml_tree = load_xml(xml_path)

    # Determine electrode type from XML if not provided
    if electrode_type is None:
        try:
            xml_electrode_type = xml_tree.find(".//ElectrodeType").text
            electrode_type = xml_electrode_type.lower()
        except AttributeError:
            electrode_type = 'staggered'  # Default to staggered if not found

    # Extract channel groups
    channel_groups = par["ChannelGroups"]
    tgroups = [grp["Channels"] for grp in channel_groups]
    n_groups = len(tgroups)

    # Generate xcoords and ycoords based on electrode type
    xcoords, ycoords = [], []
    for g, tchannels in enumerate(tgroups):
        if electrode_type == 'staggered':
            x = []
            y = []
            for i in range(len(tchannels)):
                x.append(-20 if (i + 1) % 2 == 1 else 20)
                y.append(-i * 20)
            x = [xi + g * 200 for xi in x]
            hor_dist = 40
            vert_dist = 40

        elif electrode_type == 'neurogrid':
            x = []
            y = []
            for i in range(len(tchannels)):
                x.append(len(tchannels) - i)
                y.append(-i * 30)
            x = [xi + g * 30 for xi in x]
            hor_dist = 30
            vert_dist = 30

        elif electrode_type in ['poly3', 'poly5']:
            print("Poly3 and poly5 electrodes not tested for python wrapper ks4, please check the mapping works as intended.")
            poly_num = 3 if electrode_type == 'poly3' else 5
            x = [None] * len(tchannels)
            y = [None] * len(tchannels)
            extrachannels = len(tchannels) % poly_num
            polyline = [i % poly_num for i in range(len(tchannels) - extrachannels)]

            for i, val in enumerate(polyline):
                if val == 1:
                    x[i + extrachannels] = -18
                elif val == 2:
                    x[i + extrachannels] = 0
                elif val == 0:
                    x[i + extrachannels] = 18

            for i in range(len(tchannels)):
                if x[i] == 18:
                    y[i] = -(i // poly_num) * 20
                elif x[i] == 0:
                    y[i] = -(i // poly_num) * 20 - 10 + extrachannels * 20
                elif x[i] == -18:
                    y[i] = -(i // poly_num) * 20

            for i in range(extrachannels):
                x[i] = 0

            x = [xi + g * 200 for xi in x]
            hor_dist = ""
            vert_dist = ""

        else:
            raise ValueError(f"Electrode type {electrode_type} not supported.")

        xcoords.extend(x)
        ycoords.extend(y)

    # Create channel map
    all_channels = [ch for grp in tgroups for ch in grp]  # Flatten all channels
    unique_channels = sorted(set(all_channels))  # Unique sorted channels
    Nchannels = len(unique_channels)  # Total number of unique channels

    # Initialize arrays
    kcoords = np.zeros(Nchannels, dtype=int)  # Initialize kcoords with zeros
    connected = np.ones(Nchannels, dtype=bool)  # All channels are connected by default
    chan_map = np.arange(1, Nchannels + 1)  # 1-based channel map
    chan_map0ind = chan_map - 1  # 0-based channel map

    # Assign kcoords based on group membership
    for g, tgroup in enumerate(tgroups, start=1):
        for ch in tgroup:
            idx = unique_channels.index(ch)  # Find the index of the channel in unique_channels
            kcoords[idx] = g  # Assign the group index as kcoord

    # Mark rejected channels as disconnected
    for ch in reject_channels:
        if ch in unique_channels:
            idx = unique_channels.index(ch)
            connected[idx] = False

    # Sort xcoords and ycoords by unique channel order
    xcoords = np.array(xcoords)[np.argsort(all_channels)][np.argsort(unique_channels)]
    ycoords = np.array(ycoords)[np.argsort(all_channels)][np.argsort(unique_channels)]

    # Save to .mat file
    mat_data = {
        'chanMap': chan_map,
        'connected': connected,
        'xcoords': xcoords,
        'ycoords': ycoords,
        'kcoords': kcoords,
        'chanMap0ind': chan_map0ind
    }
    sio.savemat(basepath / 'chanMap.mat', mat_data)
    print("Channel map saved to", basepath / 'chanMap.mat')
    n_chan = len(x)
    try:
        sampling_freq = xml_tree.find(".//samplingRate")
        if sampling_freq is not None:
            sampling_freq = float(sampling_freq.text)  # Convert text to float
        else:
            raise ValueError("samplingRate element not found in the XML file.")
    except Exception as e:
        print(f"Error reading sampling rate from .xml file: {e}")
    try:
        data_type = xml_tree.find(".//nBits")
        if data_type is not None:
            data_type = int(data_type.text)
            if data_type == 16:
                data_type = "int16"
            elif data_type == 32:
                data_type = "int32"
            else:
                print("Unknown data type: {data_type}")
        else:
            raise ValueError("data type element not found in the XML file.")
    except Exception as e:
        print(f"Error reading sampling rate from .xml file: {e}")
    try:
        settings = {"n_groups": n_groups,
                    "n_chan": Nchannels,
                    "sampling_freq": sampling_freq,
                    "electrode_type": electrode_type,
                    "hor_dist": hor_dist,
                    "vert_dist": vert_dist,
                    }
    except Exception as e:
        print(f"Error creating settings dictionary: {e}")
    return settings, data_type