# from itertools import zip_longest
from collections import OrderedDict
from functools import wraps
from .tests import *
format1 = 1
def minCoverRange(start,stop):
    return False

class DummyTester():
    def __init__(self):
        pass
    def query(*args,**kwargs):
        print(*[x for x in args if isinstance(x,str)])
        if kwargs:
            print(kwargs)
        return False
class B1500():
    def __init__(self):
        self._device = DummyTester()  # open pyvisa device
        self.tests = OrderedDict()

    def init(self):
        self.reset()
        self.check_err()

    def reset(self):
        self._device.query("*RST?")
    def operations_completed(self):
        return self._device.query("*OPC?")

    def add_test(name, test_tuple):
        self.tests[name]=test_tuple

    def enable_timestamp(self, state):
        if state:
            self._device.query("TSC {}".format(1))
        else:
            self._device.query("TSC {}".format(0))

    def check_err(self):
        pass
    def DC_V_sweep(self, input_channel,ground_channel,start,stop,step,compliance,input_range=None,sweepmode=SweepMode.linear_up_down,power_comp=None,measure_range=MeasureRanges.full_auto):
        measure_setup=Measurement(target=Inputs.I, mode=MeasureModes.staircase_sweep,side=MeasureSides.current_side,range=measure_range)
        if input_range is None:
            input_range = minCoverRange(start,stop)
        sweep_setup=StaircaseSweep(input=Inputs.V,start=start,stop=stop,step=step,sweepmode=sweepmode,compliance=compliance,auto_abort=AutoAbort.enabled,input_range=input_range,power_comp=power_comp)
        in_channel= Channel(number=input_channel,measurement=measure_setup,staircase_sweep=sweep_setup)
        ground_setup=DCForce(input=Inputs.V,value=0,compliance=compliance)
        ground= Channel(number=ground_channel,dcforce=ground_setup)
        test = TestSetup(channels=[in_channel,ground])
        self.run_test(test)

    def run_test(self, test_tuple):
        measurements = []
        self.set_format(test_tuple.format,test_tuple.output_mode)
        self.set_filter(test_tuple.filter)
        self.enable_timestamp(True)
        self.set_adc_global(adc_modes=test_tuple.adc_modes,
                     highspeed_adc_number=test_tuple.highspeed_adc_number,
                     highspeed_adc_mode = test_tuple.highspeed_adc_mode)
        for channel in test_tuple.channels:
            self.setup_channel(channel)
            if channel.measurement:
                measurements.append(channel.measurement)
        self.multi_setup(test_tuple.multi_setup)
        try:
            ret = self.execute(measurements) # resets timestamp, executes and optionally waits for answer, returns data with elapsed
        finally:
            for channel in test_tuple.channels:
                self.teardown_channel(channel)
        return ret

    def set_filter(self, filter):
        self._device.query("FL {}".format(filter))

    def multi_setup(self, multi_setup):
        pass

    def setup_channel(self, channel):
        #connect channel
        self._device.query("CN {}".format(channel.number))  # connect channel
        self._device.query("SSR {},{}".format(channel.number, channel.series_resistance))  # connects or disconnects 1MOhm series
        self._device.query("AAD {},{}".format(channel.number, channel.channel_adc))  # sets channel adc type
        # TODO add further channel and measurement setup
        if channel.measurement is not None:
            self.setup_measurement(channel.number, channel.measurement)
        if channel.dcforce is not None:
            self.dc_force(channel.number, channel.dcforce)
        elif channel.staircase_sweep is not None:
            self.staircase_sweep(channel.number, channel.staircase_sweep)
        elif channel.pulse_sweep is not None:
            self.pulse_sweep(channel.number, channel.pulse_sweep)
        elif channel.pulse is not None:
            self.pulse(channel.number, channel.pulse)
        elif channel.quasipulse is not None:
            self.quasipulse(channel.number, channel.quasipulse)
        elif channel.highspeed_spot is not None:
            self.highspeed_spot(channel.number, channel.highspeed_spot)
        elif channel.spot is not None:
            self.spot(channel.number, channel.spot)
        elif channel.SPGU is not None:
            self.SPGU(channel.number, channel.SPGU)

    def setup_measurement(self, channel_number, measurement):
        self._device.query("MM {},{}".format(measurement.mode, channel_number))  # connect channel
        self._device.query("CMM {},{}".format(channel_number, measurement.side))  # connects or disconnects 1MOhm series
        if measurement.target == Inputs.V:
            self._device.query("RI {},{}".format(channel_number, measurement.range))  # sets channel adc type
        else:
            self._device.query("RV {},{}".format(channel_number, measurement.range))  # sets channel adc type

    def dc_force(self,channel_number, force_setup):
        force_query = ",".join(["{}".format(x) for x in force_setup[1:]])
        if force_setup.input == Inputs.V:
            self._device.query("DV {},{}".format(channel_number, force_query))
        if force_setup.input == Inputs.I:
            self._device.query("DI {},{}".format(channel_number, force_query))

    def staircase_sweep(self, channel_number, sweep_setup):
        self._device.query("WT {},{}".format(sweep_setup.hold,sweep_setup.delay))
        self._device.query("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            self._device.query("WV {}".format(",".join(["{}".format(x) for x in sweep_setup[1:-3] if isinstance(x,IntEnum) ])))
        else:
            self._device.query("WI {}".format(",".join(["{}".format(x) for x in sweep_setup[1:-3] if isinstance(x,IntEnum) ])))

    def pulse_sweep(self, channel_number, sweep_setup):
        self._device.query("PT {},{}".format(sweep_setup.hold,sweep_setup.width, sweep_setup.period))
        self._device.query("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            self._device.query("PWV {}".format(",".join(["{}".format(x) for x in sweep_setup[1:-4] if x])))
        else:
            self._device.query("PWI {}".format(",".join(["{}".format(x) for x in sweep_setup[1:-4] if x])))

    def SPGU(channel_number):
        pass
        """
        session.WriteString("CN " & sp_ch(0) & "," & sp_ch(1) & vbLf) ’SPGU ch on
        ’37
        session.WriteString("SIM 0" & vbLf)
        ’PG mode
        session.WriteString("SPRM 2," & duration & vbLf)
        ’Duration mode
        session.WriteString("ODSW " & sp_ch(0) & ", 0" & vbLf) ’Disables pulse switch ’40
        session.WriteString("ODSW " & sp_ch(1) & ", 0" & vbLf)
        session.WriteString("SER " & sp_ch(0) & "," & loadz & vbLf)
        ’Load impedance
        session.WriteString("SER " & sp_ch(1) & "," & loadz & vbLf)
        session.WriteString("SPPER " & period & vbLf)
        ’Pulse period
        session.WriteString("SPM " & sp_ch(0) & ",1" & vbLf)
        ’2-level pulse setup
        ’45
        session.WriteString("SPT " & sp_ch(0) & ",1," & p1_del & "," & p1_wid & "," &
        p_lead & "," & p_trail & vbLf)
        session.WriteString("SPV " & sp_ch(0) & ",1," & p1_base & "," & p1_peak & vbLf)
        session.WriteString("SPM " & sp_ch(1) & ",3" & vbLf)
        ’3-level pulse setup
        ’48
        session.WriteString("SPT " & sp_ch(1) & ",1," & p2_del1 & "," & p2_wid1 & "," &
        p_lead & "," & p_trail & vbLf)
        session.WriteString("SPT " & sp_ch(1) & ",2," & p2_del2 & "," & p2_wid2 & "," &
        p_lead & "," & p_trail & vbLf)
        session.WriteString("SPV " & sp_ch(1) & ",1," & p2_base1 & "," & p2_peak1 & vbLf)
        session.WriteString("SPV " & sp_ch(1) & ",2," & p2_base2 & "," & p2_peak2 & vbLf)
        session.WriteString("SPUPD" & sp_ch(0) & "," & sp_ch(1) & vbLf) ’Apply setup ’53
        """


    def teardown_channel(self, channel):
        # force voltage to 0
        self._device.query("DZ {}".format(channel.number))
        #disconnect channel
        self._device.query("CL {}".format(channel.number))

    def set_format(self, format, output_mode):
        self._device.query("FMT {},{}".format(format, output_mode))

    def execute(self, measurements, force_wait=False, autoread=True):
        self._device.query("XE")
        if autoread:
            return self._device.query("NUB?")

    def set_adc_global(self, adc_modes=[], highspeed_adc_number=None, highspeed_adc_mode=None):
        if adc_modes:
            for setting in adc_modes:
                self._device.query("AIT {}".format(",".join(["{}".format(x) for x in setting])))
        else:
            if  highspeed_adc_number is None or highspeed_adc_mode is None:
                raise ValueError("Either give complete adc mapping or specify highspeed ADC")
            self._device.query("AV {}, {}".format(highspeed_adc_number, highspeed_adc_mode))

    def setup_pulse(self,chan_dict):
        for c, setup in chan_dict.items():
            self._device.query(
                "PT {hold}, {width}, {period}, {tdelay}".format(
                    mode=setup["measurement"]["mode"],
                    channel=c))
            self._device.query(
                "PV {channel},{vrange},{base},{pulse},{Icomp}".format(
                    mode=setup["measurement"]["mode"],
                    channel=c))
            self._device.query("RI {channel},{measure_range}".format(
                measure_range=setup["measurement"]["measure_range"], channel=c))
