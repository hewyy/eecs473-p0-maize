#!/usr/bin/env python

'''
FILE demo-turning.py

This file is used to control a robot with two servos.

TODO: add more text here
'''

from joy.plans import Plan
from joy import JoyApp
from joy.decl import *
from joy.misc import *
from joy import *
import ckbot
import time


# TODO: change these as needed to acheive the correct FORWARD motion
THRUST_DN = 4500 # <-- inrease magnitude to make thruster scoop lower
THRUST_UP = -9000 # <-- increase magnitude to make thruster raise higher


# TODO: change these as needed to acheive the correct TURNING motion
# thrusting servo pos
POS_DN = 6000 
POS_UP = -7000 

# turning servo pos
POS_TL = -8577
POS_TR = 8577
POS_CT = 0

TURN_DELTA = 6000


class Move:

    def __init__(self, servo, start_pos, end_pos, speed, run_short = False):
        self.servo = servo
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.speed = speed


        self.servo.set_speed(speed)
        real_speed = self.servo.get_moving_speed() # the speed we set is not the acutal speed in the register, some API problems?


        angle_delta = abs(self.start_pos - self.end_pos) / 100.0


        # estamted time it will take to complete the rotation (in ms)
        self.rt_estimate = (5.0/3.0)*angle_delta/abs(real_speed) - run_short # this is the estimated time it will take to make the rotation

        if run_short:
            self.rt_estimate = self.rt_estimate - self.rt_estimate*0.03


        ##### explaing in the 5/3 above #######
        #   we need the angualr change to be in terms of rotation, 
        #        rotation amount = angle_delta / 36000 
        #
        #   we also need the to convert the speed to be in terms of ms
        #        rp(ms) = rmp / 60000
        #
        #  finally, we need to etimate the time, so 
        #       time = rotation amount / rp(ms)
        # 
        #  the 5/3 is just 60000 / 36000


    def run(self):
        self.servo.set_speed(self.speed)
        self.servo.set_pos(self.end_pos)
        time.sleep((self.rt_estimate / 10.0))
        return


class Routine:

    def __init__(self, moves):
        self.moves = moves

    def execute(self):
        for move in self.moves:
            move.run()


class P0App( JoyApp ):
    '''
    The P0App handles keyboard events to stop or start plans.
    '''

    '''
    This searches for three servors named 'front', 'middle', and 'back'
    It overrides anything specified in the .yml file.

    Servos are initialized and plans are created.
    '''
    def __init__(self,robot=dict(count=2),*arg,**kw):
        cfg = dict ()

        # initializes the application's app.robot attribute
        JoyApp.__init__(self,robot=robot,cfg=cfg,*arg,**kw)

        # Handle connecting to the servos
        c = ckbot.logical.Cluster(count=2, names={
          0x35: 'thrust',
          0x08: 'turn',
        })

        # servo defintions
        self.thrust = c.at.thrust
        self.turn = c.at.turn

        self.moving_forward = False


        self.turn_left = Routine([
                            Move(self.turn, POS_CT, POS_TL, 100), 
                            Move(self.thrust, POS_DN, POS_UP, 100),
                            Move(self.turn, POS_TL, POS_CT, 100),
                            Move(self.thrust, POS_UP, POS_DN, 100)
                            ])

        self.turn_right = Routine([
                            Move(self.turn, POS_CT, POS_TR, 100), 
                            Move(self.thrust, POS_DN, POS_UP, 100),
                            Move(self.turn, POS_TR, POS_CT, 100),
                            Move(self.thrust, POS_UP, POS_DN, 100)
                            ])

        self.turn_left_small = Routine([
                            Move(self.turn, POS_CT, POS_TL + TURN_DELTA, 100), 
                            Move(self.thrust, POS_DN, POS_UP, 100),
                            Move(self.turn, POS_TL + TURN_DELTA, POS_CT, 100),
                            Move(self.thrust, POS_UP, POS_DN, 100)
                            ])

        self.turn_right_small = Routine([
                            Move(self.turn, POS_CT, POS_TR - TURN_DELTA, 100), 
                            Move(self.thrust, POS_DN, POS_UP, 100),
                            Move(self.turn, POS_TR - TURN_DELTA, POS_CT, 100),
                            Move(self.thrust, POS_UP, POS_DN, 100)
                            ])        

        self.move_forward = Routine([
                            Move(self.thrust, THRUST_DN, THRUST_UP, 100), 
                            Move(self.thrust, THRUST_UP, THRUST_DN, 15, run_short = True)
                            ])



    def move_to_pos(self, servo, pos):
        servo.set_pos(pos)
        try:
            while(servo.mem_read(b'\x2e') == 1):
                continue
        except:
            return 


    def onStart(self):
        """
        Don't act until told to start moving forward
        Doesn't take any actions in onStart
        """
        progress("Started program")

    def stopAllPlans(self):
        """
        Helper function to stop all the plans. This will
        stop all the plans running without regard to whether they are
        currently active or not.

        This is called before starting a new plan.
        """
        progress("Stop all plans called")
        # self.move_forward.stop()


    def onEvent(self,evt):
        # assertion: must be a KEYDOWN event

        if evt.type != KEYDOWN:
            return

        # MOVING LEFT
        if evt.key == K_LEFT:
            self.turn_left.execute()


        # MOVING LEFT - small
        elif evt.key == K_a:
            self.turn_left_small.execute()

        # MOVING RIGHT
        elif evt.key == K_RIGHT:
            self.turn_right.execute()


        # MOVING RIGHT - small
        elif evt.key == K_d:
            self.turn_right_small.execute()


        # MOVE FORWARD
        elif evt.key == K_UP:
            moving_forward = True
            self.move_forward.execute()


        #  vv BELOW IS FOR TESTING vv #

        # THRUST UP
        elif evt.key == K_w:
            self.move_to_pos(self.thrust, POS_UP)

        # THRUST DOWN
        elif evt.key == K_s:
            self.thrust.set_speed(7)
            self.move_to_pos(self.thrust, POS_DN)
            self.thrust.set_speed(0)
        
        # RESET ARM POSIION
        elif evt.key == K_RSHIFT:
            self.move_to_pos(self.thrust, POS_CT)
            self.move_to_pos(self.turn, POS_CT)


        # Hide robot position events
        elif evt.type==CKBOTPOSITION:
            return

        # Send events to JoyApp if not recognized
        JoyApp.onEvent(self,evt)

    def onStop(self):
        """
        Stops any plans that may be running
        """
        progress("P0App: onStop called")
        self.stopAllPlans()

#main function
if __name__=="__main__":
    app = P0App()
    app.run()
