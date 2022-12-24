# IPv6-only experiment

This repository contains the configuration files and the scripts that were used for an experiment in the context of the networking course.

The objective of the experiment is to configure an IPv6-only Wi-Fi access point and evaluate its feasibility and performance.

This repository contains three main components:

- Static configurations: these configurations need to be saved in the specified emplacement in the router (written as a comment on the first line of the file).
- Dynamic configurations: this component is a script to is meant to run regularly in order to generate configurations that require dynamic data (such as IP address).
- Bandwidth and throughput measurements: this component contains a script for measuring bandwidth and throughput, and a notebook that generates graphs using the results.

## Setup

This section contains the initial setup that needs to be performed on the router computer.

### Assumptions

The following assumptions are made:

- The server is running Linux (Manjaro 22)
- The server has access to an Ethernet interface named ``enp3s0`` and a Wi-Fi interface named ``wlp2s0``.
- The server is connected via Ethernet to a router that allows prefix delegation using PPPoE (not DHCPv6). Here, we used Proximus.

You will need to adapt the configurations if you do not meet these assumptions.

### Network credentials

In order to receive a prefix from Proximus, you need to establish a PPPoE session using the network credentials.

These credentials are different from the Wi-Fi password, they can be found on the MyProximus website by following [these instructions](https://www.proximus.be/support/en/id_sfaqr_mdm_pwd/personal/support/internet/internet-at-home/advanced-settings/password-for-your-modem-and-your-internet-connection.html).

It is also possible that your ISP instead wants you to request a prefix using DHCPv6 prefix delegation. In this case, instead of using pppd, you should uncomment prefix delegation lines in the [dhcpcd.conf](./static/dhcpcd.conf) file. Since Proximus doesn't support it, we weren't able to test it, so you might need to adapt some other config files to get it working.

Finally, some ISP do not support additionnal prefixes. In this case, you must set your router in bridge mode.

### Configuration

1. Install the following programs:
    - `hostapd`
    - `radvd` 2.20 or above: we had to build the beta from source to have PREF64 features which were added after 2.19, the latest release at time of writing
    - `dhcpcd`
    - `pppd`
    - `tayga`
    - `named` (bind9 on Debian)

2. Copy static configuration. In each file in the [static](./static/) directory, the first line is a comment indicating the destination of the file.
    - Some files require some changes, such as interface name, network credentials... Read comments.

3. Copy the [autoconfig](./autoconfig/) directory in the Documents of the main user. We used `/home/admin/Documents/autoconfig`.
4. Copy the [router_autoconfig.service](./autoconfig/router_autoconfig.service) file in the `/usr/lib/systemd/system/` directory.
5. Enable all services: `hostapd`, `dhcpcd`, `pppd`, `named`, `router_autoconfig` (the latter will start radvd and tayga)

## Measurements

On a Linux client, go in the [measurements](./measurements/) directory and run the [measure.sh](./measurements/measure.sh) script. Send the output to a file, for example `bash ./measure.sh > ./measurements/ipv6.txt`. At the same time start the download of a large file. The script will measure every second the throughput and bandwidth of the WiFi interface. The provided notebook can then be used to generate graphs of the results.

This script is forked from [Dan Nanni's scripts](https://www.xmodulo.com/measure-packets-per-second-throughput-high-speed-network-interface.html).