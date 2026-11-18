import numpy as np

from pymodaq_utils.config import GlobalConfig
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from pymodaq_plugins_heidenhain.hardware.ik220 import IK220
from pymodaq_plugins_heidenhain.hardware.ik220_mock import IK220Mock


class DAQ_0DViewer_IK220(DAQ_Viewer_base):
    """PyMoDAQ 0D viewer giving the absolute position, in mm, of a HEIDENHAIN EnDat encoder read by an IK 220 card.

    Compatible devices: HEIDENHAIN IK 220 PC counter card (PCI) with an absolute encoder with EnDat interface, such as
    the LC 483 linear encoder.

    Tested with an IK 220 card and an LC 483 encoder on axis 1 (ruler of the Dilor Z40 spectrometer), Windows 10
    64 bits (version 1607), PyQt5, PyMoDAQ 5.3.11 with pymodaq_gui 5.3.11: the hardware class, including after a cold
    start of the PC, and the plugin in DAQ_Viewer (position stable to about 30 nm). Also tested in MOCK mode (simulated
    card, hardware/ik220_mock.py).

    Installation: HEIDENHAIN IK 220 driver and DLL (IK220Dll64.dll, package 739275-05 for Windows 10 64 bits), and a
    64-bit Python. Set the mode to IK220 and the axis in the local configuration file config_heidenhain.toml.

    Only one program may use the card at a time: the HEIDENHAIN test application calls IK220Init when it starts,
    which erases the configuration made by this plugin. Close it before initializing the plugin.

    Attributes:
    -----------
    controller: IK220 or IK220Mock
        Wrapper of the IK 220 DLL, or its simulator in MOCK mode.
    """
    params = comon_parameters + [
        {'title': 'Mode:', 'name': 'mode', 'type': 'list', 'limits': ['MOCK', 'IK220'],
         'value': GlobalConfig()('heidenhain', 'ik220', 'mode'),
         'tip': 'MOCK: simulated card, IK220: real card (applied at the next initialization)'},
        {'title': 'Axis:', 'name': 'axis', 'type': 'int', 'min': 0, 'max': 15,
         'value': GlobalConfig()('heidenhain', 'ik220', 'axis'),
         'tip': 'IK 220 axis of the encoder (applied at the next initialization)'},
        {'title': 'DLL folder:', 'name': 'dll_path', 'type': 'str',
         'value': GlobalConfig()('heidenhain', 'ik220', 'dll_path'),
         'tip': 'Folder of IK220Dll64.dll (applied at the next initialization)'},
        {'title': 'Signal period (nm):', 'name': 'signal_period', 'type': 'int', 'value': 0, 'readonly': True,
         'tip': 'Signal period of the encoder, read by IK220ConfigEn at initialization'},
    ]

    def ini_attributes(self):
        self.controller: IK220 = None

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:
            controller_class = IK220Mock if self.settings['mode'] == 'MOCK' else IK220
            self.controller = controller_class(dllpath=self.settings['dll_path'], axis=self.settings['axis'])
        else:
            self.controller = controller
        self.settings.child('signal_period').setValue(self.controller.signal_period_nm)

        # prepares the viewer for one value, the position in mm
        self.dte_signal_temp.emit(DataToExport(name='IK220', data=[
            DataFromPlugins(name='IK220', data=[np.array([0.])], dim='Data0D', labels=['Position'], units='mm')]))

        info = (f"IK 220 axis {self.controller.encoder_axis} ({self.settings['mode']}), "
                f"signal period {self.controller.signal_period_nm} nm")
        return info, True

    def close(self):
        """Release the controller: the IK 220 DLL has no function to end the communication"""
        # only the master owns the controller (a slave must not close the shared one) and ini_detector may
        # have failed before creating it, so close can be called while self.controller is still None
        if self.is_master and self.controller is not None:
            self.controller = None

    def grab_data(self, Naverage=1, **kwargs):
        """Read the position of the encoder, in mm

        Synchronous: a reading takes less than a millisecond. Averaging, if any, is done by DAQ_Viewer
        (hardware_averaging is False), so Naverage is not used here.
        """
        position = self.controller.get_axis_position()
        self.dte_signal.emit(DataToExport(name='IK220', data=[
            DataFromPlugins(name='IK220', data=[np.array([position])], dim='Data0D', labels=['Position'],
                            units='mm')]))

    def stop(self):
        """Nothing to stop: a reading of the encoder is instantaneous"""
        return ''

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        # mode, axis and dll_path are applied at the next initialization, signal_period is read-only
        pass


if __name__ == '__main__':
    main(__file__)
