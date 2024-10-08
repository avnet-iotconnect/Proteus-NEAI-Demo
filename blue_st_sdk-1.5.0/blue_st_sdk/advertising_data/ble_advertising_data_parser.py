################################################################################
# COPYRIGHT(c) 2024 STMicroelectronics                                         #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided that the following conditions are met:  #
#   1. Redistributions of source code must retain the above copyright notice,  #
#      this list of conditions and the following disclaimer.                   #
#   2. Redistributions in binary form must reproduce the above copyright       #
#      notice, this list of conditions and the following disclaimer in the     #
#      documentation and/or other materials provided with the distribution.    #
#   3. Neither the name of STMicroelectronics nor the names of its             #
#      contributors may be used to endorse or promote products derived from    #
#      this software without specific prior written permission.                #
#                                                                              #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"  #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE    #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE   #
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE    #
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR          #
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF         #
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS     #
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN      #
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)      #
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                                  #
################################################################################


"""ble_advertising_data_parser

The ble_advertising_data_parser module contains tools to parse the advertising
data coming from Bluetooth devices.
"""


# IMPORT

from abc import ABCMeta
from abc import abstractmethod


# INTERFACES

class BLEAdvertisingDataParser(object):
    """Interface to parse the advertising data sent by a Bluetooth device."""
    __metaclass__ = ABCMeta

    @classmethod
    @abstractmethod
    def parse(self, advertising_data):
        """Parse the BLE advertising_data.

        Args:
            advertising_data (list): BLE advertising_data.

        Returns:
            :class:`blue_st_sdk.advertising_data.blue_st_advertising_data.BLEAdvertisingData`:
            The advertising data information sent by the device.

        Raises:
            :exc:`NotImplementedError` if the method has not been implemented.
        """
        raise NotImplementedError('You must implement "parse()" to '
                                  'use the "BLEAdvertisingDataParser" class.')
