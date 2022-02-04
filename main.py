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



# TODO: change these as needed to acheive the correct FORWARD motion
THRUST_DN = 1000 # <-- inrease magnitude to make thruster scoop lower
THRUST_UP = -8000 # <-- increase magnitude to make thruster raise higher



# TODO: change these as needed to acheive the correct TURNING motion
# thrusting servo pos
POS_DN = 6000 
POS_UP = -4000 

# turning servo pos
POS_TL = -8577
POS_TR = 8577
POS_CT = 0



class Servo:
    def __init__(self, servo, min_pos=-10000, max_pos=10000, pos_step=100, start_pos=0, run=True, *arg,**kw):
        """A helper class to handle servo interactions

        Args:
            servo: The physical servo from pyckbot
            min_pos: The minimum position the servo can be set to
            max_pos: The maximum position the servo can be set to
            pos_step: The amount to change the servo position each time
                change_pos is called
            start_pos: The position the servo should be set to when starting
                the plan.
            run: Whether the server should change its position after being set
                to the start position. If False, the servo will not take any
                further movement.

        Returns:
            An instance of a Servo class.
        """
        self.name = servo.name
        self.start_pos = start_pos
        self.max_pos = max_pos
        self.min_pos = min_pos
        self.pos_step = pos_step
        self.increase = True
        self.servo = servo
        self.run = run

    def increase_pos(self):
        """
        Increases the position of a servo by the position step.
        Only changes the position if self.run == True
        """
        if self.run:
            self.set_pos(self.current_pos + self.pos_step)

    def decrease_pos(self):
        """
        Decreases the position of a servo by the position step.
        Only changes the position if self.run == True
        """
        if self.run:
            self.set_pos(self.current_pos - self.pos_step)

    def set_pos(self, pos):
        """Sets the position of the servo to pos

        Args:
            pos: A positive or negative value to set the position to
        """
        self.servo.set_pos(pos)
        self.current_pos = pos

    def change_pos(self):
        """Decides how to change the position of the servo

        If the current position is greater than the maximum position,
        will set self.increase to be False. If the current position is less
        than the minimum position, will set self.increase to be True.

        If self.increase is True, it will call self.increase_pos otherwise
        it will call self.decrease_pos
        """
        if self.current_pos > self.max_pos:
            self.increase = False
        if self.current_pos < self.min_pos:
            self.increase = True

        act = self.increase_pos if self.increase else self.decrease_pos
        act()

class MoveServos(Plan):
    '''
    MoveServos plan.
    '''

    def __init__(self, app, servos, *arg,**kw):
        """Create an instance of the MoveServos plan

        Args:
            app: The joy app the plan was created in
            servos: A dictionary of servos

        Returns:
            An instance of the MoveServos plan.
        """
        Plan.__init__(self, app,**kw)
        self.servos = servos

    def servosToStartPosition( self ):
        """
        Sets all servos to their start positions
        """
        for servo_name, servo in self.servos.items():
            servo.set_pos(servo.start_pos)

    def onStart( self ):
        """
        Called when the plan is started. Sets all servos to
        start position.
        """
        self.servosToStartPosition()

    def onStop( self ):
        """
        Called when the plan is stopped. Sets all servos to
        start position.
        """
        self.servosToStartPosition()

    def behavior( self ):
        """
        Will continiously change the servo's position until
        the plan is stopped.

        Yields control back to JoyApp to make sure any other events
        can be handled.
        """
        while True:
            yield
            for servo_name, servo in self.servos.items():
                servo.change_pos()

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


        self.move_forward = MoveServos(self, {
            'thrust': Servo(self.thrust, min_pos=THRUST_UP, max_pos=THRUST_DN, pos_step=180, start_pos=0) #TODO: play around with the pos_step
            #'turn': Servo(self.turn, start_pos=0, run=False) #TODO: need to change strat_pos
        })


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
        self.move_forward.stop()


    def onEvent(self,evt):
        # assertion: must be a KEYDOWN event
        if evt.type != KEYDOWN:
            return


        # MOVING LEFT
        if evt.key == K_LEFT:
            self.stopAllPlans()

            # down
            self.move_to_pos(self.thrust, POS_UP)

            # left
            self.move_to_pos(self.turn, POS_TL)

            # up
            self.move_to_pos(self.thrust, POS_DN)

            # right
            self.move_to_pos(self.turn, POS_CT)


        # MOVING RIGHT
        elif evt.key == K_RIGHT:
            self.stopAllPlans()

            # down
            self.move_to_pos(self.thrust, POS_UP)

            # right
            self.move_to_pos(self.turn, POS_TR)

            # up
            self.move_to_pos(self.thrust, POS_DN)

            # left
            self.move_to_pos(self.turn, POS_CT)


        # THRUST UP
        elif evt.key == K_UP:
            # go forward (up arrow)
            self.stopAllPlans()
            self.move_to_pos(self.thrust, POS_UP)


        # THRUST DOWN
        elif evt.key == K_DOWN:
            # go backward (down arrow)
            self.stopAllPlans()
            self.move_to_pos(self.thrust, POS_DN)


        # MOVE FORWARD
        elif evt.key == K_SPACE:
            # pause/stop (space bar)
            self.stopAllPlans()
            self.move_forward.start()

        
        # RESET ARM POSIION
        elif evt.key == K_RSHIFT:
            # reset orientation
            self.stopAllPlans()
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
