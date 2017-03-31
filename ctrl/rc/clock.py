if __name__ == "__main__":

    import sys
    sys.path.append('.')

import warnings
from time import perf_counter

from ctrl import block
from ctrl.block import clock as clk

import rc
from rc import mpu9250

# make sure it is disabled when destroyed
import atexit; atexit.register(mpu9250.power_off)

# Uses Alex Martelli's Borg for making Clock a singleton
class MPU9250Clock(clk.Clock):

    _shared_state = {}

    def __init__(self, **kwargs):

        # Makes sure clock is a singleton
        self.__dict__ = self._shared_state

        # Do not initialize if already initialized
        if not self.__dict__ == {}:
            warnings.warn('> Clock is already initialized. Skipping call to __init__')
            return

        self.period = kwargs.pop('period', 0.01)
        
        # call super
        super().__init__(**kwargs)

        # set period
        self.set_period(self.period)

        # initialize imu 
        self.imu = None
        self.read()

    def set(self, exclude = (), **kwargs):
        """
        Set properties of `Clock`. 

        :param tuple exclude: list of attributes to exclude
        :param float period: clock period
        :param kwargs: other keyword arguments
        :raise: `BlockException` if any of the `kwargs` is left unprocessed
        """

        if 'period' in kwargs:
            self.period = kwargs.pop('period')

        # call super
        return super().set(exclude, **kwargs)

    def set_period(self, period):
        """
        Set `Clock` period.

        :param float period: clock period
        """
        
        warnings.warn('> Setting clock period to {}s'.format(period))
            
        # set period
        self.period = period

        # initialize mpu9250
        mpu9250.initialize(enable_dmp = True,
                           dmp_sample_rate = int(1/self.period))
        
    def get_period(self):
        """
        Get `TimerClock` period.

        :return: clock period
        :retype: float
        """
        return self.period
    
    def get_imu(self):

        return self.imu

    def read(self):

        #print('> read')
        if self.enabled and rc.get_state() == rc.RUNNING:

            # Read imu (blocking call)
            self.imu = mpu9250.read()
            
        # Call super.read
        return super().read()

if __name__ == "__main__":

    import time, math

    import rc
    rc.set_state(rc.RUNNING)

    Ts = 0.01
    clock = Clock(period = Ts)
    
    print("\n> Testing Clock @{} Hz".format(1/Ts))

    N = int(5/Ts)
    (t0,) = clock.read()
    avg = 0
    mx = 0
    for k in range(1,N):

        (t1,) = clock.read()
        dt = 1000 * (t1 - t0)
        t0 = t1
        avg = ((k-1)/k) * avg + (1/k) * dt
        mx = max(dt, mx)
        print('\r dt = {:7.3f} ms  average = {:7.3f} ms   max = {:7.3f} ms'.format(dt, avg, mx), end='')

    print()
    
    Ts = 0.25;
    clock.set_period(Ts)
    
    print("\n> Testing Clock @{} Hz".format(1/Ts))

    N = int(5/Ts)
    (t0,) = clock.read()
    avg = 0
    mx = 0
    for k in range(1,N):

        (t1,) = clock.read()
        dt = 1000 * (t1 - t0)
        t0 = t1
        avg = ((k-1)/k) * avg + (1/k) * dt
        mx = max(dt, mx)
        print('\r dt = {:7.3f} ms  average = {:7.3f} ms   max = {:7.3f} ms'.format(dt, avg, mx), end='')