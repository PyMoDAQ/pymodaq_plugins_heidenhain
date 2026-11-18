"""
Wrapper of the HEIDENHAIN IK 220 DLL (IK220Dll64.dll), to read the absolute position of an EnDat encoder.

Written for the LC 483 linear encoder of the Dilor Z40 spectrometer, tested on Windows 10 64 bits with the
HEIDENHAIN driver 739275-05. Only one program may use the card at a time: the HEIDENHAIN test application calls
IK220Init when it starts, which erases the configuration made by this class.
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
    """Absolute EnDat encoder connected to an IK 220 card.

    The constructor loads the DLL, checks that the axis exists and configures it (IK220Init, EnDat encoder,
    IK220ResetEn, IK220ConfigEn); get_axis_position then returns the position in mm.

    Example:
        ik = IK220(axis=1)
        position_mm = ik.get_axis_position()
    """
    units = 'mm'

    def __init__(self, dllpath="C:\\Program Files (x86)\\HEIDENHAIN\\DLL64", axis=1):
        """Initialize device

        axis: IK 220 axis the encoder is connected to, from 0 to 15 (two axes per card).
        On the Z40, the ruler is on axis 1 ("Axis 2" in the HEIDENHAIN test application).
        """
        self.dll = None
        self.axis = []
        self.encoder_axis = axis
        self.signal_period_nm = None  # signal period of the encoder, read by IK220ConfigEn
        self.pStatus = c_ushort()
        self.pAlarm = c_ushort()
        if platform.system() != "Windows" or not is_64bits:
            raise IK220Error('The IK 220 DLL is used here with Windows and a 64-bit Python only')
        try:
            self.dll = cdll.LoadLibrary(os.path.join(dllpath, "IK220Dll64"))
        except OSError as e:
            raise IK220Error(f'Cannot load IK220Dll64 from {dllpath}: is the IK 220 driver installed? ({e})') from e

        self.get_present_axis()
        if self.encoder_axis not in self.axis:
            raise ValueError(f'Axis {self.encoder_axis} not found on the IK 220 cards, present axes: {self.axis}')
        self.config_endat()

    def config_endat(self):
        """Initialize the card on the encoder axis and configure it for an EnDat encoder."""
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
            self.signal_period_nm = p_period.value  # 20000 for the LC 483 (20 µm)

    def get_present_axis(self):
        """List the axes of the IK 220 cards (two per card) found by IK220Find_64, stored in self.axis."""
        serial = (c_uint64 * 16)()
        if not self.dll.IK220Find_64(byref(serial)):
            raise IK220Error('IK220Find_64 failed: is the IK 220 driver installed?')
        self.axis = []
        for i in range(0, 16, 1):  # 16 axes at most, numbered from 0 to 15
            if serial[i] > 0:
                self.axis.append(i)
            else:
                pass
        return f'Axis {self.axis} are present'

    def get_axis_position(self):
        """Absolute position of the encoder, in mm.

        IK220ReadEn gives the position in signal periods (IK 220 manual, p. 49), converted with the signal period
        read by IK220ConfigEn (in nm: 20000 for the LC 483, whose signal period is 20 µm).
        """
        p_data = c_double()
        ok = self.dll.IK220ReadEn(self.encoder_axis, byref(self.pStatus), byref(p_data), byref(self.pAlarm))
        if not ok or self.pStatus.value != 0:
            status = self.pStatus.value
            raise IK220Error(f'IK220ReadEn failed on axis {self.encoder_axis} '
                             f'(status {status}: {ENDAT_READ_STATUS.get(status, "unknown")})')
        if self.pAlarm.value:
            raise IK220Error(f'Alarm of the EnDat encoder on axis {self.encoder_axis}')
        return p_data.value * self.signal_period_nm * 1e-6
