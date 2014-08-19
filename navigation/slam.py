# My implementation of a SLAM algorithm, based on this:
#<http://ocw.mit.edu/courses/aeronautics-and-astronautics/
#16-412j-cognitive-robotics-spring-2005/projects/1aslam_blas_repo.pdf>

from __future__ import division

import math
import sys

import numpy as np

from programs import log

import blobs
import filters
import motors
import robot_status
import sensors
import utilities


# A class representing a single landmark.
class Landmark:
  # How many times we have to see it before it's deemed usable.
  usable_threshold = 1
  current_id = 0
  # The validation gate threshold.
  lamda = 100

  def __init__(self):
    # How many times we've seen it.
    self.sightings = 1
    # Where (relative to the robot's position then) we last saw it.
    self.last_location = None

    # The landmark's unique numerical ID.
    self.id = Landmark.current_id
    Landmark.current_id += 1

    # The range and bearing between the robot and the landmark, as calculated
    # from the odometry.
    self.h = None

    # The innovation covariance calculated by the EKF for this landmark.
    self.S = None

  # Covert an (x, y) location to a range and bearing.
  def __range_and_bearing(self, point):
    x = point[0]
    y = point[1]

    landmark_range = (x ** 2 + y ** 2) ** (1 / 2)
    landmark_bearing = math.pi / 2 - math.atan(y / x)

    return np.vstack((landmark_range, landmark_bearing))

  # The range and bearing between the robot and the landmark, as seen by the
  # lidar.
  @property
  def z(self):
    return self.__range_and_bearing(self.last_location)

  # If this landmark is suitable for SLAM.
  def usable(self):
    return self.sightings >= Landmark.usable_threshold

  # Takes an the location of an observed landmark,
  # and returns whether it passes or fails the validation gate.
  def validation_gate(self, location):
    #TODO (danielp): I'm not sure if I'm doing this right.
    #z = self.__range_and_bearing(location)

    #v = z - self.h
    #value = np.dot(np.dot(np.reshape(v, (1, -1)), np.linalg.inv(self.S)), v)
    #log.debug("Validation gate value for landmark %d: %s." % (self.id, value))

    if utilities.distance(location, self.last_location) <= Landmark.lamda:
      return True
    return False


# A database for storing landmarks.
class LandmarkDatabase:
  def __init__(self):
    self.landmarks = []
    self.new_landmarks = []
    # This is there to insure that no new landmark gets checked against
    # landmarks that were found in the same cycle as it was.
    self.new_this_cycle = []

  # Takes a landmark, and increments an existing one if it's seen it or adds it
  # as a new one if it hasn't.
  def check_landmark(self, location):
    # Check distance between this and all the known landmarks.
    best_landmark = None
    best_distance = sys.maxint
    for landmark in self.landmarks + self.new_landmarks:
      # Find the landmark that it's closest to.
      distance = utilities.distance(landmark.last_location, location)
      if distance < best_distance:
        best_distance = distance
        best_landmark = landmark

    if (best_landmark and best_landmark.validation_gate(location)):
      log.debug("Landmark at %s corresponds to landmark at %s." % \
          (location, best_landmark.last_location))

      best_landmark.sightings += 1
      best_landmark.last_location = location

    else:
      log.debug("Found a new landmark at %s." % (str(location)))

      landmark = Landmark()
      landmark.last_location = location
      self.new_this_cycle.append(landmark)

  # Returns a list of all the landmarks that are usable.
  def get_usable_landmarks(self):
    return self.landmarks

  # Returns a list of landmarks that are being used for the first time.
  def get_new_landmarks(self):
    self.new_landmarks.extend(self.new_this_cycle)
    self.new_this_cycle = []

    ret = []
    for landmark in self.new_landmarks:
      if landmark.usable():
        log.debug("Using new landmark %d." % (landmark.id))
        ret.append(landmark)

        # Bounce it to the other list.
        self.landmarks.append(landmark)

    # Remove landmarks that are no longer new.
    for landmark in ret:
      self.new_landmarks.remove(landmark)

    return ret


# Represents a single Extended Kalman Filter implementation.
class Kalman:
  # How many mm's per 100 the wheel encoders are generally off by.
  encoder_drift = 1
  # How many mm's per 100 the LDS range readings are generally off by.
  range_error = 0.1
  # How many radians the LDS bearing readings are generally off by.
  bearing_error = 0.02

  def __init__(self, initial_x, initial_y, initial_theta):
    self.landmark_db = LandmarkDatabase()

    # System state.
    self.X = np.vstack((
        initial_x,
        initial_y,
        initial_theta
    ))
    # Covariance matrix.
    # We only have one observation of the robot position, so we can't really do
    # anything meaningful here.
    self.P = np.zeros((3, 3))
    # Prediction Jacobian.
    self.A = self.__prediction_jacobian(0, 0)
    # Innovation covariance. (Gets set later.)
    self.S = None

  # Find the measurement model of a landmark.
  def __measurement_model(self, landmark):
    l_x = landmark.last_location[0]
    l_y = landmark.last_location[1]
    x = self.X[0]
    y = self.X[1]
    theta = self.X[2]

    distance = ((l_x - x) ** 2 + (l_y - y) ** 2) ** (1 / 2)
    bearing = theta - math.atan((l_y - y) / (l_x - x))
    log.debug("Landmark %d: Range %f, Bearing %f." % \
        (landmark.id, distance, bearing))

    return np.vstack((distance, bearing))

  # Find the Jacobian of the measurement model for a particular landmark.
  def __measurement_jacobian(self, landmark):
    l_x = landmark.last_location[0]
    l_y = landmark.last_location[1]
    distance = landmark.h[0]
    x = self.X[0]
    y = self.X[1]

    range_x = (x - l_x) / distance
    range_y = (y - l_y) / distance
    bearing_x = (l_y - y) / distance ** 2
    bearing_y = (l_x - x) / distance ** 2

    jacobian = np.array([
        [range_x, range_y, 0],
        [bearing_x, bearing_y, -1],
    ])

    return jacobian

  # Find the prediction model.
  def __prediction_model(self, dx, dy, dtheta, q):
    x = self.X[0]
    y = self.X[1]
    theta = self.X[2]

    x_pos = x + dx + dx * q
    y_pos = y + dy + dy * q
    bearing = theta + dtheta + dtheta * q

    prediction = np.vstack((x_pos, y_pos, bearing))

    return prediction

  # Find the jacobian of the prediction model.
  def __prediction_jacobian(self, dx, dy):
    jacobian = np.array([
        [1, 0, -dy],
        [0, 1, dx],
        [0, 0, 1]
    ])

    return jacobian

  # Find SLAM-specific Jacobians.
  def __slam_jacobians(self, prediction_jacobian, dx, dy, dtheta):
    J_xr = np.delete(prediction_jacobian, 2, 0)

    theta = self.X[2]

    row_1_col_1 = math.cos(theta + dtheta)
    row_2_col_1 = math.sin(theta + dtheta)
    row_1_col_2 = -dy * math.cos(dtheta) - dx * math.sin(dtheta)
    row_2_col_2 = dx * math.cos(dtheta) - dy * math.sin(dtheta)

    J_z = np.array([
        [row_1_col_1, row_1_col_2],
        [row_2_col_1, row_2_col_2]
    ])

    return (J_xr, J_z)

  # Find the process noise.
  def __process_noise(self, dx, dy, dtheta):
    W = np.vstack((dx, dy, dtheta))
    # TODO (danielp): I'm kind of BSing the calculation for C.
    percentage = Kalman.encoder_drift * 0.01
    C = np.random.normal(percentage, percentage ** 2, 1)
    Q = np.dot(W * C, W.reshape(1, -1))

    return Q

  # Find measurement noise.
  def __measurement_noise(self, landmark_range):
    percentage = Kalman.range_error * 0.01
    c = np.random.normal(percentage, percentage ** 2, 1)
    percentage = Kalman.bearing_error * 0.01
    bd = np.random.normal(percentage, percentage ** 2, 1)

    R = np.array([
      [landmark_range * c, 0],
      [0, bd]
    ])

    return R

  # Run the prediction step, updating current state with odometry data.
  def predict(self, dx, dy, dtheta):
    log.debug("Running SLAM prediction step...")
    prediction = self.__prediction_model(dx, dy, dtheta, 0)

    # Update the state.
    self.X[:3] = prediction
    log.debug("New state: %s." % (self.X))

    # Update the prediction jacobian.
    self.A = self.__prediction_jacobian(dx, dy)
    log.debug("New prediction jacobian: %s." % (self.A))

    # Compute the process noise.
    Q = self.__process_noise(dx, dy, dtheta)
    log.debug("Process noise: %s." % (Q))

    # Update covariance for robot position.
    self.P[0:3, 0:3] = np.dot(np.dot(self.A, self.P[0:3, 0:3]), self.A) + Q

    # Update feature cross-correlations.
    column = 3
    while column < self.P.shape[1]:
      self.P[0:3, column:(column + 2)] = \
          np.dot(self.A, self.P[0:3, column:(column + 2)])

      column += 2

    log.debug("New covariance matrix: %s." % (self.P))

  # Run step 2, updating state from observed landmarks.
  def landmark_update(self):
    log.debug("Running SLAM landmark update step...")

    # Get all the landmarks from the database that are ready to be used.
    landmarks = self.landmark_db.get_usable_landmarks()

    # Update landmark range and bearing.
    for i in range(0, len(landmarks)):
      landmark = landmarks[i]

      # Use the measurement model.
      landmark.h = self.__measurement_model(landmark)
      # Compute measurement noise.
      R = self.__measurement_noise(landmark.z[0])
      log.debug("Measurement noise: %s." % (R))

      # Create the H matrix.
      H = np.zeros((2, len(landmarks) * 2 + 3))
      # Fill in the first part of the H matrix.
      jacobian = self.__measurement_jacobian(landmark)
      H[0:2, 0:3] = jacobian
      # Set the landmark-specific part.
      H[0:2, (i + 3):(i + 5)] = jacobian[0:2, 0:2] * -1
      log.debug("H matrix for landmark %d: %s." % (landmark.id, H))

      # Now we can compute the innovation covariance.
      V = np.identity(2)
      landmark.S = np.dot(np.dot(H, self.P), H.T) + np.dot(np.dot(V, R), V.T)
      log.debug("Innovation covariance for landmark %d: %s." %
          (landmark.id, landmark.S))

      K = np.dot(np.dot(self.P, H.T), np.linalg.inv(landmark.S))
      log.debug("Kalman gain for landmark %d: %s." % (landmark.id, K))

      # Compute a new state vector from the Kalman gain.
      innovation = landmark.z - landmark.h
      log.debug("Innovation for landmark %d: %s." % (landmark.id, innovation))
      self.X = self.X + np.dot(K, innovation)
      log.debug("Corrected state vector: %s." % (self.X))

  # Run step 3, incorporating new landmarks into the system state.
  def incorporate_new(self, dx, dy, dtheta):
    log.debug("Running SLAM new landmark incorporation step...")

    landmarks = self.landmark_db.get_new_landmarks()

    next_index = self.X.shape[0]
    next_row = self.P.shape[0]
    next_column = self.P.shape[1]
    log.debug("Index of next landmark in X: %d." % (next_index))
    log.debug("Next row, column in P: %d, %d." % (next_row, next_column))

    # Calculate SLAM-specific jacobians.
    J_xr, J_z = self.__slam_jacobians(self.A, dx, dy, dtheta)
    log.debug("J_xr: %s\n, J_z: %s." % (J_xr, J_z))

    # Extend the state vector to contain all the new landmarks.
    rows_needed = len(landmarks) * 2
    padding = np.zeros((rows_needed, 1))
    self.X = np.vstack((self.X, padding))
    # Extend the covariance vector to contain all the new landmarks.
    column_padding = np.zeros((self.P.shape[0], rows_needed))
    self.P = np.hstack((self.P, column_padding))
    row_padding = np.zeros((rows_needed, self.P.shape[1]))
    self.P = np.vstack((self.P, row_padding))

    for landmark in landmarks:
      # Add it to the state vector.
      self.X[next_index] = landmark.last_location[0]
      self.X[next_index + 1] = landmark.last_location[1]
      next_index += 2

      # Add it to the covariance matrix.
      R = self.__measurement_noise(landmark.z[0])
      # NOTE: The MIT paper has a mistake on this one, they use the whole P
      # matrix instead of just the submatrix. Not only is this mathematically
      # impossible, if you go and look at the sources you will see that it is
      # actually just supposed to be the upper left 3x3 submatrix.
      covariance = np.dot(np.dot(J_xr, self.P[0:3, 0:3]), J_xr.T) + \
          np.dot(np.dot(J_z, R), J_z.T)
      log.debug("Covariance of landmark %d: %s." % (landmark.id, covariance))
      self.P[next_row:(next_row + 2),
          next_column:(next_column + 2)] = covariance

      # Covariance between robot and landmark.
      robot_landmark_cov = np.dot(self.P[0:3, 0:3], J_xr.T)
      log.debug("Covariance between robot and landmark %d: %s." %
          (landmark.id, robot_landmark_cov))
      # NOTE: Again, the MIT paper is incorrect here. In the section defining
      # the covariance matrix, the definitions for submatrices "D" and "E"
      # should be switched.
      self.P[0:3, next_column:(next_column + 2)] = robot_landmark_cov
      # Covariance between landmark and robot.
      self.P[next_row:(next_row + 2), 0:3] = robot_landmark_cov.T
      # TODO (danielp): There is an issue somewhere again, because in both
      # papers that I looked at, the math doesn't work out. I'll therefore have
      # to try both ways that it could be.
      # Covariance between landmark and each other landmark.
      row = next_row
      column = 3
      diag_row = 3
      diag_column = next_column
      while column < next_column:
        # In the bottom two rows.
        landmark_landmark = np.dot(J_xr, self.P[0:3, column:(column + 2)])
        self.P[row:(row + 2), column:(column + 2)] = landmark_landmark

        # The diagonal one.
        self.P[diag_row:(diag_row + 2), diag_column:(diag_column + 2)] = \
          landmark_landmark.T

        column += 2
        diag_row += 2

      next_row += 2
      next_column += 2

    log.debug("New covariance matrix: %s." % (self.P))

  # Run a single iteration of the Kalman filter. Returns the robot's new
  # position and bearing.
  def run_iteration(self, landmark_points, dx, dy, dtheta):
    # Add each landmark to the database.
    for point in landmark_points:
      self.landmark_db.check_landmark(point)

    self.predict(dx, dy, dtheta)
    self.landmark_update()
    self.incorporate_new(dx, dy, dtheta)

    # If we don't copy it, other things end up modifying the original array,
    # which REALLY confuses the Kalman filter.
    x_cop = np.copy(self.X)
    return (x_cop[0], x_cop[1], x_cop[2])

# Monitors and controls the SLAM algorithm.
class Slam:
  def __init__(self):
    self.lds = sensors.LDS()
    self.wheels = motors.Wheels()

    # Start with a displacement of zero, and assume we are aligned with a wall.
    self.x_pos = 0
    self.y_pos = 0
    # We start at 90 because it makes the math make more since, i.e. x_pos
    # is sideways and y_pos is up and down.
    self.bearing = math.pi / 2
    # Temporary wheel positions to save at the start of driving operations.
    self.driving_l_wheel = 0
    self.driving_r_wheel = 0

    self.kalman = Kalman(self.x_pos, self.y_pos, self.bearing)

  # Returns all the landmarks in a series of points.
  def __find_landmarks(self, points):
    all_blobs = blobs.find_blobs(points)
    walls = filters.find_walls(all_blobs)
    # We could use spikes here, but that is unreliable in environments with people
    # in them.

    # Extract landmark points from wall landmarks.
    landmark_points = []
    for wall in walls:
      point = utilities.landmark_point((0, 0), wall[0], wall[1])
      landmark_points.append(point)

    return landmark_points

  # Gets laser data and uses kalman filter to improve odometry guesses.
  def __enhance_with_lidar(self, dx, dy, dtheta):
    scan = self.lds.get_scan(stale_time = 0)
    scan = filters.remove_outliers(scan)
    points = utilities.to_rectangular(scan)

    landmarks = self.__find_landmarks(points)
    log.debug("Found landmarks at: %s." % (landmarks))

    # Run the kalman filter.
    self.x_pos, self.y_pos, self.bearing = \
        self.kalman.run_iteration(landmarks, dx, dy, dtheta)

    log.debug("Corrected position: (%f, %f)." % (self.x_pos, self.y_pos))
    log.debug("Corrected bearing: %f." % (self.bearing))

  # Gets run every time the robot starts driving.
  def started_driving(self):
    self.driving_l_wheel, self.driving_r_wheel = self.wheels.get_distance()
    log.debug("Wheel position at start of driving: L: %d, R: %d" % \
      (self.driving_l_wheel, self.driving_r_wheel))

  # Gets run every time the robot stops driving.
  def stopped_driving(self):
    old_bearing = self.bearing

    # Figure out how far we drove.
    l_wheel, r_wheel = self.wheels.get_distance()
    distance_l = l_wheel - self.driving_l_wheel
    distance_r = r_wheel - self.driving_r_wheel
    log.debug("Left distance: %d, Right distance: %d." % (distance_l, distance_r))

    circumference = robot_status.ROBOT_WIDTH * math.pi

    dtheta = 0
    if distance_l * distance_r < 0:
      # One wheel went forward and one went backward.
      left_over = abs(distance_l) - abs(distance_r)
      # Have the code below handle any extra distance.
      if left_over > 0:
        # Compute the change in bearing, using the wheel that traveled the shorter
        # distance.
        dtheta = distance_r / circumference * 2 * math.pi
        # Get the sign right. (A negative right distance means we went
        # clockwise, which decreases our bearing, etc.)
        dtheta = abs(dtheta) * (distance_r / abs(distance_r))

        distance_l = distance_l + distance_r
        distance_r = 0

      elif left_over < 0:
        dtheta = distance_l / circumference * 2 * math.pi
        dtheta = abs(dtheta) * (distance_r / abs(distance_r))

        distance_r = distance_r + distance_l
        distance_l = 0

      else:
        # It doesn't really matter which one we pick in this case.
        dtheta = distance_l / circumference * 2 * math.pi
        dtheta = abs(dtheta) * (distance_r / abs(distance_r))

        distance_r = 0
        distance_l = 0

    # Calculate change in position and bearing. (Both wheels always move at
    # the same speed.)
    difference = distance_r - distance_l
    # Now our circumference is doubled, because we're only rotating with one
    # wheel.
    circumference *= 2
    turn_angle = difference / circumference * 2 * math.pi
    dtheta += turn_angle

    # Since we're not rotating around the center of the robot, the x and y
    # positions also get changed.
    r = robot_status.ROBOT_WIDTH
    dx = r * math.cos(turn_angle) - r
    dy = r * math.sin(turn_angle)
    if turn_angle:
      # Cos remains positive regardless of the angle, so we need to negate it if
      # we're going in the other direction.
      dx *= turn_angle / abs(turn_angle)

    # Calculate change in position from driving straight.
    straight_component = min(abs(distance_r), abs(distance_l))
    # Get the sign right.
    if straight_component:
      if straight_component == abs(distance_r):
        straight_component *= distance_r / straight_component
      else:
        straight_component *= distance_l / straight_component

    dx += straight_component * math.cos(old_bearing)
    dy += straight_component * math.sin(old_bearing)

    self.x_pos += dx
    self.y_pos += dy
    self.bearing += dtheta

    # Normalize bearing.
    if self.bearing:
      self.bearing = self.bearing % \
          (2 * math.pi * (self.bearing / abs(self.bearing)))
    if self.bearing < 0:
      self.bearing = 2 * math.pi - abs(self.bearing)

    log.debug("New position: (%f, %f)." % (self.x_pos, self.y_pos))
    log.debug("New bearing: %f." % (math.degrees(self.bearing)))

    # Now that the robot has moved, use laser data and the Kalman filter to
    # improve our odometry data.
    self.__enhance_with_lidar(dx, dy, dtheta)

  # Returns SLAM's best guess as to our displacement.
  def get_displacement(self):
    return (self.x_pos, self.y_pos, math.degrees(self.bearing))

  # Resets the position.
  def reset_position(self):
    self.x_pos = 0
    self.y_pos = 0

  # Resets the bearing.
  def reset_bearing(self):
    self.bearing = 0
