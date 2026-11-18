import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_utils.config import GlobalConfig
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from pymodaq_plugins_heidenhain.hardware.ik220 import IK220
from pymodaq_plugins_heidenhain.hardware.ik220_mock import IK220Mock


class DAQ_0DViewer_IK220(DAQ_Viewer_base):
    """ Instrument plugin class for a OD viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of instruments that should be compatible with this instrument plugin.
        * With which instrument it has actually been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

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
        """Terminate the communication protocol"""
        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        # only the master owns the controller (a slave must not close the shared one) and ini_stage/ini_detector may
        # have failed before creating it, so close can be called while self.controller is still None
        if self.is_master and self.controller is not None:
            #  self.controller.your_method_to_terminate_the_communication()  # when writing your own plugin replace this line
            ...

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
        """Stop the current grab hardware wise if necessary"""
        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_stop_acquisition()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        ##############################
        return ''

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == "a_parameter_you've_added_in_self.params":
           self.controller.your_method_to_apply_this_param_change()  # when writing your own plugin replace this line
#        elif ...
        ##


if __name__ == '__main__':
    main(__file__)
