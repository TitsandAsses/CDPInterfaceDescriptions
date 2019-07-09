from netmiko import ConnectHandler
import re
import getpass

u = input("Username: ")
p = getpass.getpass(prompt="Password: ")

with open('devices.txt') as f:
    devices = f.read().splitlines()

device_list = list()
for ip in devices:
    cisco_device = {
        'device_type': 'cisco_ios',
        'ip': ip,                                                         #fill in IP addresses based on devices.txt
        'username': u,
        'password': p,
        'port': 22,
        'secret': p,
        'verbose': True,
    }
    device_list.append(cisco_device)

def get_neighbor_mapping(cdp_output):
    outputList = []
    outputList = cdp_output.splitlines()                                  #split the output into a list
    neighborList = outputList[1:]                                         # drop the first line
    neighbor_mapping = {}
    hostname = ""                                                         #create hostname and toggle outside loop because sometimes
    toggle = 0                                                            #hostname is too long and line is split in 2 lines
    for line in neighborList:
        if len(line) < 50:
            hostname = line
            if '.' in str(hostname):
                hostname = hostname.split('.')                              #if hostname is followe by .systems.infra... drop all those last bits
                hostname = str(hostname[0])
            toggle = 1
            continue
        else:
            if toggle == 0:
                CdpOutputLine = str(line).split()
                hostname = CdpOutputLine[0]
                if '.' in hostname:
                    hostname = hostname.split('.')                          #if hostname is followe by .systems.infra... drop all those last bits
                    hostname = str(hostname[0])
                interface = str(CdpOutputLine[1]) + " " + str(CdpOutputLine[2])
                neighbor_mapping[interface] = hostname
                continue
            elif toggle == 1:
                toggle = 0
                CdpOutputLine = str(line).split()
                interface = str(CdpOutputLine[0]) + " " + str(CdpOutputLine[1])
                neighbor_mapping[interface] = hostname
                continue
    #print(neighbor_mapping)
    return neighbor_mapping

for device in device_list:
    print("\n")
    print("~" * 72)
    print("\n")
    print('Connecting to ' + device['ip'])
    connection = ConnectHandler(**device)
    connection.enable()
    cdp_output = connection.send_command('show cdp neighbors | b Device ID')
    neighborList = get_neighbor_mapping(cdp_output)
    while True:
        print(cdp_output)
        print("~" * 72)
        neighborIndexList = {}
        for idx, interface in enumerate(neighborList):
            print(str(idx) + ") " + neighborList.get(interface) + ' <=> ' + interface)
            neighborIndexList[idx] = interface
        print("~" * 72)
        print('Does this mapping look correct?')
        verify = input('Type the number of the incorrect one to remove or hit type Y/y to continue')
        if verify.lower() == "y":
            print("~" * 72)
            print('Applying commands and saving config')
            print("~" * 72)
            for interface in neighborList:
                commands = []
                commands.append("interface " + interface)
                commands.append(" des *** To " + neighborList.get(interface) + " ***")
                output = connection.send_config_set(commands)
                connection.send_command("do wr")
                print('\n')
                print(output)
            break
        if verify.isdigit() == True:
            interface = neighborIndexList[int(verify)]
            neighborList.pop(interface)                                     #if user enters a number drop that entry from the dictionairy

    connection.disconnect()
