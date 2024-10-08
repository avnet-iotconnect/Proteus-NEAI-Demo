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


# IMPORT

from blue_st_sdk.feature import Feature
from blue_st_sdk.feature import Sample
from blue_st_sdk.feature import ExtractedData
from blue_st_sdk.features.field import Field
from blue_st_sdk.features.field import FieldType
from blue_st_sdk.utils.number_conversion import LittleEndian
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidDataException


# CLASSES

class FeatureHumidity(Feature):
    """The feature handles the data coming from a humidity sensor.

    Data is two bytes long and has one decimal digit.
    """

    FEATURE_NAME = "Humidity"
    FEATURE_UNIT = "%"
    FEATURE_DATA_NAME = "Humidity"
    FEATURE_DATA_MAX = 100
    FEATURE_DATA_MIN = 0
    DATA_LENGTH_BYTES = 2
    SCALE_FACTOR = 10.0
    FEATURE_FIELDS = Field(
        FEATURE_DATA_NAME,
        FEATURE_UNIT,
        FieldType.Float,
        FEATURE_DATA_MAX,
        FEATURE_DATA_MIN)

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that will send data to
                this feature.
        """
        super(FeatureHumidity, self).__init__(
            self.FEATURE_NAME,
            device,
            [self.FEATURE_FIELDS])

    def _extract_data(self, timestamp, data, offset):
        """Extract the data from the feature's raw data.
        
        Args:
            timestamp (int): Data's timestamp.
            data (str): The data read from the feature.
            offset (int): Offset where to start reading data.
        
        Returns:
            :class:`blue_st_sdk.feature.ExtractedData`: Container of the number
            of bytes read and the extracted data.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        if len(data) - offset < self.DATA_LENGTH_BYTES:
            raise BlueSTInvalidDataException(
                'There are no %d bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        sample = Sample(
            [LittleEndian.bytes_to_int16(data, offset) / self.SCALE_FACTOR],
            self.get_fields_description(),
            timestamp)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)

    @classmethod
    def get_humidity(self, sample):
        """Get the humidity value from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            float: The humidity value if the data array is valid, <nan>
            otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[0]:
                    return float(sample._data[0])
        return float('nan')

    def read_humidity(self):
        """Read the humidity value.

        Returns:
            float: The humidity value if the read operation is successful, <nan>
            otherwise.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        try:
            self._read_data()
            return FeatureHumidity.get_humidity(self._get_sample())
        except (BlueSTInvalidOperationException, BlueSTInvalidDataException) as e:
            raise e
