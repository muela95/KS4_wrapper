import os
from pathlib import Path

def find_xml_files(folder_path):
    """
    Find all .xml files in the specified folder.

    Parameters
    ----------
    folder_path : str
        Path to the folder to search.

    Returns
    -------
    list
        List of Path objects for .xml files.
    """
    xml_files = list(Path(folder_path).glob("*.xml"))
    return xml_files

def prompt_user_for_xml_file(xml_files):
    """
    Prompt the user to choose one .xml file from a list.

    Parameters
    ----------
    xml_files : list
        List of Path objects for .xml files.

    Returns
    -------
    Path
        The selected .xml file.
    """
    
    if len(xml_files) == 1:
        return xml_files[0]

    print("Multiple .xml files found:")
    for i, xml_file in enumerate(xml_files):
        print(f"{i + 1}: {xml_file.name}")

    while True:
        try:
            choice = int(input("Enter the number of the .xml file you want to use: "))
            if 1 <= choice <= len(xml_files):
                return xml_files[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")