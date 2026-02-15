# Pi-Betaflight WiFi Control System

Pi-Betaflight-Link is a Raspberry Pi–based WiFi control bridge that lets you fly a Betaflight quad using a gamepad over your local network instead of a traditional RC transmitter.[page:1]

## Overview

The system is split into **three** main layers that work together over WiFi and USB serial.[page:1]

- Layer 1 – Input (Mac + Gamepad): `gamepad_controller.py` reads joystick axes and buttons, converts them into RC channel values (1000–2000), and sends them as UDP packets to the Pi.[page:1]  
- Layer 2 – Bridge (Raspberry Pi Zero 2 W): `drone_bridge.py` listens for those UDP packets on `192.168.1.179:5555`, unpacks the RC values, and forwards them to the flight controller interface.[page:1]  
- Layer 3 – Flight Controller (HAKRC F405 V2): `flight_controller.py` speaks MSP over `/dev/ttyACM0` (115200 baud) so Betaflight receives valid RC commands as if from a regular receiver.[page:1]

## Features

- Gamepad-to-RC mapping with configurable channels and ranges (1000–2000). [page:1]  
- WiFi UDP link between the ground station (Mac) and Raspberry Pi bridge. [page:1]  
- MSP serial interface to any compatible Betaflight flight controller (tested on HAKRC F405 V2). [page:1]  
- Clear separation of responsibilities between input, networking, and MSP/serial layers for easier debugging and extension. [page:1]

## Repository Structure

- `gamepad_controller.py` – Reads gamepad input on the Mac, converts to RC values, and sends UDP packets to the Pi. [page:1]  
- `drone_bridge.py` – Runs on the Pi Zero 2 W, receives UDP packets on port `5555`, and forwards them to the flight controller module. [page:1]  
- `flight_controller.py` – Handles USB serial connection to the Betaflight FC and implements the MSP command layer. [page:1]

## Basic Usage

1. Connect the Raspberry Pi Zero 2 W to the Betaflight flight controller via USB so it appears as `/dev/ttyACM0` at 115200 baud. [page:1]  
2. Configure the Pi on the same WiFi network as your Mac, using its IP address. [page:1]  
3. Run `drone_bridge.py` on the Pi to start listening for incoming RC UDP packets on port `5555`. [page:1]  
4. On the Mac, connect a supported gamepad and run `gamepad_controller.py`, pointing it to the Pi’s IP and UDP port. [page:1]  
5. Arm and control the quad through Betaflight using the gamepad inputs sent over WiFi. [page:1]

## Safety Notes

- Always test with props removed first and verify channel mapping, arming behavior, and failsafe before attempting any flight. [page:1]  
- Use a secure, low-latency local network; unexpected WiFi drops or lag can lead to loss of control. [page:1]  
- Ensure Betaflight failsafe is correctly configured to disarm, drop, land or return home if MSP or RC data stops updating. [page:1]
