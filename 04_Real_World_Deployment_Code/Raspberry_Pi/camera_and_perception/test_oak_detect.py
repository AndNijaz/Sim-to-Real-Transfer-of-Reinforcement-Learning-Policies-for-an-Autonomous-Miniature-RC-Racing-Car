import depthai as dai

devices = dai.Device.getAllAvailableDevices()

if not devices:
    print("No OAK devices found.")
else:
    print(f"Found {len(devices)} OAK device(s):")
    for device in devices:
        print(device)
