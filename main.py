#!/usr/bin/env python

'''
FILE RobotDriver.py

This file is used to control a robot with three servos. It is meant for a
configuration with three servos in a straight line. The front servo has a
leg on the left side, the middle servo has a leg on the right side, and the
rear servo has legs on both sides.

To move forward, both the front and middle servos are used in tandem. To back
left, the middle servo is used and to back right the front servo is used.

The rear servo is used to move backwards and is positioned the opposite direction
of the front two servos.
'''
from joy.plans import Plan
from joy import JoyApp
from joy.decl import *
from joy.misc import *
from joy import *
import ckbot

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

        Rebacks:
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

        Rebacks:
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
          0x35: 'front',
          0x08: 'back',
        })

        # servo defs
        self.front = c.at.front
        self.back = c.at.back

        # vibrator
        speed = 350
        delta = 700 #the amount it moves back and forth

        front_center = 0
        left_center = -8500
        right_center = 8500

        # arms
        enabled = True
        arm_down = 1000
        arm_up = -7000
        arm_speed = 150


        # Move the front and middle motors in tandem to move forward
        self.move_forward = MoveServos(self, {
            'back': Servo(self.back, min_pos=front_center - delta, max_pos=front_center + delta, pos_step=speed, start_pos=0),
            'front': Servo(self.front, min_pos=arm_up, max_pos=arm_down, pos_step=arm_speed, start_pos=arm_down, run=enabled)
        })
        self.move_left = MoveServos(self, {
            'back': Servo(self.back, min_pos=left_center - delta, max_pos=left_center + delta, pos_step=speed, start_pos=left_center),
            'front': Servo(self.front, min_pos=arm_up, max_pos=arm_down, pos_step=arm_speed, start_pos=arm_down, run=enabled)
        })
        self.move_right = MoveServos(self, {
            'back': Servo(self.back, min_pos=right_center - delta, max_pos=right_center + delta, pos_step=speed, start_pos=right_center),
            'front': Servo(self.front, min_pos=arm_up, max_pos=arm_down, pos_step=arm_speed, start_pos=arm_down, run=enabled)
        })


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
        self.move_left.stop()
        self.move_right.stop()


    def onEvent(self,evt):
        """
        Responds to keyboard events
            - left arrow: go left
            - right arrow: go right
            - up arrow: go forward
            - space key: pause/stop
        """
        #progress("here")
        if evt.type != KEYDOWN:
            reback

        # assertion: must be a KEYDOWN event
        if evt.key == 276:
            # go left (left arrow)
            self.stopAllPlans()
            self.move_left.start()

        elif evt.key == 275:
            # go right (right arrow)
            self.stopAllPlans()
            self.move_right.start()

        elif evt.key == 273:
            # go forward (up arrow)
            self.stopAllPlans()
            self.move_forward.start()

        elif evt.key == 274:
            # go backward (down arrow)
            self.stopAllPlans()
            # self.move_back.start()

        elif evt.key == 32:
            # pause/stop (space bar)
            self.stopAllPlans()

        # Hide robot position events
        elif evt.type==CKBOTPOSITION:
            reback

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
