"""Simulated IK 220 card with an EnDat encoder: same public methods as IK220, no DLL needed.

Used by the MOCK mode of the plugin and by the tests. The position can be changed through position_mm, for instance
by a simulated motor, and the reading is quantized to the 10 nm measuring step of the LC 483.
"""
import random

MEASURING_STEP_MM = 10e-6  # 10 nm, measuring step of the LC 483 returned by IK220ConfigEn


class IK220Mock:
    """Fake of IK220, with the same public methods and attributes."""
    units = 'mm'

    def __init__(self, dllpath=None, axis=1, position_mm=158.44, noise_mm=10e-6):
        self.axis = []
        self.encoder_axis = axis
        self.signal_period_nm = None
        self.position_mm = position_mm  # true position of the simulated encoder
        self.noise_mm = noise_mm  # standard deviation of the reading noise
        self.get_present_axis()
        if self.encoder_axis not in self.axis:
            raise ValueError(f'Axis {self.encoder_axis} not found on the IK 220 cards, present axes: {self.axis}')
        self.config_endat()

    def config_endat(self):
        """Simulates the configuration: gives the signal period of the LC 483."""
        self.signal_period_nm = 20000

    def get_present_axis(self):
        """One simulated card, with two axes."""
        self.axis = [0, 1]
        return f'Axis {self.axis} are present'

    def get_axis_position(self):
        """Position in mm, with noise, quantized to the measuring step."""
        reading = self.position_mm + random.gauss(0., self.noise_mm)
        return round(reading / MEASURING_STEP_MM) * MEASURING_STEP_MM
