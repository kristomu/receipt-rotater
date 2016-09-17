# Detect alignment of a receipt by looking for lines. The model is that we
# have considerable horizontal and vertical alignment, so there will be
# a cluster of angles around some angle, and then another cluster nearly 90
# degrees off.

# Example receipt "receipt.png" was taken from Wikipedia:
# https://upload.wikimedia.org/wikipedia/commons/0/0b/ReceiptSwiss.jpg
# tilted 5.67 degrees.

# Our idea is to do this:
#	1. Find prospective lines with a Hough transform
#	2. Of the angles of those lines, find two modes that are sufficiently 
#		far apart (modeling the horizontal and vertical lines)
#	3. Cluster the remaining lines' angles according to which mode they're
#		close to.
#	4. Take the mean of the median angles of the two clusters.
#	4. Return this as the rotation angle, and rotate.

import cmath, math, sys
import numpy as np
from collections import Counter
from operator import itemgetter, attrgetter

from skimage import feature, io, color, transform

##############################################

# Angular distances and circular statistics

def normalize_angle(x):
	while x < -np.pi:
		x += 2 * np.pi
	while x >= np.pi:
		x -= 2 * np.pi

	return x

def short_angle_dist(a, b):
	x = normalize_angle(a - b)
	
	return abs(x)	# we don't need the direction

def threshold(x, centerpoint, distance, verbose=False):
	if short_angle_dist(x[0], centerpoint) > distance:
		return x[1]
	return 0

def val_if_at_distance(centerpoint, distance):
	return lambda x: threshold(x, centerpoint, distance)

# angle_magnitude_list is a list of (angle, magnitude) tuples.
# The angle gives the angle of the point group, and the magnitude is how many
# points we should consider there to be there.
def get_weighted_angular_mean(angle_magnitude_list):
	point_total = 0

	for theta, rho in angle_magnitude_list:
		point_total += rho * np.exp(1j * theta)

	return cmath.phase(point_total)

# TODO? later: Weber problem -- or is that overkill?
# For now: gets the median angle (i.e. where we've passed half the magnitude)
def get_median(angle_magnitude_list):
	total_weight = sum([x[1] for x in angle_magnitude_list])
	current_weight = 0

	for angle, magnitude in angle_magnitude_list:
		if current_weight + magnitude > total_weight/2.0:
			return angle
		current_weight += magnitude

	return 1/0 	# shouldn't happen

##############################################

def get_estimated_degrees(estimated_radians):
	estimated_degrees = estimated_radians * 180 / np.pi	

	# If it's greater than 45', then it's probably the vertical angle.
	# Subtract it from 90'.

	if estimated_degrees > 45:
		estimated_degrees = estimated_degrees - 90
	if estimated_degrees < -45:
		estimated_degrees = 90 + estimated_degrees

	return estimated_degrees

###################################################################

# TODO: Organize better

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

# Get the (weighted) angle estimates for any lines running through the
# picture, using the Hough transform.

hspace, angles, distances = transform.hough_line(edges, 
	np.arange(-np.pi/2, np.pi/2, np.pi/720))
hspace, angles, distances = transform.hough_line_peaks(hspace, angles, 
	distances, num_peaks=100)

# Give each angle a weight depending on its intensity in Hough space.
angle_counts = Counter()
total_magnitudes = 0

for hough_point_idx in xrange(len(angles)):
	magnitude, angle = hspace[hough_point_idx], angles[hough_point_idx]
	angle_counts[angle] += magnitude
	total_magnitudes += magnitude

# Quick and dirty: First find the mode. Then find the mode that's more
# than 45 degrees (pi/8) away. Use these angles for centers and assign each
# angle to the cluster given by the closest mode. Determine the mean angle 
# within each cluster, and those are the angles.

angular_mode = max(angle_counts.iteritems(), key=itemgetter(1))
print angular_mode
distant_ang_mode = max(angle_counts.iteritems(), 
	key=val_if_at_distance(angular_mode[0], np.pi/8))
print distant_ang_mode

# Now assign each counter item to the point it's closest to.
# Tiebreak in favor of the second point (but doesn't matter in practice).

cluster = [[], []]

for angle, magnitude in angle_counts.iteritems():
	if short_angle_dist(angle, angular_mode[0]) < \
		short_angle_dist(angle, distant_ang_mode[0]):

		cluster[0].append((angle, magnitude))
	else:
		cluster[1].append((angle, magnitude))

cluster[0] = sorted(cluster[0])
cluster[1] = sorted(cluster[1])

# If there's only one cluster, make the second a duplicate of the first.

if len(cluster[1]) == 0:
	cluster[1] = cluster[0]

# Calculate the cluster medians and mean of medians, and rotate.

cluster_medians = [get_median(x) for x in cluster]
estimated_degrees = [get_estimated_degrees(x) for x in cluster_medians]

print "First cluster says: rotate by %.2f"% -estimated_degrees[0]
print "Second cluster says: rotate by %.2f"% -estimated_degrees[1]

gm = sum(estimated_degrees)/float(len(estimated_degrees))

print "Mean of medians: %.2f" % -gm

rotated_image = transform.rotate(img, gm, cval=1) # white background
io.imsave('rotated_image.png', rotated_image)