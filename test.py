#!/usr/bin/python

import motors

wheels = motors.Wheels()
wheels.safe_drive(500, 500, 200)
wheels.safe_drive(300, -300, 50)
wheels.safe_drive(-300, 300, 100)
wheels.safe_drive(-500, -500, 200)
