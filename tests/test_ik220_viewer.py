"""Behaviour tests of the IK220 viewer against the simulated card (no hardware, no visible GUI)."""
import pytest

from pymodaq.utils.plugin_testing import make_detector, grab_and_wait, assert_units

from pymodaq_plugins_heidenhain.daq_viewer_plugins.plugins_0D.daq_0Dviewer_IK220 import DAQ_0DViewer_IK220


@pytest.fixture
def detector(qapp):
    plugin = make_detector(DAQ_0DViewer_IK220, mode='MOCK')
    assert plugin.initialized
    yield plugin
    plugin.close()


def test_initialization_shows_the_signal_period(detector):
    assert detector.settings['signal_period'] == 20000


def test_grab_returns_one_position_in_mm(detector):
    dte = grab_and_wait(detector)
    assert len(dte) == 1
    assert_units(dte, 'mm')
    assert dte[0].data[0][0] == pytest.approx(158.44, abs=0.001)


def test_absent_axis_fails_the_initialization(qapp):
    with pytest.raises(ValueError):
        make_detector(DAQ_0DViewer_IK220, mode='MOCK', axis=2)


def test_close_releases_the_controller(detector):
    detector.close()
    assert detector.controller is None
