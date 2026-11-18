"""
Wrapper for grating movement using Arduino
"""

import os
import platform
import sys
from ctypes import c_ulong, c_double, c_ushort, c_uint64
from ctypes import cdll, byref

is_64bits = sys.maxsize > 2 ** 32


class IK220:
    """
    Wrapper to the Heidenhain dll
    """
    units = 'cm'

    def __init__(self, dllpath="C:\\Program Files (x86)\\HEIDENHAIN\\DLL64"):
        """Initialize device"""
        self.dll = None
        self.axis = []
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
        self.config_endat()

    def config_endat(self):
        p_status = c_ushort()  # pointer
        p_type = c_ushort()  # pointer
        p_period = c_ulong()  # pointer
        p_step = c_ulong()  # pointer
        p_turns = c_ushort()  # pointer
        p_ref_dist = c_ushort()  # pointer
        p_cnt_dir = c_ushort()
        for axis in self.axis:
            # Sequence required by the IK 220 manual (p. 33 and 47-50), checked on the Z40 card after a cold start:
            # without the first three calls, IK220ReadEn fails unless another program configured the card before.
            self.dll.IK220Init(axis)  # loads and starts the firmware; all parameters return to their default values
            self.dll.IK220WritePar(axis, 1, 1)  # parameter 1 = 1: EnDat encoder (default 0: incremental)
            self.dll.IK220ResetEn(axis, byref(p_status))  # resets the EnDat encoder
            self.dll.IK220ConfigEn(axis, byref(p_status), byref(p_type), byref(p_period), byref(p_step), byref(p_turns),
                                   byref(p_ref_dist), byref(p_cnt_dir))

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
        self.dll.IK220Find_64(byref(serial))
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
        self.dll.IK220ReadEn(1, byref(self.pStatus), byref(p_data), byref(self.pAlarm))
        return round(p_data.value * 2, 3)