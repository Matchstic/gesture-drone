import time

'''
Throttle is driven by linear acceleration in the z axis.

The idea is that the user's movement is tracked to find the peak
acceleration before movement slows again. This is then translated
into a decay function, which reduces the throttle over time.

The greater the acceleration, the longer this decay occurs, resulting
in a longer period of acceleration on the remote hardware. As a result,
this produces a larger vertical translation.
'''
class Throttle():
    BASE          = 0
    PEAK          = 1
    WAIT          = 2

    state         = BASE
    direction     = 0
    value         = 0.5
    previous      = []
    peakValue     = 0.0
    waitStart     = 0
    waitDuration  = 0
    peakStart     = 0

    PEAK_TIMEOUT  = 500

    def tick(self, vel, midpoint):
        computed = 0
        if vel > 0:
            computed = ((vel * 1.4) + 100) / 200.0
        elif vel < 0:
            computed = ((vel * 1.8) + 100) / 200.0

        # State handling
        if self.state == Throttle.BASE:
            if vel > midpoint:
                self.state = Throttle.PEAK
                self.direction = 1
                self.peakStart = time.ticks_ms()
            elif vel < 0 - midpoint:
                self.state = Throttle.PEAK
                self.direction = -1
                self.peakStart = time.ticks_ms()

        elif self.state == Throttle.PEAK:
            directionCheck = False

            if self.direction == 1:
                directionCheck = vel < self.peakValue
                self.peakValue = vel if vel >= self.peakValue else self.peakValue
            elif self.direction == -1:
                directionCheck = vel > self.peakValue
                self.peakValue = vel if vel <= self.peakValue else self.peakValue

            # Only change current throttle when heading towards peak, and ignore
            # lower values when velocity is dropped due to reduced motion.
            if not directionCheck:
                self.value = computed

            # Check previous and current, then see if we're in the endgame
            allInBounds = True
            for prev in self.previous:
                if not (prev > 0 - midpoint and prev < midpoint):
                    allInBounds = False

            diff = time.ticks_diff(time.ticks_ms(), self.peakStart)

            if (vel > 0 - midpoint and vel < midpoint and allInBounds) or diff > Throttle.PEAK_TIMEOUT:
                # reset to baseline
                #self.waitStart = time.ticks_ms()
                #self.waitDuration = abs(((self.value - 0.5) * 2) * 50) + 40

                #print('>>>> RESET WITH duration: ' + str(self.waitDuration))

                #self.state = Throttle.WAIT

                self.state = Throttle.BASE
                self.value = 0.5
                self.peakValue = 0.0

        elif self.state == Throttle.WAIT:
            diff = time.ticks_diff(time.ticks_ms(), self.waitStart)

            if diff > self.waitDuration:
                self.waitStart = 0
                self.state = Throttle.BASE
                self.value = 0.5
                self.peakValue = 0.0

        if len(self.previous) >= 5:
            self.previous.pop()

        self.previous.append(vel)

    def compute(self):
        return self.value