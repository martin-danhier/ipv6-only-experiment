#!/usr/bin/env python
import jinja2
import os
import json

### Settings loading ###

def load_settings():
    # Get prefix from ppp0
    router_ipv6 = os.popen("ip addr show ppp0 scope global | grep -Po 'inet6 \K[\da-f:]+'").read().strip()

    if router_ipv6 == "":
        print("No router IPv6 address found")
        return None, False

    router_ipv6_prefix = ":".join(router_ipv6.split(":")[:4]) + "::"
    nat64_link_local = os.popen("ip addr show nat64 scope link | grep -Po 'inet6 \K[\da-f:]+'").read().strip()

    settings = {
        'prefix': router_ipv6_prefix,
        'router': {
            'ipv6': router_ipv6,
        },
        'nat64': {
            'ipv6': f"{router_ipv6_prefix}2",
            'router_ipv6': f"{router_ipv6_prefix}3",
            'ipv4': '192.168.255.2',
            'router_ipv4': '192.168.255.3',
            'link_local': nat64_link_local,
        }
    }

    # Load old settings
    old_settings = {}
    if os.path.exists("settings.json"):
        with open("settings.json", "r") as f:
            old_settings = json.load(f)

    # Deep check if settings have changed
    changed = False
    if old_settings != settings:
        changed = True

    # Save the settings
    with open("settings.json", "w") as f:
        json.dump(settings, f)

    return settings, changed

### Config generation ###

def gen_config(template_file: str, settings):

    # --- Get the template file ---
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(template_file)),
        extensions=['jinja2.ext.do'],
    )
    template = env.get_template(os.path.basename(template_file))

    # --- Render the template ---
    rendered = template.render(settings)

    # --- Write the rendered template to the output directory ---

    # Remove .j2 from the filename
    output_file = os.path.basename(template_file)[:-3]

    # Write the rendered template to the output directory
    with open(f"output/{output_file}", "w") as f:
        f.write(rendered)

    print(f"Generated {output_file}")

    return rendered

### Service update ###

def update_radvd_config():
    # Copy output file to /etc/radvd.conf
    os.system("sudo cp output/radvd.conf /etc/radvd.conf")
    # Restart radvd
    os.system("sudo systemctl restart radvd")

def update_tayga_config():
    # Copy output file to /etc/tayga.conf
    os.system("sudo cp output/tayga.conf /etc/tayga.conf")
    # Restart tayga
    os.system("sudo systemctl restart tayga")

def update_services():
    # Update radvd config
    update_radvd_config()

    # Update tayga config
    update_tayga_config()

### Manual network fixes ###

def setup_network(settings):
    router_ipv6 = settings['router']['ipv6']
    nat_ipv6    = settings['nat64']['ipv6']
    nat_router_ipv6 = settings['nat64']['router_ipv6']
    nat_router_ipv4 = settings['nat64']['router_ipv4']

    # Add router IP to wlp2s0
    os.system(f"sudo ip addr add {router_ipv6}/64 dev wlp2s0")

    # Add nat64 IPs
    os.system(f"sudo ip addr add {nat_router_ipv6}/127 dev nat64")
    os.system(f"sudo ip addr add {nat_router_ipv4}/24 dev nat64")

    # Add nat64 route
    os.system(f"sudo ip -6 route add 64:ff9b::/96 via {nat_ipv6}")

    print("Network was setup")

def fix_network(settings):
    prefix = settings['prefix']

    # Remove prefix route from ppp0 (it keeps getting added for some reason)
    os.system(f"sudo ip -6 route del {prefix}/64 dev ppp0")

    print("Fixed routing")

### Main ###

def main():
    # Get the current settings
    settings, changed = load_settings()

    # Skip this time if settings can't be loaded
    if settings is not None:

        # Update the config files if the settings have changed
        if changed:
            # Setup network
            setup_network(settings)

            # Create output directory if it doesn't exist
            if not os.path.exists("output"):
                os.makedirs("output")

            # Get the template files
            template_files = os.listdir("templates")

            # Render the templates
            for template_file in template_files:
                gen_config(f"templates/{template_file}", settings)

            # Update the services
            update_services()

        # In any case, fix the network
        fix_network(settings)

if __name__ == "__main__":
    main()
