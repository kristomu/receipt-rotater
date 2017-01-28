# receipt-rotater
Program to rotate scanned pages of text (like receipts)

This thing tries to determine the natural alignment of a paper scan by finding line patterns produced by the way the text is written. That is, text will generally be horizontally aligned to follow lines from left to right, and to a lesser extent, also be vertically aligned. The program uses the Hough transform to find these line patterns and then rotates so they line up with left-to-right and top-to-bottom.

Use median\_hough.py. combo\_hough.py is an older version. Usage is just "python median\_hough.py imagefile.png". The rotated image is returned as rotated\_image.png.
