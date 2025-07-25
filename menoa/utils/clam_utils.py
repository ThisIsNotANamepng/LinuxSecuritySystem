import subprocess
import shutil
import os
from typing import List, Tuple, Optional
from datetime import datetime
import tomli, tomli_w
from pathlib import Path
import requests

import utils

def is_clamscan_available() -> bool:
    """Check if clamscan is installed and available in PATH."""
    return shutil.which("clamscan") is not None

def is_freshclam_available() -> bool:
    """Check if freshclam (database updater) is installed."""
    return shutil.which("freshclam") is not None

def scan_path(path: str, recursive: bool = True) -> Tuple[bool, List[Tuple[str, str]]]:
    """
    Scan a file or directory using clamscan.
    
    Returns a tuple (success, results), where results is a list of (filename, result) tuples.
    """
    if not is_clamscan_available():
        return False, [("ERROR", "clamscan not found in PATH.")]

    if not os.path.exists(path):
        return False, [("ERROR", f"Path not found: {path}")]

    cmd = ["clamscan"]
    if recursive:
        cmd.append("-r")
    cmd.append(path)

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        # clamscan exits with non-zero status if infection is found
        output = e.stdout
    else:
        output = process.stdout

    results = parse_clamscan_output(output)
    return True, results

def scan_path_streaming(path: str, recursive: bool = True):
    """
    Generator that streams clamscan output line-by-line.
    Yields (filename, result) as they're found.
    """
    if not is_clamscan_available():
        print("Clam error")
        yield ("ERROR", "clamscan not found in PATH.")
        return

    if not os.path.exists(path):
        print("path error")
        yield ("ERROR", f"Path not found: {path}")
        return

    cmd = ["clamscan"]

    if recursive:
        cmd.append("-r")
    cmd.append(path)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        if ": " in line:
            file, result = line.strip().rsplit(": ", 1)
            yield (file, result)

def get_clamav_version() -> Optional[str]:
    """Return the version of clamscan if available."""
    if not is_clamscan_available():
        return None

    try:
        result = subprocess.run(["clamscan", "-V"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_database_version():
    # Returns the database patch version and when it was last changed

    full = get_clamav_version().split("/")

    return (full[1], full[2])

def get_last_time_scanned():
    # Returns the last time the system was scanned, found in /gui/data/last_scanned

    last_scanned = ""

    with open("data/last_scanned", "r") as file:
        last_scanned = file.read()

    return last_scanned

def set_last_time_scanned():
    # Updates the last time the system was scanned, found in /gui/data/last_scanned

    with open("data/last_scanned", "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))

def get_scan_total(path):
    total = 0
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    total += 1
                elif entry.is_dir(follow_symlinks=False):
                    total += get_scan_total(entry.path)
    except PermissionError:
        pass  # Skip folders/files we can't access
    return total
    
def update_all_feeds():

    with open(str(Path.home())+"/.menoa/config.toml", "r") as file:
        config = file.read()

    toml_dict = tomli.loads(config)

    for i in toml_dict['clam_feeds'].keys():
        update_feed(i)


def update_feed(index):
    """
    Updates a feed using the given index which could be a title (as in the "default_daily" in [clam_feeds.default_daily] from the config)
    """

    with open(str(Path.home())+"/.menoa/config.toml", "r") as file:
        config = file.read()

    toml_dict = tomli.loads(config)

    try:
        feed = (toml_dict["clam_feeds"][index])
    except KeyError:
        raise Exception("Error: Feed does not exist")

    utils.progress_download(feed['url'], feed["local_path"].replace("~", str(Path.home())))

    #response = requests.get(feed['url'])

    #with open(feed["local_path"].replace("~", str(Path.home())), "wb") as file:
    #    file.write(response.content)

    return feed

def add_feed(index, name, url, description, local_path, supports_versioning=False, move_into_default_feed_path=True):
    """
    Adds a clam feed from the config
    if `move_into_default_feed_path` is True Menoa will try to copy the given filepath into `~/.menoa/feeds/xxxx``
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    if index in config["clam_feeds"].keys():
        raise Exception("Error: Feed with index", index, "already exists. This identifier must be unique")

    if move_into_default_feed_path: # Copy filepath into local feed storage
        new_path = str(Path.home())+"/.menoa/feeds/"+Path(local_path).name
        shutil.copy2(local_path, new_path)
        local_path = new_path

    config["clam_feeds"][index] = {
        "url": url,
        "name": name,
        "description": description,
        "local_path": local_path,
        "last_refreshed": "1970-01-01T00:00:00",
        "supports_versioning": supports_versioning
    }

    with open(str(Path.home())+"/.menoa/config.toml", "wb") as f:
        tomli_w.dump(config, f)

def remove_feed(index):
    """
    Removes a clam feed from the config
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    if index not in config["clam_feeds"].keys():
        raise Exception("Given feed index not found in config")

    config["clam_feeds"].pop(index)

    with open(str(Path.home())+"/.menoa/config.toml", "wb") as f:
        tomli_w.dump(config, f)

def list_feeds():
    """
    Returns a dictionary with all of the clam feeds
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    return config["clam_feeds"]

def get_delay():
    """
    Returns the delay for scanning
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    return config["clamav"]

def set_scanning_delay(seconds):
    """
    Sets the delay for scanning
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    config["clamav"]["scan_delay"] = seconds

    with open(str(Path.home())+"/.menoa/config.toml", "wb") as f:
        tomli_w.dump(config, f)


def set_feed_refresh_delay(seconds):
    """
    Sets the delay for refresh
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    config["clamav"]["feed_update_delay"] = seconds

    with open(str(Path.home())+"/.menoa/config.toml", "wb") as f:
        tomli_w.dump(config, f)
        
def toggle(status=None):
    """
    Toggles scanning, reverses current status if nothing is passed
    """

    with open(str(Path.home())+"/.menoa/config.toml", "rb") as f:
        config = tomli.load(f)

    current = config["clamav"]["enabled"]

    if status is None:
        config["clamav"]["enabled"] = not current
    else:
        config["clamav"]["enabled"] = status

    with open(str(Path.home())+"/.menoa/config.toml", "wb") as f:
        tomli_w.dump(config, f)

    if status is None: return not current
    else: return status