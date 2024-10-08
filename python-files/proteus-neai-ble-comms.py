#!/usr/bin/env python

import keyboard
import logging
import os
import sys
import threading
import time
import traceback
import json
import config

from blue_st_sdk.manager import Manager
from blue_st_sdk.manager import ManagerListener
from blue_st_sdk.device import DeviceListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features.pnpl import feature_pnplike
from blue_st_sdk.features import feature_neai_anomaly_detection

# Bluetooth scanning time in seconds (optional).
SCANNING_TIME_s = 5

# Pause in seconds.
PAUSE_s = 1

# Duration of phases.
LEARNING_TIME_s = 10

# Timeout for notifications in seconds.
NOTIFICATIONS_TIMEOUT_s = 0.05

# MAC address of the device to connect to.
TARGET_DEVICE_MAC = config.mac_address  # Proteus - FP-AI-PDMWBSOC


# CLASSES

# Implementation of the interface used by the Manager class to notify that a new
# device has been discovered or that the scanning starts/stops.
class MyManagerListener(ManagerListener):

    #
    # This method is called whenever a discovery process starts or stops.
    #
    # @param manager          Manager instance that starts/stops the process.
    # @param enabled          True if a new discovery starts, False otherwise.
    #
    def on_discovery_change(self, manager, enabled):
        logging.getLogger('BlueST').info(
            'Discovery of bluetooth devices {}.'.format('started' if enabled else 'stopped'))

    #
    # This method is called whenever a new device is discovered.
    #
    # @param manager          Manager instance that discovers the device.
    # @param device           New device discovered.
    # @param error_message    Error message in case the advertisement data
    #                         does not comply with the BlueST protocol, when:
    #                         "show_non_bluest_devices=True" in "manager.discover()".
    #
    def on_device_discovered(self, manager, device, error_message=False):
        logging.getLogger('BlueST').info(
            'NEW DEVICE:   {}{}'.format(
                device, '' if not error_message else '   ' + error_message))

    #
    # This method is called whenever an advertising data has updated.
    #
    # @param manager          Manager instance that discovers the device.
    # @param device           Device whose advertising data has updated.
    # @param advertising_data BlueST advertising data object.
    #
    def on_advertising_data_updated(self, manager, device, advertising_data):
        logging.getLogger('BlueST').info(
            'UPDATED:      {}'.format(device))

    #
    # This method is called whenever an advertising data has been received
    # but has not changed.
    #
    # @param manager          Manager instance that discovers the device.
    # @param device           Device whose advertising data has not changed.
    # @param advertising_data BlueST advertising data object.
    #
    def on_advertising_data_unchanged(self, manager, device, advertising_data):
        logging.getLogger('BlueST').info(
            'UNCHANGED:    {}'.format(device))


#
# Implementation of the interface used by the Device class to notify that a device
# has updated its status.
#
class MyDeviceListener(DeviceListener):

    #
    # To be called whenever a device connects to a host.
    #
    # @param device Device that has connected to a host.
    #
    def on_connect(self, device):
        logging.getLogger('BlueST').info(
            'Device {} connected.'.format(device.get_name()))

    #
    # To be called whenever a device disconnects from a host.
    #
    # @param device     Device that has disconnected from a host.
    # @param unexpected True if the disconnection is unexpected, False otherwise
    #                   (called by the user).
    #
    def on_disconnect(self, device, unexpected=False):
        logging.getLogger('BlueST').info(
            'Device {} disconnected{}.'.format(device.get_name(), ' unexpectedly' if unexpected else ''))
        if unexpected:
            # Exiting.
            logging.getLogger('BlueST').info('')
            logging.getLogger('BlueST').info('Exiting...')
            logging.getLogger('BlueST').info('')
            sys.exit(0)


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its data.
#
class MyPnPLikeFeatureListener(FeatureListener):

    #
    # Constructor.
    #
    # @param event Stop event.
    #
    def __init__(self, event):
        self._event = event

    #
    # To be called whenever the feature updates its data.
    # Stop event triggered when valid JSON is received.
    #
    # @param feature Feature that has updated.
    # @param sample  Data extracted from the feature.
    #
    def on_update(self, feature, sample):
        logging.getLogger('BlueST').info(feature)
        self._event.set()


#
# Implementation of the interface used by the Feature class to notify that a
# feature has updated its data.
#
class MyNEAIADFeatureListener(FeatureListener):

    #
    # Constructor.
    #
    # @param event Stop event.
    #
    def __init__(self, event):
        self._event = event

    #
    # To be called whenever the feature updates its data.
    #
    # @param feature Feature that has updated.
    # @param sample  Data extracted from the feature.
    #
    def on_update(self, feature, sample):
        global command
        logging.getLogger('BlueST').info(feature)
        phase = feature.get_phase(sample)
        if (command == feature_neai_anomaly_detection.Command.LEARN and \
            phase == feature_neai_anomaly_detection.Phase.IDLE_TRAINED) or \
           (command == feature_neai_anomaly_detection.Command.DETECT and \
            (phase == feature_neai_anomaly_detection.Phase.IDLE or \
             phase == feature_neai_anomaly_detection.Phase.IDLE_TRAINED)) or \
           (command == feature_neai_anomaly_detection.Command.STOP and \
            (phase == feature_neai_anomaly_detection.Phase.IDLE or \
             phase == feature_neai_anomaly_detection.Phase.IDLE_TRAINED)) or \
           (command == feature_neai_anomaly_detection.Command.RESET and \
            phase == feature_neai_anomaly_detection.Phase.IDLE):
            self._event.set()


# FUNCTIONS

# Wait for active notifications until the given event is triggered.
def wait_for_notifications_until_event_triggered(device, stop_event):
    global command
    while not stop_event.is_set():
        device.wait_for_notifications(NOTIFICATIONS_TIMEOUT_s)
    command = None
    stop_event.clear()


# Wait for active notifications until the given key is pressed.
def wait_for_notifications_until_key_pressed(device, stop_key):
    stop_event = threading.Event()
    KeyboardThread(stop_key, stop_event)
    wait_for_notifications_until_event_triggered(device, stop_event)


# Release manager resources.
def release_manager_resources(manager):
    if manager:
        manager.remove_listeners()


# Release device resources.
def release_device_resources(device):
    if device:
        for feature in device.get_features():
            if feature:
                feature.remove_listeners()
        if device.is_connected():
            device.remove_listeners()
            device.disconnect()


# Main application.
def main(argv):
    global command
    upstream_dict = {"message":""}
    with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_message.json", "w") as upstream_file:
        json.dump(upstream_dict, upstream_file)

    # Setting text logging level: 'DEBUG', 'INFO' (default), 'WARNING', 'ERROR', or 'CRITICAL'.
    logging.getLogger('BlueST').setLevel('DEBUG')

    # Printing intro.
    logging.getLogger('BlueST').info('BlueST example: "{}"'.format(os.path.basename(__file__)))

    try:
        # Creating bluetooth manager.
        manager = Manager.instance()
        manager_listener = MyManagerListener()
        manager.add_listener(manager_listener)

        # Scanning bluetooth devices.
        logging.getLogger('BlueST').info('')
        logging.getLogger('BlueST').info('Scanning bluetooth devices... (CTRL+C to quit)')
        logging.getLogger('BlueST').info('')

        # Synchronous discovery of bluetooth devices.
        # manager.discover(SCANNING_TIME_s, show_non_bluest_devices=False)

        # Asynchronous discovery of bluetooth devices.
        # Alternative 1.
        #manager.discover(SCANNING_TIME_s, asynchronous=True)
        #time.sleep(SCANNING_TIME_s)

        # Asynchronous discovery of bluetooth devices.
        # Alternative 2.
        manager.start_discovery()
        time.sleep(SCANNING_TIME_s)
        manager.stop_discovery()

        # Getting discovered devices.
        discovered_devices = manager.get_devices()

        # Listing discovered devices.
        if not discovered_devices:
            logging.getLogger('BlueST').info('No bluetooth devices found. Exiting...')
            logging.getLogger('BlueST').info('')
            sys.exit(0)
        logging.getLogger('BlueST').info('')
        logging.getLogger('BlueST').info('Available bluetooth devices:')
        for i, device in enumerate(discovered_devices):
            logging.getLogger('BlueST').info('%d) %s: [%s]' % (i, device.get_name(), device.get_mac_address()))
            i += 1
        logging.getLogger('BlueST').info('')

        # Connecting to the target device.
        device_found = False
        for i, device in enumerate(discovered_devices):
            if device.get_mac_address() == TARGET_DEVICE_MAC:
                device_found = True
                break
        if not device_found:
            raise Exception("Error: target MAC address not found.")
        device_listener = MyDeviceListener()
        device.add_listener(device_listener)
        logging.getLogger('BlueST').info('Connecting to %s...' % (device.get_name()))
        if not device.connect():
            logging.getLogger('BlueST').info('Connection failed.')
            logging.getLogger('BlueST').info('')
            raise Exception()

        # Getting features.
        features = device.get_features()
        logging.getLogger('BlueST').info('')
        logging.getLogger('BlueST').info('Features:')
        for i, feature in enumerate(features):
            if feature:
                logging.getLogger('BlueST').info('%d) %s' % (i, feature.get_name()))
            i += 1
        logging.getLogger('BlueST').info('')

        # Add PnPLike feature and listener, and enable notifications.
        feature_pnpl = device.get_feature(feature_pnplike.FeaturePnPLike)
        pnpl_response_event = threading.Event()
        feature_pnpl_listener = MyPnPLikeFeatureListener(pnpl_response_event)
        feature_pnpl.add_listener(feature_pnpl_listener)

        # Add NEAIAnomalyDetection feature and listener, and enable notifications.
        feature_neai_ad = device.get_feature(feature_neai_anomaly_detection.FeatureNEAIAnomalyDetection)
        neai_ad_response_event = threading.Event()
        feature_neai_ad_listener = MyNEAIADFeatureListener(neai_ad_response_event)
        feature_neai_ad.add_listener(feature_neai_ad_listener)

        # Configuring learning time.
        pnpl_command = "{\"neai_anomaly_detection\": {\"time_or_signals\": " + str(LEARNING_TIME_s) + "}}"
        logging.getLogger('BlueST').info("Sending '{}' command.".format(pnpl_command))
        feature_pnpl.send_command(pnpl_command)
        device.enable_notifications(feature_pnpl)
        wait_for_notifications_until_event_triggered(device, pnpl_response_event)
        device.disable_notifications(feature_pnpl)
        logging.getLogger('BlueST').info('')
        upstream_dict["message"] = "1st COMMS SUCCESSFUL"
        with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_message.json", "w") as upstream_file:
            json.dump(upstream_dict, upstream_file)

        current_state = "IDLE"
        last_command = ""
        
        # COMMUNICATION LOOP.
        while True:
            # Open commands communication file
            with open("/home/weston/proteus-neai-demo-main/communication-jsons/downstream_commands.json", "r") as downstream_file:
                try:
                    # Copy command json into a dictionary
                    dict = json.load(downstream_file)
                except Exception as e:
                    print("Trouble reading downsteam command file, trying again soon...")
                    print(e)
                    # If unable to copy command json, return to beginning of loop after a brief pause
                    time.sleep(1)
                    continue
            # If the received command is the same as the last received command
            if dict["command"] == last_command:
                # Ignore it and return to the beginning of the loop after a brief pause
                time.sleep(1)
                continue
            else:
                # Keep track of this command as the most recent command
                last_command = dict["command"]
                
            # START ANOMALY DETECTION
            if dict["command"] == 'start_ad':
                command = feature_neai_anomaly_detection.Command.DETECT
                logging.getLogger('BlueST').info('Anomaly detection started... Press "ESC" to stop.')
                feature_neai_ad.detect()
                device.enable_notifications(feature_neai_ad)
                current_state = "ANOMALY DETECTION"
                upstream_dict["message"] = ""
                while True:
                    time.sleep(0.5)
                    with open("/home/weston/proteus-neai-demo-main/communication-jsons/downstream_commands.json", "r") as downstream_file:
                        try:
                            dict = json.load(downstream_file)
                        except:
                            print("Trouble reading downstream command file. trying again soon...")
                            continue
                    if dict["command"] == 'stop_ad':
                        break
                    else:
                        device.wait_for_notifications(NOTIFICATIONS_TIMEOUT_s)
                        if dict["command"] in ["learn","reset_knowledge"] and dict["command"] != last_command:
                            msg_str = "DEVICE IN ANOMALY DETECTION MODE... COMMAND " + dict["command"] + " IGNORED."
                            last_command = dict["command"]
                            upstream_dict["message"] = msg_str
                            with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_message.json", "w") as upstream_file:
                                json.dump(upstream_dict, upstream_file)
            # STOP ANOMALY DETECTION
            elif dict["command"] == 'stop_ad':
                if current_state != "ANOMALY DETECTION":
                    upstream_dict["message"] = "DEVICE NOT IN ANOMALY DETECTION MODE SO COMMAND stop_ad IGNORED."
                    with open("/home/weston/proteus-neai-demo-main/communication-jsons/upstream_message.json", "w") as upstream_file:
                        json.dump(upstream_dict, upstream_file) 
                    continue
                command = feature_neai_anomaly_detection.Command.STOP
                feature_neai_ad.stop()
                wait_for_notifications_until_event_triggered(device, neai_ad_response_event)
                device.disable_notifications(feature_neai_ad)
                logging.getLogger('BlueST').info('Anomaly detection stopped.')
                logging.getLogger('BlueST').info('')
                current_state = "IDLE"
            # RESET KNOWLEDGE
            elif dict["command"] == 'reset_knowledge':
                # Resetting model.
                command = feature_neai_anomaly_detection.Command.RESET
                logging.getLogger('BlueST').info('Resetting model...')
                device.enable_notifications(feature_neai_ad)
                feature_neai_ad.reset()
                wait_for_notifications_until_event_triggered(device, neai_ad_response_event)
                device.disable_notifications(feature_neai_ad)
                logging.getLogger('BlueST').info('Model cleared.')
                logging.getLogger('BlueST').info('')
            # LEARNING
            elif dict["command"] == 'learn':
                command = feature_neai_anomaly_detection.Command.LEARN
                logging.getLogger('BlueST').info('Learning started ({} seconds)...'.format(LEARNING_TIME_s))
                feature_neai_ad.learn()
                device.enable_notifications(feature_neai_ad)
                wait_for_notifications_until_event_triggered(device, neai_ad_response_event)
                device.disable_notifications(feature_neai_ad)
                logging.getLogger('BlueST').info('Learning stopped.')
                logging.getLogger('BlueST').info('')


    except Exception as e:
        try:
            # Traceback.
            logging.getLogger('BlueST').info(repr(e))
            traceback.print_exc(file=sys.stdout)
            # Exiting.
            if 'manager' in locals():
                release_manager_resources(manager)
            if 'device' in locals():
                release_device_resources(device)
            logging.getLogger('BlueST').info('')
            logging.getLogger('BlueST').info('Exiting...')
            logging.getLogger('BlueST').info('')
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':

    # Global variables.
    command = None

    # Running main function.
    main(sys.argv[1:])
