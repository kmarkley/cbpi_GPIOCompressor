from modules import cbpi
from modules.base_plugins.gpio_actor import *
from modules.core.props import Property
from datetime import datetime, timedelta

cbpi.gpio_compressors = []

class Compressor(object):
    c_delay = Property.Number("Compressor Delay", True, 10, "minutes")
    d_cycle_on = Property.Number("Compressor Duty Cycle On", True, 180, "minutes")
    e_cycle_off = Property.Number("Compressor Duty Cycle Off", True, 30, "minutes")

    def init(self):
        super(Compressor, self).init()
        cbpi.gpio_compressors += [self]

        self.actor_is_off = True
        self.compressor_is_on = False
        self.compressor_last_off = datetime(1,1,1)

        self.delayed = False
        self.delayed_on_time = datetime.now()

        self.cycle_rest = False
        self.cycle_on_time = datetime.now()
        self.cycle_off_time = self.cycle_on_time + timedelta(minutes=int(self.d_cycle_on))

        cbpi.app.logger.info("GPIOCompressor: '{}' initialized".format(self.name))


    def on(self, power=100):
        # actor was just turned on
        if self.actor_is_off:
            # set flag so this only executes once
            self.actor_is_off = False
            # reset active duty cycle
            if not self.cycle_rest:
                next_on = max(datetime.now(),self.delayed_on_time)
                if next_on >= self.compressor_last_off + timedelta(minutes=int(self.e_cycle_off)):
                    # if the actor has been off longer than the duty cycle rest, then reset the duty cycle
                    self.cycle_off_time = next_on + timedelta(minutes=int(self.d_cycle_on))
                else:
                    # otherwise, add the time spent turned off to the current duty cycle
                    self.cycle_off_time = self.cycle_off_time + (next_on - self.compressor_last_off)

        self.automatic(power)


    def off(self):
        # actor was just turned off
        if not self.actor_is_off:
            # set flag so this only executes once
            self.actor_is_off = True
            # set dalayed state
            self.delayed = True
            # determine when the delay ends
            self.delayed_on_time = datetime.now() + timedelta(minutes=int(self.c_delay))
            # write to log
            cbpi.app.logger.info("GPIOCompressor: '{}' delayed until {}".format(self.name, self.delayed_on_time))

        self.automatic()


    def automatic(self, power=100):

        # check if delay has expired
        if self.delayed:
            if datetime.now() >= self.delayed_on_time:
                # unset delayed state
                self.delayed = False
                # write to log
                cbpi.app.logger.info("GPIOCompressor: '{}' delay ended".format(self.name))

        # check if the rest duty cycle has expired
        if self.cycle_rest:
            if datetime.now() >= self.cycle_on_time:
                # unset rest state
                self.cycle_rest = False
                # write to log
                cbpi.app.logger.info("GPIOCompressor: '{}' duty cycle active until {}".format(self.name, self.cycle_off_time))

        # check if the active duty cycle has expired
        else:
            if datetime.now() >= self.cycle_off_time:
                # set rest state
                self.cycle_rest = True
                # determine when the rest cycle ends
                self.cycle_on_time = datetime.now() + timedelta(minutes=int(self.e_cycle_off))
                # detrmine when the next active cycle ends (overwritten if actor is turned off/on)
                self.cycle_off_time = self.cycle_on_time + timedelta(minutes=int(self.d_cycle_on))
                # write to log
                cbpi.app.logger.info("GPIOCompressor: '{}' duty cycle rest until {}".format(self.name, self.cycle_on_time))

        # act on compressor
        # cbpi.app.logger.info("GPIOCompressor: '{}' off:{} delayed:{} rest:{}".format(self.name, self.actor_is_off, self.delayed, self.cycle_rest))
        if self.actor_is_off or self.delayed or self.cycle_rest:
            self.compressor_off()
        else:
            self.compressor_on(power)


    def compressor_on(self, power=100):
        if not self.compressor_is_on:
            self.compressor_is_on = True
            cbpi.app.logger.info("GPIOCompressor: '{}' compressor now running".format(self.name))
        super(Compressor, self).on(power)


    def compressor_off(self):
        if self.compressor_is_on:
            self.compressor_is_on = False
            self.compressor_last_off = datetime.now()
            cbpi.app.logger.info("GPIOCompressor: '{}' compressor now off".format(self.name))
        super(Compressor, self).off()


@cbpi.backgroundtask(key="update_compressors", interval=5)
def update_compressors(api):
    for compressor in cbpi.gpio_compressors:
        compressor.automatic()

@cbpi.actor
class RelayCompressor(Compressor, RelayBoard):
    pass

@cbpi.actor
class GPIOCompressor(Compressor, GPIOSimple):
    pass
