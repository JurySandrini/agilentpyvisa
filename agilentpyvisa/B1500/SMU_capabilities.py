from logging import getLogger
from .helpers import format_command
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *

class SweepUnit(object):
    """ Common functionality of pulsed sweep and staircase weep"""

    def set_sweep_auto_abort(self, auto_abort):
        exception_logger.info("Setting GLOBAL parameter SweepAbort")
        return self.parent.write("WM {}".format(auto_abort))

    def set_sweep_timing(
        self,
        hold,
        delay,
        step_delay=None,
     output_trigger_delay=None):
        exception_logger.info("Setting GLOBAL parameter SweepTiming")
        return self.parent.write(
            format_command(
                "WT",
                hold,
                delay,
                step_delay,
                output_trigger_delay))


class PulseUnit(object):
    """ Shared Functionality of PulsedSpot and PulsedSweep"""

    def set_pulse_timing(self, hold, width, period):
        """ Sets up the pulse timing parameters for SMU pulsed sweep and spot"""
        self.parent.write(
            format_command("PT",
                           hold,
                           width,
                           period))


class StaircaseSweepUnit(SweepUnit):

    def set_staircase_sweep_current(
        self,
        channel,
        sweepmode,
        input_range,
        start,
        stop,
        step,
        Vcomp,
     power_comp):
        return self.parent.write(
            format_command(
                "WI",
                channel,
                sweepmode,
                input_range,
                start,
                stop,
                stop,
                Vcomp,
                power_comp))

    def set_staircase_sweep_voltage(
        self,
        channel,
        sweepmode,
        input_range,
        start,
        stop,
        step,
        Icomp,
     power_comp):
        return self.parent.write(
            format_command(
                "WV",
                channel,
                sweepmode,
                input_range,
                start,
                stop,
                stop,
                Icomp,
                power_comp))

    def setup_staircase_sweep(self, channel, staircase_setup):
        if channel not in self.channels:
            raise ValueError(
                "Trying to set nonexistent channel {} in SMU on slot {}".format(
                    channel, self.slot))
        self.measurements[channel] = staircase_setup
        self.set_sweep_timing(staircase_setup.hold, staircase_setup.delay)
        self.set_sweep_auto_abort(staircase_setup.auto_abort)
        if staircase_setup.input == Inputs.V:
            return self.set_staircase_sweep_voltage(
                channel,
                staircase_setup.sweepmode,
                staircase_setup.input_range,
                staircase_setup.start,
                staircase_setup.stop,
                staircase_setup.step,
                staircase_setup.compliance,
                staircase_setup.power_comp)
        else:
            return self.set_staircase_sweep_current(
                channel,
                staircase_setup.sweepmode,
                staircase_setup.input_range,
                staircase_setup.start,
                staircase_setup.stop,
                staircase_setup.step,
                staircase_setup.compliance,
                staircase_setup.power_comp)

    def setup_staircase_measure(self, channel, measure_setup):
        raise NotImplementedError()


class SingleMeasure(object):


    def set_measure_side(self,channel, side):
        """ Specify whether the sensor should read on the current, voltage,
        compliance or force side. See MeasureSides"""
        self.parent.write("CMM {},{}".format(channel, side))

    def set_measure_range(self,channel, target, range):
        """ Sets measure ranges out of available Ranges. The less range changes,
        the faster the measurement. Thus the spees increases from full_auto to
        limited to fixed. See MeasureRanges_X for availble values"""
        if target == Inputs.V:
            self.parent.write(
                "RV {},{}".format(
                    channel,
                    range))  # sets channel adc type
        else:
            self.parent.write(
                "RI {},{}".format(
                    channel,
                    range))  # sets channel adc type

    def _setup_xe_measure(self,config, channel=None):
        """ Configures most XE triggered measurements. """
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        if config.mode not in tuple([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_side(channel, config.side)
        if config.mode not in tuple([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_range(channel, config.target, config.range)


class DCForceUnit(object):
    def force_voltage(self,
            channel,
            input_range,
            value,
            compliance,
            polarity=None,
            compliance_range=None):
        return self.parent.write(format_command("DV",
                                                channel,
                                                input_range,
                                                value,
                                                compliance,
                                                polarity,
                                                compliance_range,)
                                    )
    def setup_dc_force(self, channel, force_setup):
        """ Sets up the channel configuration for forcing a DC force or current."""
        if force_setup.input_range not in self.input_ranges:
            raise ValueError(
                "Input range {} of channel {} not available in installed module {}".format(
                    repr(
                        force_setup.input_range),
                    channel,
                    self))
        if force_setup.input == Inputs.V:
            return self.force_voltage(
                channel,
                force_setup.input_range,
                force_setup.value,
                force_setup.compliance,
                force_setup.polarity,
                force_setup.compliance_range,
            )
        elif force_setup.input == Inputs.I:
            return self.force_current(
                channel,
                force_setup.input_range,
                force_setup.value,
                force_setup.compliance,
                force_setup.polarity,
                force_setup.compliance_range,
            )
        else:
            raise ValueError("Unkown Input {}".format(force_setup.input))

    def force_current(
            self,
            channel,
            input_range,
            value,
            compliance,
            polarity=None,
            compliance_range=None):
        return self.parent.write(
            format_command(
                "DI",
                channel,
                input_range,
                value,
                compliance,
                polarity,
                compliance_range,
                ))


class SpotUnit(SingleMeasure):

    def setup_spot_measure(self, measure_setup, channel=None):
        self._setup_xe_measure(measure_setup, channel)

class BinarySearchUnit(object):
    def setup_binarysearch_measure(self,measure_setup,channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        self.set_search_measure(measure_setup.mode)
        self.set_binary_search_output_mode(measure_setup.output_mode)
        self.set_binarysearch_controlmode(measure_setup.control_mode, measure_setup.auto_abort)
        self.set_binarysearch_timing(measure_setup.hold,measure_setup.delay)
        if measure_setup.target==Targets.I:
            self.set_binarysearch_condition_current(channel,measure_setup.searchmode,measure_setup.condition, measure_setup.measure_range, measure_setup.target_value)
        else:
            self.set_binarysearch_condition_voltage(channel,measure_setup.searchmode,measure_setup.condition, measure_setup.measure_range, measure_setup.target_value)

    def _validateSearchInput(self, inp, start, stop):
        for x in (start,stop):
            if inp == Inputs.V:
                if abs(x) >self._search_max_voltage:
                    raise ValueError("Invalid Search input, ensure both start and stop are smaller than +- {}".format(self._search_max_voltage))
            else:
                if abs(x) >self._search_max_current:
                    raise ValueError("Invalid Search input, ensure both start and stop are smaller than +- {}".format(self._search_max_current))
    def _validateCompliance(self, inp, compliance, start, stop):
        m = max([abs(start),abs(stop)])
        if inp == Inputs.V:
            check=[(m <= k,k) for k in self._search_compliance_current.keys()]
            if not any([x[0] for x in check]):
                raise ValueError("Invalid Search compliance, check page 4-24 in the manual for valid Icomp")
            if not any([ compliance <y for y in [ self._search_compliance_current[x[1]] for x in check if x[0]]]):
                raise ValueError("For your current start and stop, please choose one of the following Compliance values {}".format([self._search_compliance_current[x[1]] for x in check if x[0]]))
        else:
            check=[(m < k,k) for k in self._search_compliance_voltage.keys()]
            if not any([x[0] for x in check]):
                raise ValueError("Invalid Search compliance, check page 4-24 in the manual for valid Icomp")
            if not any([ compliance <y for y in [ self._search_compliance_voltage[x[1]] for x in check if x[0]]]):
                raise ValueError("For your voltage start and stop, please choose one of the following Compliance values {}".format([self._search_compliance_voltage[x[1]] for x in check if x[0]]))

    def setup_binarysearch_force(self, search_setup, channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        if search_setup.input==Inputs.I:
            if search_setup.start is not None:
                self._validateSearchInput(search_setup.input,search_setup.start,search_setup.stop, search_setup.input_range)
                self._validateCompliance(search_setup.input,search_setup.start,search_setup.stop, search_setup.input_range)
                self.set_binarysearch_current(channel,search_setup.start, search_setup.stop, search_setup.input_range, search_setup.compliance)
            elif search_setup.sync_polarity is not None:
                self.set_binarysearch_synchrous_current(channel,search_setup.sync_polarity, search_setup.sync_offset, search_setup.sync_compliance)
        else:
            if search_setup.start is not None:
                self._validateSearchInput(search_setup.input,search_setup.start,search_setup.stop, search_setup.input_range)
                self._validateCompliance(search_setup.input,search_setup.start,search_setup.stop, search_setup.input_range)
                self.set_binarysearch_voltage(channel,search_setup.start, search_setup.stop, search_setup.input_range, search_setup.compliance)
            elif search_setup.sync_polarity is not None:
                self.set_binarysearch_synchrous_voltage(channel,search_setup.sync_polarity, search_setup.sync_offset, search_setup.sync_compliance)

    def set_binarysearch_controlmode(self, controlmode, auto_abort):
        self.parent.write(format_command("BSM",controlmode,auto_abort))

    def set_binarysearch_condition_current(self,channel,searchmode,condition,measure_range,target_value):
        self.check_search_target(Targets.I,target_value)
        self.parent.write(format_command("BGI",channel, searchmode, condition,measure_range,target_value))

    def set_binarysearch_condition_voltage(self,channel,searchmode,condition,measure_range,target_value):
        self.check_search_target(Targets.V,target_value)
        self.parent.write(format_command("BGV",channel, searchmode, condition,measure_range,target_value))

    def set_binarysearch_synchrous_voltage(self, channel,polarity,offset,compliance):
        self.parent.write(format_command("BSSV",channel,polarity,offset,compliance))

    def set_binarysearch_synchrous_current(self, channel,polarity,offset,compliance):
        self.parent.write(format_command("BSSI",channek,polarity,offset,compliance))

    def set_binarysearch_voltage(self, channel,start,stop,input_range,compliance):
        self.parent.write(format_command("BSV",channel,input_range,start,stop,compliance))

    def set_binarysearch_current(self, channel,start,stop,input_range,compliance):
        self.parent.write(format_command("BSI",channel,input_range,start,stop,compliance))

    def set_binarysearch_timing(self, hold, delay):
        self.parent.write(format_command("BST",hold, delay))

    def set_binary_search_output_mode(self, output):
        self.parent.write("BSVM {}".format(output))

    def set_search_measure(self, mode):
        self.parent.write("MM {}".format(mode))
