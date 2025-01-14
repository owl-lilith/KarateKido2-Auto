# Karate Kido Game 


## Overview
The Karate Kido Game Solver is a Python-based project utilizing OpenCV, NumPy, and computer vision techniques to analyze and automate gameplay for the "Karate Kido" game. This solver identifies critical game elements, such as logs, branches, numbers, power-ups, and player positions, to make real-time decisions and perform automated actions.

<p align="center">
  <img src="https://raw.githubusercontent.com/owl-lilith/KarateKido2-Auto/refs/heads/main/game_window.png" alt="System Overview" width="350">
</p>


## Features
- **Detect the game window:**
1.	Take a screen shot from the device using mss
2.	Convert the screen shot to gray scale
3.	Using SIFT to match a given template with the screen shot
4.	Filter the matches to get the best one
5.	Conclude: game window top left, game window bottom right

- **Preprocess image to detect the tree log and branches:**
1.	HSV to detect the colors shade segmentation and lighting for the log and branches
2.	Canny for edges
3.	Hough Lines Probability to detect continues lines
4.	Detect the vertical lines for log coordinates using Sobel
5.	Detect the horizontal lines for branches coordinates using Sobel

- **Detect Log:**
1.	From the vertical lines of the processed image 
2.	Measure the longest lines that close to the middle
3.	Assume it is the log boundaries
4.	Conclude: log center coordinate, log top left coordinate, log bottom right coordinate

- **Detect Branches:**
1.	From the horizontal lines of the processed image 
2.	Detect all the lines that happened to be above the log bottom right coordinate
3.	Filter the concluded lines from the previous step by keep the closest branches according to a given threshold  
4.	Sort the concluded lines from the most bottom (closest to the player) to the most top (far away from the player)
5.	Conclude: branches list, each element represent [x left coordinate,  y left coordinate, x right coordinate, y right coordinate]

- **Detect the character (player):**
1.	Template Matching algorithm
2.	Blob Detection Simple algorithm

- **Detect Glass:**
1.	Crop the given frame to focus on the log surrounded area 
2.	HSL FULL conversion to detect the glass structure gradients and brightness
3.	Using farther Morphologies conversions (dilation, erosion) to detect the glass
4.	Detect the longest blob 
5.	Conclude: glass center coordinate, glass top left coordinate, glass bottom right coordinate

- **Detect Numbers:**
1.	Crop the given frame to focus on the log area 
2.	YCrCb space color conversion to detect the number-tone-based density
3.	Histogram calculation and Normalization to compare the given numbers template (2, 3, 4) and the given preprocessed frame
4.	Assume the number value according to the score result from the histogram comparison (determine the value if its template comparing get the highest score)
5.	Conclude: number value, number center coordinate, number top left coordinate, number bottom right coordinate

- **Detect Power ups:**
1.	Lab space color conversion to detect the calibration power up brightness and color differences 
2.	Using farther Morphologies conversions (dilation, erosion)
3.	Hough Circles algorithm to detect the power up
4.	Conclude: power up center, power up top left, power up bottom right


## Output
<p align="center">
  <img src="https://raw.githubusercontent.com/owl-lilith/KarateKido2-Auto/refs/heads/main/debug/result_screening.png" alt="System Overview" width="350">
</p>

- output on consol
``` python
start
frame30: hit 2
frame37: hit glass
frame55: hit 3
frame67: hit glass
frame74: hit 3
catch power up
frame92: hit 4
catch power up
catch power up
frame116: hit 2
frame122: hit glass
frame128: hit 2
catch power up
frame148: hit 2
frame150: hit glass
frame171: hit 2
catch power up
frame182: hit 2
frame188: hit glass
frame210: hit glass
frame211: hit 2
catch power up
frame239: hit 4
frame245: hit glass
catch power up
frame266: hit 4
frame284: hit 4
frame302: hit 3
catch power up
frame317: hit 2
frame329: hit 2
frame345: hit 4
frame358: hit 2
catch power up
frame378: hit 2
frame397: hit 3
catch power up
frame406: hit glass
frame419: hit 3
frame426: hit glass
```

 
 
