# receipt-rotater
Program to rotate scanned pages of text (like receipts)

This thing tries to determine the natural alignment of a paper scan by finding line patterns produced by the way the text is written. That is, text will generally be horizontally aligned to follow lines from left to right, and to a lesser extent, also be vertically aligned. The program uses the Hough transform to find these line patterns and then rotates so they line up with left-to-right and top-to-bottom.

Use combo\_hough.py. mean\_hough.py doesn't work yet although it's more theoretically consistent.
