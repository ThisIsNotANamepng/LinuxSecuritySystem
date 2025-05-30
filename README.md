# Linux Security Center

I want to build a good AV for Linux, but it needs to follow some good design goals which follow Linux principles

- Needs to get out of the way
- Focus on intelligent, important features and minimal bloat
- Scriptable

To that end, I think it should have the following tools

- ClamAV powered antivirus
- Process scanning (ML with those datasets)
    - Could learn based on the user’s behavior, alert when unusual behavior happens
    - Could make our own damn dataset, UNSW-NB15 has ~920000 benign and ~110000 malicious traces
        - We could have the cyber club attack a box
            - Maybe even for malware night
- Take a command and try to predict what will happen to the system
    - Should do de-obsfucation
    - Could take a bash script
        - For example, when a software needs to be installed with a bash script the tool could scan it to find anything malicious
- System Attestation, check binary file hashes against an api with known good hashes
- Basic network analysis, search every foreign address the system connects to against a threat feed of bad ips/domains

And also

- Should also be options to turn any of the above tools on/off
- Should be able to run and be useful without root

Note: This is not a security scanner, it is not for finding all security flaws within a system. There are tools such as Lynis for that. This tool is only meant to include some features which detect continuous threats to a typical desktop system

## ClamAV Frontend

### Updating signatures

`freshclam` needs root to run, so unless we can get a window to open just to get root for that (which I can't figure out) I think the best option is to maintain our own feed which is downloaded and used instead of the clamav feed. I don't like it, but I think it's the only way. It can be stored on the central server, and be base don the actual clamav feed + yarify from abuse.ch

Note: With `clamscan --version` you get smething like: ClamAV 1.4.2/27649/Mon May 26 03:31:06 2025, this is ClamAV Version/threat feed database version (increments by 1 every update)/Last time the database was updated on their end. If we could find where they say the current database version, we could check for out of date local version

## Binary Attestation

### Local database

When you redraw the gui you don't want to re-check every binary against the api because the binaries are unlikely to have changed. It would be more efficient to cache a local database with all of the binaries that have been checked and the result of the check

## To Install

### Linux

1. Make a new Python virtual environment (optional but highly encouraged): `python3 -m venv env` and activate `source env/bin/activate`

2. Install Python requirments: `pip install -r requirements.txt`

3. Install ClamAV: `sudo <package-manager> install clamav`

4. Run `cd gui`, `python3 main.py`

### Windows

Switch to Linux

## TODO:

[ ] Find a better threat feed for urls, I think they can be smaller and more specific to these needs, also I think this feeds might only be for malware distribution and not contain things like c&c servers (https://urlhaus.abuse.ch/api/#csv)
[ ] You can only get the ip addresses of foreign connections, not domains. Some (I'm assuming) urls are on the threat feed but not the ip addresses of those domains, so they aren't detected. We need to resolve the domains on the list to ips or the ips on the system to domains. It would probably be easiest to do this on the doanload server for the threat feeds (I'm assuming there will be a server controlled by me for this)
[ ] Should network monitoring include ipv6? Right now it doesn't
[ ] I want the ClamAV scanning to run a different color circle as it loads the signatures
[ ] When clamav scanning is running, the progress % text line should be in the middle of the circle
[ ] When scanning a directory less than 1000 files the logic is wrong I think. When I scanned a smaller dir the circle didn't fill up all the way

#### Progress:

[x] ClamAV functions
[ ] Process scanning model
[ ] Process continuous scanning
[ ] System command testing
[ ] Make a good de-obsfucator
[x] Binary attestation client
[ ] Binary attestation server
[ ] Network monitoring

[ ] Process scanning GUI
[ ] ClamAV GUI
[ ] Command testing GUI
[ ] Binary attestation GUI
[ ] Network monitoring GUI
