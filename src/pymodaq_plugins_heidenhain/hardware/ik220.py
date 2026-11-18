"""
Wrapper for grating movement using Arduino
"""

import os
import platform
import sys
from ctypes import c_ulong, c_double, c_ushort, c_uint64
from ctypes import cdll, byref

is_64bits = sys.maxsize > 2 ** 32
# Status written by IK220ReadEn (IK 220 manual, p. 49)
ENDAT_READ_STATUS = {0: 'ok', 1: 'encoder not responding or not connected', 2: 'CRC error', 3: 'type A error'}


class IK220Error(Exception):
    """Error reported by the IK 220 card, its driver or the EnDat encoder."""


class IK220:
    """
    Wrapper to the Heidenhain dll
    """
    units = 'cm'

    def __init__(self, dllpath="C:\\Program Files (x86)\\HEIDENHAIN\\DLL64", axis=1):
        """Initialize device

        axis: IK 220 axis the encoder is connected to, from 0 to 15 (two axes per card).
        On the Z40, the ruler is on axis 1 ("Axis 2" in the HEIDENHAIN test application).
        """
        self.dll = None
        self.axis = []
        self.encoder_axis = axis
        self.pStatus = c_ushort()
        self.pAlarm = c_ushort()
        if not dllpath:
            dllpath = 'C:\\Program Files (x86)\\HEIDENHAIN'
            if is_64bits:
                if platform.machine() == "AMD64":
                    dllpath = os.path.join(dllpath, 'DLL64')
                else:
                    dllpath = os.path.join(dllpath, 'DLL')
        try:
            # Check operating system and load library
            if platform.system() == "Windows":
                if is_64bits:
                    dllname = os.path.join(dllpath, "IK220Dll64")
                    # print(dllname)
                    self.dll = cdll.LoadLibrary(dllname)
                else:
                    dllname = os.path.join(dllpath, "IK220Dll")
                    self.dll = cdll.LoadLibrary(dllname)
            else:
                print("Cannot detect operating system, will now stop")
                raise Exception("Cannot detect operating system, will now stop")
        except Exception as e:
            raise Exception("error while initialising hein libraries. " + str(e))

        self.get_present_axis()
        if self.encoder_axis not in self.axis:
            raise ValueError(f'Axis {self.encoder_axis} not found on the IK 220 cards, present axes: {self.axis}')
        self.config_endat()

    def config_endat(self):
        p_status = c_ushort()  # pointer
        p_type = c_ushort()  # pointer
        p_period = c_ulong()  # pointer
        p_step = c_ulong()  # pointer
        p_turns = c_ushort()  # pointer
        p_ref_dist = c_ushort()  # pointer
        p_cnt_dir = c_ushort()
        for axis in [self.encoder_axis]:
            # Sequence required by the IK 220 manual (p. 33 and 47-50), checked on the Z40 card after a cold start:
            # without the first three calls, IK220ReadEn fails unless another program configured the card before.
            if not self.dll.IK220Init(axis):  # loads and starts the firmware; all parameters return to default values
                raise IK220Error(f'IK220Init failed on axis {axis}')
            if not self.dll.IK220WritePar(axis, 1, 1):  # parameter 1 = 1: EnDat encoder (default 0: incremental)
                raise IK220Error(f'IK220WritePar failed on axis {axis}')
            if not self.dll.IK220ResetEn(axis, byref(p_status)) or p_status.value != 0:  # resets the EnDat encoder
                raise IK220Error(f'IK220ResetEn failed on axis {axis} (status {p_status.value})')
            if (not self.dll.IK220ConfigEn(axis, byref(p_status), byref(p_type), byref(p_period), byref(p_step),
                                           byref(p_turns), byref(p_ref_dist), byref(p_cnt_dir))
                    or p_status.value != 0):
                raise IK220Error(f'IK220ConfigEn failed on axis {axis} (status 0x{p_status.value:04X})')

    def get_present_axis(self):
        """
        :return:
            position of the axis i with respect to the
        Input:
            None
        Output:
            pointer 16 entries
        """
        serial = (c_uint64 * 16)()
        if not self.dll.IK220Find_64(byref(serial)):
            raise IK220Error('IK220Find_64 failed: is the IK 220 driver installed?')
        self.axis = []
        for i in range(0, 16, 1):  # There is 16 axis numbered from 0 t 15
            if serial[i] > 0:
                self.axis.append(i)
            else:
                pass
        return f'Axis {self.axis} are present'

    def get_axis_position(self):
        """
        :return: the absolute position deduced from one period.
        To obtain the real value in cm^{-1} this result has to be multiplied by a factor 2.
        Finally, as our goal is t reach a resolution of 0.1 cm^{-1} (i.e. 1µm),
        the obtained result is rounded

        Input:
            None
        Output:

        """
        p_data = c_double()
        ok = self.dll.IK220ReadEn(self.encoder_axis, byref(self.pStatus), byref(p_data), byref(self.pAlarm))
        if not ok or self.pStatus.value != 0:
            status = self.pStatus.value
            raise IK220Error(f'IK220ReadEn failed on axis {self.encoder_axis} '
                             f'(status {status}: {ENDAT_READ_STATUS.get(status, "unknown")})')
        if self.pAlarm.value:
            raise IK220Error(f'Alarm of the EnDat encoder on axis {self.encoder_axis}')
        return round(p_data.value * 2, 3)
    