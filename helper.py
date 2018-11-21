import json

VERSION = '1.2'


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


status = color.BOLD + color.PURPLE + "[STATUS] " + color.END
usage = color.BOLD + color.YELLOW + "[USAGE] " + color.END
error = color.BOLD + color.RED + "[ERROR] " + color.END


def bold_blue(txt):
    return color.BOLD + color.BLUE + txt + color.END

def bold_purple(txt):
    return color.BOLD + color.PURPLE + txt + color.END

def load_json(path):
    """Opens a json file and returns the content as a python dictonary.

    Parameters:
        path(str): Path of json file
    """
    if not path.lower().endswith('.json'):
        raise ValueError("Wrong file format!")
    with open(path) as f:
        return json.load(f)
