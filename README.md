# BCollector

- Download files from a http, https or sftp server into your local infrastructure.
- Copy or decrypt files to destination directory.
- Keep backup in the download folder for a given period of time, delete obsolete files.
- Works as daemon / in an andless loop.

## Requirements
Python 3.12 works fine. Newer versions should be no problem.

In addition to the standard libraries python-gnupg and paramiko are required:

```
python -m pip install python-gnupg py7zr paramiko
```
In case your download machine is offline, download the libraries on an online system:

```
python -m pip download python-gnupg py7zr paramiko
```
Transport the .whl files to the offline machine and execute:
```
python -m pip install --no-index --find-links .\ python-gnupg paramiko
```

## Configuration
Bcollector reads the configuration from one file. As configparser is used, INI file syntax is used. The default is
`bcollector.conf` in the directory of `bcollector.py`.

### Example:
```
[REMOTE]
# remote location (url) to sync to
#url = https://example.org/
url = http://example.org:8080/
#url = sftp://user@example.org/
#password for sftp
#password = dummy
# regular expression to select targetted files
match = *
#match = .*\.7z
#match = .*\.gpg
#match = ^[^.].*
# timout connection attempt in seconds
timeout = 30
# maximumretries on bad download attempts
retries = 10
# delay in seconds after bad download attempt
delay = 2
# pgp to decrypt pgp/gpg files with synmmetric password, 7z tp unpack/decrypt 7zip files or none to disable decryption
encryption = pgp
#encryption = none
# passphrase to decrypt
passphrase = dummy

[LOCAL]
# download directory (used to sync/check for new files)
download = /home/user/Download
# destination directory to copy files to, decrypt on the way if set
destination = /home/user/Public
# log file
logfile = /home/user/Logging/bcollector_log.txt
# max. size of log file in MiB
logsize = 32
# database to track files
db = /home/user/.bcollector/files.db
# set yes to delay forwarding until destination directory does not exist
wait = yes
# trigger file name to write into destination directory
trigger = /home/neo/Public/test_trigger.txt
# minutes to keep files in download directory
keep_files = 1
# minutes to keep entries in data base
keep_entries = 2

[LOOP]
# enable endless loop with yes
enable = no
# hours of the day (every = every hour)
# hours = 0, 3, 9, 12, 15, 18, 21
hours = every
# minutes of the hour when to start download attempt (every = every minute)
#minutes = 8,18,28,38,48,58
minutes = every
```
### REMOTE
If the source files are hosted on a HTTP or HTTPS server, the configuration needs
```
url = http://example.org:8080/
```
or
```
url = https://example.org/
```
in the config file. For the SFTP protocoll the url is given in the following syntax:
```
url = sftp://user@example.org/
password = topsecret
```
The files can be selected by a regular expression. The entry
```
match = .*\.7z
```
would copy/synchronize all files with extension `.7z`,
```
match = *
```
selects all files.

A good choice communicating with the server might be:
```
timeout = 30
retries = 10
delay = 2
```
This translate to:
- skip download attempt if there is no response for 30 seconds
- retry download attempt 10 times before throwing error
- delay 2 seconds before new download attempt

A special functionality is to decrypt files while transporting from the download folder to the final destination. GnuPG and 7-Zip is emplemented for now. The encryption is is indicated by `pgp`, `7z` or `none` for no encryption, e.g.:
```
encryption = pgp
passphrase = ultrasecret
```
### LOCAL
In this section of the config file the local paths are defined:
```
download = /home/user/Download
destination = /home/user/Public
logfile = /home/user/Logging/bcollector_log.txt
logsize = 32
db = /home/user/.bcollector/files.db
```
This translates to:
- download new files to `/home/user/Download`
- copy them to  `/home/user/Public` (possibly decrypt on the way)
- write log to `/home/user/Logging/bcollector_log.txt`
- compress old logs using ZIP (in same directory) and create a new log file
- store infos about files as SQLite in `/home/user/.bcollector/files.db`

set yes to delay forwarding until destination directory does not exist
wait = yes
trigger file name to write into destination directory
trigger = /home/neo/Public/test_trigger.txt
minutes to keep files in download directory
keep_files = 1
minutes to keep entries in data base
keep_entries = 2



## Legal Notice

### License
Respect GPL-3: https://www.gnu.org/licenses/gpl-3.0.en.html

### Disclaimer
Use the software on your own risk.

This is not a commercial product with an army of developers and a department for quality control behind it.


