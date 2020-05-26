# openrgb-python
A python client for the [OpenRGB SDK](https://gitlab.com/CalcProgrammer1/OpenRGB)

I started this project because I wanted to be able to control the color of my lights based on temps.  Because of this goal, the full functionality of the OpenRGB SDK isn't implemented, but I tried to implement the supported features in the best (easiest to use) way possible.  

SDK Feature Support:
  - [x] Setting client name
  - [x] Getting device info
  - [x] Setting color by device
  - [x] Setting color by zone
  - [ ] Setting color by led
  - [ ] Setting mode
  - [ ] Setting custom modes
  - [ ] resizing zones

```python
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType

client = OpenRGBClient()

client.clear() # Turns everything off

motherboard = client.get_devices_by_type(DeviceType.DEVICE_TYPE_MOTHERBOARD)[0]

motherboard.set_color(RGBColor(0, 255, 0))
motherboard.zone[0].set_color(RGBColor(255, 0, 0))
```

For a more fully-featured python implementation, check out B Horn's [OpenRGB-PyClient](https://github.com/bahorn/OpenRGB-PyClient)