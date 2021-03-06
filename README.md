![alt text](logo.png "BlueCat Logo")

dhcpreserved.py
Python3 script, to be run upon BDDS server to capture the last time a DHCP Reserved Object was leased and updates a "Last Reserved" user defined field if a DHCPACK is found in the syslog for the reserved address.

**This is a community offering on BlueCat labs and as such it provided without formal support, this software is provided on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See license

## Usage

```
python3 dhcpreserved.py --bam <IP address of BAM> --username <API username> --password <API username>

bam         IP Address of the BlueCat Address Manager
username    BAM API username
password    BAM API password

```
## Example output
```
python3 dhcpreserved.py --bam 172.17.44.90 --username apiuser --password apiuser
dhcpreserved.py v0.1 - Update Address Manager Last Reserved UDF for DHCP_RESERVED objects
Number of DHCP Reservations known to DHCPMON: 2
List of DHCP Reserved Address[es] known to DHCPMON process: ['172.17.44.99', '172.17.44.101']
Syslog Created:  2021-06-11 09:57:01
Syslog Modified:  2021-06-11 09:57:01
Last DHCP reservation for 172.17.44.99 @ 2021-06-07 14:30:25
Updated Last Reserved UDF on 172.17.44.99 <Response [200]>
Last DHCP reservation for 172.17.44.101 @ 2021-06-07 14:07:31
Updated Last Reserved UDF on 172.17.44.101 <Response [200]>
```
![alt text](Screenshot.png "Address Manager")

## NOTES
* Requires port 443 to be open on the BlueCat DNS/DHCP Server firewall in order to communicate with the BlueCat Address Manager API via HTTPS
* Should NOT require any pip installation of python libraries, python3 native libraries only
* Tested provisionally against Integrity 9.3 only, should function on Integrity 9.1+
* Expected to be called periodically to update the Address Manager, only supports default DATETIME format and does NOT scan/decompress .gz syslog files only the current one
