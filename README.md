About
=====

TFBrew is yet another beer homebrewing control system for (but not limited to) the Raspberry Pi.

You can use it to:
+ Monitor the temperature in your mash kettle or hot liqure tank using the W1Sensor plugin.
+ Turn heaters and pumps on and off using the GPIOActor (raspberry pi) or the TPLinkActor (WiFi controlled socket).
+ Maintain a stable temperature in your mash by combining a heater and temperature sensor in a controller
  with process logic (the PIDLogic plugin).
+ Control and monitor your brewing process through a mobile device, e.g. with a [Blynk](http://www.blynk.cc) frontend.

It aims to be a flexible, modular system allowing the user to configure it to different setups
of homebrewing equipment.

TFBrew was written by Hrafnkell Eiríksson - <he@klaki.net>

TFBrew is Copyright from 2017 by Hrafnkell Eiríksson and is licensed by the GNU GPL v3 license.
See the LICENSE file.

Please consult the [Wiki](https://github.com/hrafnkelle/tfbrew/wiki) for further information.

Plugins
=======
TFBrew is based around the idea of components that send each other messages. Components are implemented through plugins.
The following components are available

+ W1Sensor - for using one-wire sensors like the ds18b20
+ TiltSensor - for using the Tilt Hydrometer
+ DummySensor - simulating a sensor with a configurable value + noise
+ GPIOActor - for controlling relays (SSR) with the GPIO pins on the Raspberry Pi
+ TPLinkActor - for controlling a TPLink WiFi socket
+ DummyActor - simulating an actor, just prints out the actions
+ PIDLogic - for precise temperature control with a PID (e.g. recirculated mash)
+ HysteresisLogic - for on/off temperature control with a hysteresis (e.g. fermentation fridge control)
+ BlynkLib - for communicating with a Blynk frontend
+ SimpleWebView - for viewing the state of sensors, actors, etc in a web browser
+ Ubidots - for logging to the Ubidots IoT cloud

Configuration
=============

It is configured throug a YAML configuration file, found in config.yaml.
The included configuration might work for a single vessel BIAB system controlled by a Raspberry Pi,
using GPIO for actors and a one-wire (w1) ds18b20 (or similar) temperature sensor.
This could be controlled by a Blynk user interface.
See the included config.yaml as an example.

First, actors and sensors are declared.
Then, one or more controller is declared, a logic (how do decide when to activate e.g. heater), a sensor and an actor are attached.
Extensions can then be loaded.
Finally, message routing is set up in connections.
Each component has one or more sending and receving endpoint.
Messages from one component to another are set up like
```
KettleController.power=>UserInterface.powerdisplay
```
Installation
============
TFBrew requires at least Python 3.5 (for asyncio async/await support)

Clone this repository, and set up a virtualenv
You will need to install the following python packages (pip install into your virtualenv)
+ aiofiles
+ aiohttp
+ RPi.GPIO
+ ruamel.yaml
+ pybluez

then run the tfbrew.py file