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

class FeatureAccelerometer(Feature):
    """The feature handles the data coming from an accelerometer sensor.

    Data is six bytes long and has no decimal digits.
    """

    FEATURE_NAME = "Accelerometer"
    FEATURE_UNIT = "mg"
    FEATURE_DATA_NAME = ["X", "Y", "Z"]
    FEATURE_DATA_MAX = +2000
    FEATURE_DATA_MIN = -2000
    DATA_LENGTH_BYTES = 6
    X_INDEX = 0
    Y_INDEX = 1
    Z_INDEX = 2
    FEATURE_X_FIELD = Field(
        FEATURE_DATA_NAME[X_INDEX],
        FEATURE_UNIT,
        FieldType.Int16,
        FEATURE_DATA_MAX,
        FEATURE_DATA_MIN)
    FEATURE_Y_FIELD = Field(
        FEATURE_DATA_NAME[Y_INDEX],
        FEATURE_UNIT,
        FieldType.Int16,
        FEATURE_DATA_MAX,
        FEATURE_DATA_MIN)
    FEATURE_Z_FIELD = Field(
        FEATURE_DATA_NAME[Z_INDEX],
        FEATURE_UNIT,
        FieldType.Int16,
        FEATURE_DATA_MAX,
        FEATURE_DATA_MIN)

    def __init__(self, device):
        """Constructor.

        Args:
            device (:class:`blue_st_sdk.device.Device`): Device that will send data to
                this feature.
        """
        super(FeatureAccelerometer, self).__init__(
            self.FEATURE_NAME,
            device,
            [self.FEATURE_X_FIELD, self.FEATURE_Y_FIELD, self.FEATURE_Z_FIELD])

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
                'There are no %s bytes available to read.' \
                % (self.DATA_LENGTH_BYTES))
        sample = Sample(
            [LittleEndian.bytes_to_int16(data, offset),
             LittleEndian.bytes_to_int16(data, offset + 2),
             LittleEndian.bytes_to_int16(data, offset + 4)],
            self.get_fields_description(),
            timestamp)
        return ExtractedData(sample, self.DATA_LENGTH_BYTES)

    @classmethod
    def get_accelerometer_x(self, sample):
        """Get the accererometer value on the X axis from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            float: The accelerometer value on the X axis if the data array is
            valid, <nan> otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.X_INDEX]:
                    return float(sample._data[self.X_INDEX])
        return float('nan')

    @classmethod
    def get_accelerometer_y(self, sample):
        """Get the accererometer value on the Y axis from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            float: The accelerometer value on the Y axis if the data array is
            valid, <nan> otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.Y_INDEX]:
                    return float(sample._data[self.Y_INDEX])
        return float('nan')

    @classmethod
    def get_accelerometer_z(self, sample):
        """Get the accererometer value on the Z axis from a sample.

        Args:
            sample (:class:`blue_st_sdk.feature.Sample`): Sample data.
        
        Returns:
            float: The accelerometer value on the Z axis if the data array is
            valid, <nan> otherwise.
        """
        if sample:
            if sample._data:
                if sample._data[self.Z_INDEX]:
                    return float(sample._data[self.Z_INDEX])
        return float('nan')

    def read_accelerometer(self):
        """Read the accelerometer values.

        Returns:
            list: The accelerometer values on the three axis if the read
            operation is successful, <nan> values otherwise.

        Raises:
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidOperationException`
                is raised if the feature is not enabled or the operation
                required is not supported.
            :exc:`blue_st_sdk.utils.blue_st_exceptions.BlueSTInvalidDataException`
                if the data array has not enough data to read.
        """
        try:
            self._read_data()
            return [FeatureAccelerometer.get_accelerometer_x(self._get_sample()),
                FeatureAccelerometer.get_accelerometer_y(self._get_sample()),
                FeatureAccelerometer.get_accelerometer_z(self._get_sample())]
        except (BlueSTInvalidOperationException, BlueSTInvalidDataException) as e:
            raise e
