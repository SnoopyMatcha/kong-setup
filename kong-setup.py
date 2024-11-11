import os
import signal

import requests

API_URL = os.environ["API_URL"]
SERVICE_NAME = os.environ["SERVICE_NAME"]
URL_PREFIX = os.environ["URL_PREFIX"]
SERVICE_PORT = os.environ["SERVICE_PORT"]
PORTAL_URL = os.environ["PORTAL_URL"]


print(f"API URL: {API_URL}", flush=True)
print(f"Service name: {SERVICE_NAME}", flush=True)
print(f"URL prefix: {URL_PREFIX}", flush=True)
print(f"Service port: {SERVICE_PORT}", flush=True)
print(f"Portal URL: {PORTAL_URL}", flush=True)

service_id = None
route_id = None
plugin_id = None

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

def create_service():
    global service_id
    """
    Create a service on Kong with the given name and port.

    The service will be created with the following configuration:
    - protocol: http
    - host: <SERVICE_NAME>
    - port: <SERVICE_PORT>
    - path: /
    - connect timeout: 6000
    - write timeout: 6000
    - read timeout: 6000
    - enabled: True

    The function will print a success message if the service is created
    successfully, otherwise it will print an error message and exit with code 1.

    The function will return the ID of the created service.
    """
    print("Creating service...", flush=True)

    url = f"{API_URL}/services"
    data = {
        "name": SERVICE_NAME,
        "retries": 5,
        "protocol": "http",
        "host": SERVICE_NAME,
        "port": int(SERVICE_PORT),
        "path": "/",
        "connect_timeout": 6000,
        "write_timeout": 6000,
        "read_timeout": 6000,
        "enabled": True,
    }
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    if response.status_code == 201:
        print("Service created successfully", flush=True)
    else:
        print(f"Error creating service: {response.text}", flush=True)
        cleanup()
        exit(1)
    service_id = response.json()["id"]
    print(f"Service ID: {service_id}", flush=True)
    return service_id


def create_route():
    global route_id
    """
    Create a route for a service.

    This function will print a success message if the route is created
    successfully, otherwise it will print an error message and exit with code 1.

    The function will return the ID of the created route.
    """
    print("Creating route...", flush=True)

    url = f"{API_URL}/services/{service_id}/routes"
    data = {
        "name": f"{SERVICE_NAME}-route",
        "protocols": ["http", "https"],
        "methods": ["GET", "PUT", "POST", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        "paths": [URL_PREFIX],
    }
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    if response.status_code == 201:
        print("Route created successfully", flush=True)
    else:
        print(f"Error creating route: {response.text}", flush=True)
        cleanup()
        exit(1)
    route_id = response.json()["id"]
    print(f"Route ID: {route_id}", flush=True)


def create_plugin():
    global plugin_id
    """
    Create a plugin for a route.

    The plugin will be created with the name "amas-plugin", and the given
    configuration. The plugin will be enabled for the given protocols.

    The function will print a success message if the plugin is created
    successfully, otherwise it will print an error message and exit with code 1.

    The function will return the ID of the created plugin.
    """

    print("Creating plugin...", flush=True)
    url = f"{API_URL}/services/{service_id}/plugins"
    data = {
        "name": "amas-plugin",
        "config": {
            "pdp_endpoint": PORTAL_URL,
            "pdp_path": "/user/whoami/",
        },
        "protocols": ["grpc", "grpcs", "http", "https"],
        "enabled": False,
    }

    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    if response.status_code == 201:
        print("Plugin created successfully", flush=True)
    else:
        print(f"Error creating plugin: {response.text}", flush=True)
        cleanup()
        exit(1)
    plugin_id = response.json()["id"]
    print(f"Plugin ID: {plugin_id}", flush=True)


def cleanup():
    global service_id, route_id, plugin_id
    print("Cleaning up...", flush=True)
    print(f"Service ID: {service_id}", flush=True)
    print(f"Route ID: {route_id}", flush=True)
    print(f"Plugin ID: {plugin_id}", flush=True)
    if service_id:
        print("Cleaning up resources...", flush=True)
        # 刪除插件
        response = requests.delete(f"{API_URL}/plugins/{plugin_id}")
        print(f"Plugin deleted: {response.text}", flush=True)
    if route_id:
        # 刪除路由
        response = requests.delete(f"{API_URL}/routes/{route_id}")
        print(f"Route deleted: {response.text}", flush=True)
    if service_id:
        # 刪除服務
        response = requests.delete(f"{API_URL}/services/{service_id}")
        print(f"Service deleted: {response.text}", flush=True)


if __name__ == "__main__":

    create_service()
    create_route()
    create_plugin()
    killer = GracefulKiller()
    # 阻塞主進程，直到收到中斷信號
    while True:
      if killer.kill_now:
        break
    print("Exiting...")
    cleanup()
