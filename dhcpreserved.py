#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2021 Bluecat Networks Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Author B.Shorland - BlueCat Networks 2021

import requests
import argparse
import json
import os
import time
import datetime

# Globals
fixedIPaddress = []

# Login to BAM returns auth token
def login_bam(bamip,username,password):
    url = "http://" + bamip + "/Services/REST/v1/login?username=" + username + "&password=" + password + "&"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    token = response.text
    token = token.replace('Session Token-> ','')
    token = token.replace(' <- for User : apiuser','')
    return token

# Logout of BAM, passed IP and auth token
def logout_bam(bamip,token):
    url = "http://" + bamip + "/Services/REST/v1/logout?"
    payload={}
    headers = {}
    token=token.replace('"','')
    headers['authorization'] = token
    response = requests.request("GET", url, headers=headers, data=payload)

# Add a UDF Last Reservation to IP4 Addresses in BAM
def addUserDefinedField(bamip,token):
    url = "http://" + bamip + "/Services/REST/v1/addUserDefinedField?type=IP4Address"
    payload = json.dumps({
      "type": "TEXT",
      "defaultValue": "",
      "validatorProperties": "",
      "required": False,
      "hideFromSearch": False,
      "renderAsRadioButton": False,
      "name": "lastreservation",
      "displayName": "Last Reservation"
    })
    headers = {}
    token=token.replace('"','')
    headers['authorization'] = token
    headers['Content-type'] = 'application/json'
    response = requests.request("POST", url, headers=headers, data=payload)

# Function to return the network ID for a given IP address
def getNetwork(bamip,token,ip_address,configid):
    url = "http://" + bamip + "/Services/REST/v1/getIPRangedByIP?containerId=" + configid + "&type=IP4Network&address=" + ip_address + "&"
    payload = {}
    headers = {}
    token=token.replace('"','')
    headers['authorization'] = token
    response = requests.request("GET", url, headers=headers, data=payload)
    jsonResponse = response.json()
    id = jsonResponse['id']
    return id

# Update an entity
def updateEntity(bamip,token, entity):
    url = "http://" + bamip + "/Services/REST/v1/update"
    payload = {}
    headers = {}
    token=token.replace('"','')
    headers['authorization'] = token
    headers['Content-type'] = 'application/json'
    response = requests.request("PUT", url, headers=headers, data=json.dumps(entity))
    return response

# use getEntities to get the ID of the DHCP_RESERVED object with the passed IP
def ProcessDHCPReservedUpdate(bamip,token,networkid,ip_address,update):
    url = "http://" + bamip + "/Services/REST/v1/getEntities?parentId=" + str(networkid) + "&type=IP4Address&start=0&count=100000&"
    payload = {}
    headers = {}
    token=token.replace('"','')
    headers['authorization'] = token
    response = requests.request("GET", url, headers=headers, data=payload)
    jsonResponse = response.json()
    for val in jsonResponse:
        props = val['properties']
        # Rstrip the last | char from props
        props = props.rstrip(props[-1])
        # print (props)
        Dict = dict((x.strip(), y.strip())
             for x, y in (element.split('=')
             for element in props.split('|')))
        if Dict['state'] == "DHCP_RESERVED" and Dict['address'] == ip_address:
            val['properties'] = val['properties'] + "lastreservation=" + str(update) + "|"
            resp = updateEntity(bamip,token,val)
            return(resp)


# Function to convert hex to IP decimal format
def hex_to_ip_decimal(hex_data):
    ipaddr = "%i.%i.%i.%i" % (int(hex_data[0:2],16),int(hex_data[2:4],16),int(hex_data[4:6],16),int(hex_data[6:8],16))
    return ipaddr

# Function to read syslog in reverse looking for last DHCPACK for passed IP address
def parsesyslog(ip_address,syslog_year):
    last_match = []
    with open('/var/log/syslog', 'rt') as f:
        data = f.readlines()
    for line in reversed(data):
        if line.__contains__('DHCPACK on '+str(ip_address)):
            last_match.append(line)
            break
    try:
        lastreservation = last_match[0].split()[:3]
        lastreservation = ' '.join(lastreservation)
        # Lastreservation currently in Jun 7 14:30:25 format
        lastreservation = str(syslog_year) + " " + lastreservation
        lastreservation = datetime.datetime.strptime(lastreservation, '%Y %b %d %H:%M:%S')
    except Exception as e:
        lastreservation = 'No Reservation'
    return ip_address,lastreservation

def main():

    # Parse Commandline Arguments
    print('dhcpreserved.py v0.1 - Update Address Manager Last Reserved UDF for DHCP_RESERVED objects')
    parser = argparse.ArgumentParser(description='dhcpreserved.py v0.1 - Update Address Manager Last Reserved UDF for DHCP_RESERVED objects')
    parser.add_argument("--bam", type=str, help="IP Address of Address Manager")
    parser.add_argument("--username", type=str, help="username of API user on Address Manager" )
    parser.add_argument("--password", type=str, help="password of API user on Address Manager")
    args = parser.parse_args()

    if not (args.bam):
        parser.error('No BAM IP passed, add --bam [BAM IP]')
        exit()
    else:
        bamip = args.bam
    if not (args.username):
        parser.error('No BAM username parameter passed, add --username [BAM username]')
        exit()
    else:
        bamuser = args.username
    if not (args.password):
        parser.error('No BAM parameter passed, add --password [BAM password]')
        exit()
    else:
        bampass = args.password

    # Login to Address Manager
    mytoken = login_bam(bamip,bamuser,bampass)

    # Get the BDDS server.id which contains the server entityID, used to work out configuration for this BDDS
    if os.path.isfile('/usr/local/bluecat/server.id'):
        pathtoserverid = "/usr/local/bluecat/server.id"
        serverid_file = open(pathtoserverid,'r')
        serverid = serverid_file.read()
        serverid_file.close()
        url = "http://172.17.44.90/Services/REST/v1/getParent?entityId=" + serverid + "&"
        payload = {}
        headers = {}
        mytoken=mytoken.replace('"','')
        headers['authorization'] = mytoken
        response = requests.request("GET", url, headers=headers, data=payload)
        jsonResponse = response.json()
        configid = jsonResponse['id']
    else:
        print ("BDDS has no Server.id found, new server never under BAM control? exiting ...")
        exit()

    # Read the fixedIPaddress.dat used by DHCPMON to track DHCP_RESERVED addresses, convert all IPs from HEX to decimal IP address list
    with open('/usr/local/bluecat/fixedIPaddress.dat', 'br') as f:
        data = f.read(4)
        while data:
            number = int.from_bytes(data, "big")
            ipaddrhex = hex(number)[2:]
            result=hex_to_ip_decimal(str(ipaddrhex))
            fixedIPaddress.append(result)
            data = f.read(4)
    print("Number of DHCP Reservations known to DHCPMON:",len(fixedIPaddress))
    if len(fixedIPaddress) == 0:
        print ("No DHCP Reserved addresses, exiting ....")
        exit()
    else:
        print("List of DHCP Reserved Address[es] known to DHCPMON process:", fixedIPaddress)

    # Add the 'Last Reservation' UDF and update the field by reverse scanning of syslog for DHCPAck on IP
    addUserDefinedField(bamip, mytoken)

    # Work out the year from the syslog created timestamp, we want this to insert an ISO format date later, at default syslog is NOT in ISO format (Pah!)
    syslog_created = time.ctime(os.path.getctime("/var/log/syslog"))
    syslog_lastmod = time.ctime(os.path.getmtime("/var/log/syslog"))
    syslogc = datetime.datetime.strptime(syslog_created, '%a %b %d %H:%M:%S %Y')
    syslogm = datetime.datetime.strptime(syslog_lastmod, '%a %b %d %H:%M:%S %Y')
    print('Syslog Created: ', syslogc)
    print('Syslog Modified: ', syslogm)
    syslog_year = syslogc.year

    # Loop through IPs in fixedIPaddress sending them for parsing of when the last ACK occured
    for ip in fixedIPaddress:
        x,y = parsesyslog(ip,syslog_year)
        print ("Last DHCP reservation for " + x + " @ " + str(y))
        mynetwork = getNetwork(bamip, mytoken,str(ip),str(configid))
        id = ProcessDHCPReservedUpdate(bamip, mytoken, mynetwork,str(x),str(y))
        print("Updating Last Reserved UDF on IP " + str(x) + " " + str(id))
    logout_bam(bamip, mytoken)
    exit()

if __name__ == "__main__":
    main()
