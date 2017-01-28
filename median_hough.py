# Known bugs: TEST5 gets cut off. FIXED
# Seems to be generally less robust. FIXED

import cmath, math, sys, warnings
import numpy as np
from collections import Counter

from skimage import feature, io, color, transform

def get_median(angle_magnitude_list):
	total_weight = sum([x[1] for x in angle_magnitude_list])
	current_weight = 0

	for angle, magnitude in angle_magnitude_list:
		if current_weight + magnitude > total_weight/2.0:
			return angle
		current_weight += magnitude

	return 1/0 	# shouldn't happen

def guess_rotation(cannied_picture, bound_array):
	# Get the (weighted) angle estimates for any lines running through the
	# picture, using the Hough transform.

	hspace, angles, distances = transform.hough_line(cannied_picture, 
		bound_array)
	hspace, angles, distances = transform.hough_line_peaks(hspace, angles, 
		distances, num_peaks=10, threshold=0.15 * np.max(hspace))

	# Give each angle a weight depending on its intensity in Hough space.
	angle_counts = Counter()

	for hough_point_idx in xrange(len(angles)):
		# The angles are from -90 to 90. Since we expect the modes to be 90
		# degrees apart (corresponding to the horizontal and vertical lines
		# of the image), fold the negative angles over to the positive ones.
		degree_angle = np.rad2deg(angles[hough_point_idx])
		if (degree_angle < 0):
			degree_angle = 90 + degree_angle

		# Round off to prevent floating point problems.
		degree_angle = round(65536.0 * degree_angle)/65536.0

		magnitude, angle = hspace[hough_point_idx], degree_angle
		angle_counts[angle] += magnitude

	cluster = [(angle, magnitude) for angle, magnitude in 
					angle_counts.iteritems()]

	cluster = sorted(cluster)
	return (sum([x[1] for x in cluster]), get_median(cluster))

##############################################

img = io.imread(sys.argv[1])
# RGB or grayscale
try:
	width, height, channels = img.shape
	gray = color.rgb2grey(img)
except ValueError:
	width, height = img.shape
	gray = img

print height, width
edges = feature.canny(gray)
print "Canny done"

# The denominators should have a common factor
initial_precision = np.pi/180.0
secondary_precision = np.pi/5040.0

initial_guess = guess_rotation(edges, 
		np.arange(-np.pi/2, np.pi/2, initial_precision))[1]

print "Initial guess %g" % initial_guess

neg_initial_guess = initial_guess - 90
# Can be improved: just do an n degree range around every peak we found,
# then eliminate duplicate
#Positive quadrant
guess_range_pos = np.arange(np.deg2rad(initial_guess) - 3*initial_precision, 
	np.deg2rad(initial_guess) + 3*initial_precision, secondary_precision)
#Negative quadrant
guess_range_neg = np.arange(np.deg2rad(neg_initial_guess) - 3*initial_precision, 
	np.deg2rad(neg_initial_guess) + 3*initial_precision, secondary_precision)

final_angle = guess_rotation(edges,
	np.concatenate([guess_range_pos, guess_range_neg]))[1]

# If the angle is small, negate it
# If it's large, subtract 90 and negate it.

out_rotation = -final_angle
if abs(90-final_angle) < abs(final_angle):
	out_rotation = 90-final_angle

print "Suggested rotation: %g" % out_rotation

# Use a white background for the empty spots left after rotation
rotated_image = transform.rotate(img, -out_rotation, cval=1, resize=True) 
with warnings.catch_warnings():
	warnings.simplefilter("ignore")
	io.imsave('rotated_image.png', rotated_image)