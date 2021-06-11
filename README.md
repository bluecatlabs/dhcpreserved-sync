![alt text](logo.png "BlueCat Logo")

dhcpreserved.py
Python script run upon BDDS server to capture the last time a DHCP Reserved Object was leased out, updates a "Last Reserved" user defined field if a DHCPACK is found in the correct syslog

**This is a community offering on BlueCat labs and as such it provided without formal support, this software is provided on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. Flashing BIOS/iDRAC remotely is an invasive task and should be fully tested before using in production environments.**

## Usage

```
python3 dhcpreserved.py --bam <IP address of BAM> --username <API username> --password <API username>

bam         IP Address of the BlueCat Address Manager
username    BAM API username
password    BAM API password

```
