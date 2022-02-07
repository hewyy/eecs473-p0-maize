#!/usr/bin/env python

'''
FILE main.py

This file is used to control a robot with two servos.
Two main classes are defined in order to control the robots execution.

'''

from joy.plans import Plan
from joy import JoyApp
from joy.decl import *
from joy.misc import *
from joy import *
import ckbot
import time


# change these as needed to acheive the correct FORWARD motion
THRUST_DN = 4500 # <-- inrease magnitude to make thruster scoop lower
THRUST_UP = -9000 # <-- increase magnitude to make thruster raise higher


# change these as needed to acheive the correct TURNING motion
# thrusting servo pos
POS_DN = 6000 
POS_UP = -7000 

# turning servo pos
POS_TL = -8577
POS_TR = 8577
POS_CT = 0

# use to change the min turing amount
TURN_DELTA = 6000


class Move:
    '''
    A Move representes moving a single servo to a goal angle
    '''

    def __init__(self, servo, start_pos, end_pos, speed = 113, run_short = False):
        '''
        Creates new Move oject that takes on properties of the passed in parameters
        Also calucaltes the estimated time it will take for the move to execute
        '''
        self.servo = servo
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.speed = speed


        # the speed we set is not the acutal speed in the register, a bug in the API perhaps?
        self.servo.set_speed(speed)
        real_speed = self.servo.get_moving_speed() 

        # find the displacment angle
        angle_delta = abs(self.start_pos - self.end_pos) / 100.0


        # estamted time it will take to complete the rotation (in ms)
        self.rt_estimate = (5.0/3.0)*angle_delta/abs(real_speed) - run_short

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


        # change the estimate to be shorter, allows for smoother motion in cycles
        if run_short:
            self.rt_estimate = self.rt_estimate - self.rt_estimate*0.03



    def run(self):
        '''
        Sets the speed of the servo and then sets the position
        Yes, this is a blocking function call, but it's faster and more consistant than ckbot 
        '''
        self.servo.set_speed(self.speed)
        self.servo.set_pos(self.end_pos)
        time.sleep((self.rt_estimate / 10.0)) # sleep() is in minutes to we convert
        return


class Routine:
    '''
    A Routine is a collection of Moves which can be execuited in sequence
    '''
    def __init__(self, moves):
        '''
        Creates new Routine object
        '''
        self.moves = moves

    def execute(self):
        '''
        Runs through every move in the routine and runs the move
        '''
        for move in self.moves:
            move.run()


class P0App( JoyApp ):
    '''
    The P0App handles keyboard events and executes different routines
    '''

    def __init__(self,robot=dict(count=2),*arg,**kw):
        '''
        Initilizes a new P0App object, also creates the Routines
        '''
        
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


        # Create Routines
        self.turn_left = Routine([
                            Move(self.turn, POS_CT, POS_TL), 
                            Move(self.thrust, POS_DN, POS_UP),
                            Move(self.turn, POS_TL, POS_CT),
                            Move(self.thrust, POS_UP, POS_DN)
                            ])

        self.turn_right = Routine([
                            Move(self.turn, POS_CT, POS_TR), 
                            Move(self.thrust, POS_DN, POS_UP),
                            Move(self.turn, POS_TR, POS_CT),
                            Move(self.thrust, POS_UP, POS_DN)
                            ])

        self.turn_left_small = Routine([
                            Move(self.turn, POS_CT, POS_TL + TURN_DELTA), 
                            Move(self.thrust, POS_DN, POS_UP),
                            Move(self.turn, POS_TL + TURN_DELTA, POS_CT),
                            Move(self.thrust, POS_UP, POS_DN)
                            ])

        self.turn_right_small = Routine([
                            Move(self.turn, POS_CT, POS_TR - TURN_DELTA), 
                            Move(self.thrust, POS_DN, POS_UP),
                            Move(self.turn, POS_TR - TURN_DELTA, POS_CT),
                            Move(self.thrust, POS_UP, POS_DN)
                            ])        

        self.move_forward = Routine([
                            Move(self.thrust, THRUST_DN, THRUST_UP), 
                            Move(self.thrust, THRUST_UP, THRUST_DN, speed = 9, run_short = True)
                            ])



    def move_to_pos(self, servo, pos):
        """
        Moves the servo to the correct positoion and returns after the position is reached
        Yes, this is a blocking function call, but it is faster than the ckbot API!
        """
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

    def onStop(self):
        """
        Stops any plans that may be running
        """
        progress("P0App: onStop called")

    def onEvent(self,evt):
        """
        Called when there is pygame event
        Executes a Routine based on the key pressed
        """

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
            self.move_forward.execute()

        # THRUST UP
        elif evt.key == K_w:
            self.move_to_pos(self.thrust, POS_UP)

        # THRUST DOWN
        elif evt.key == K_s:
            self.thrust.set_speed(10)
            self.move_to_pos(self.thrust, POS_DN)
            self.thrust.set_speed(0)
        
        # RESET ARM POSIION
        elif evt.key == K_RSHIFT:
            self.thrust.set_speed(0)
            self.move_to_pos(self.thrust, POS_CT)
            self.move_to_pos(self.turn, POS_CT)

        # Hide robot position events
        elif evt.type==CKBOTPOSITION:
            return

        # Send events to JoyApp if not recognized
        JoyApp.onEvent(self,evt)


#main function
if __name__=="__main__":
    app = P0App()
    app.run()
