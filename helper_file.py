# libraries
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import math
import win32com.client, time
from queue import Queue
import pyautogui
import mss 

main_image = cv.imread("screen-shots/10.png")
template = cv.imread("characters/baby.png")
baby_x = (template.shape[0] * 100) / main_image.shape[0]
baby_y = (template.shape[1] * 100) / main_image.shape[1]

# templates
templates = {
    'baby':cv.imread("characters/baby.png"),
    'looser':cv.imread("characters/looser.png"),
    'handsome':cv.imread("characters/handsome.png"),
    'godfather': cv.imread("characters/godfather.png"),
}

number_templates = {
    2: 'number/2.png',
    3: 'number/3.png',
    4: 'number/4.png',
}

# edge
def image_edges(image):
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    
    # Edge detection
    edges = cv.Canny(image, 50, 150)
    return edges

# vertical_lines, horizontal_lines
def preprocess_log(image):
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    brown_threshold = cv.inRange(hsv, (9, 94, 0), (14, 213, 255))
    gray_threshold = cv.inRange(hsv, (113, 0, 125), (171, 69, 186))
    dark_blue_threshold = cv.inRange(hsv, (112, 68, 119), (113, 70, 144))
    # dark_blue_threshold = cv.inRange(hsv, (113, 68, 119), (113, 70, 144))
    result = brown_threshold + gray_threshold + dark_blue_threshold


    edges = image_edges(result)
         
    lines = cv.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=40, minLineLength=40, maxLineGap=20)
    
    vertical_lines = []
    horizontal_lines = []
    
    for line in lines:
        l = line[0]
        if l[0] == l[2]:
            vertical_lines.append(l)
        if abs(l[1] -l[3]) <= 3:
            horizontal_lines.append(l)   
    
    
    return vertical_lines, horizontal_lines

# center, top_left, bottom_right
def log_coordinate(image, lines):
    
    # length
    lengths = []
    for line in lines:
        l = line
        x1 = l[0]
        y1 = l[1]
        x2 = l[2]
        y2 = l[3]
        length = ((x2 - x1)**2 +(y2 - y1)**2)**0.5
        lengths.append(length)
    index_max = max(range(len(lengths)), key=lengths.__getitem__)
    
    l = lines[index_max]
    top = (l[2], l[3])
    bottom = (l[0], l[1])
    
    # width
    top_left = (0,0)
    bottom_right = (0,0)
    center = (int(image.shape[1] / 2), int(image.shape[0] / 2))
    
    half_width = center[0] - top[0]

    if half_width > 0:
        top_left = top
        bottom_right = (bottom[0]+ half_width * 2, bottom[1] )
    else:
        top_left = (top[0] + half_width * 2, top[1] )
        bottom_right = bottom
        
    return center, top_left, bottom_right

# branches   
def branches_coordinates(middle, top, bottom, horizontal_lines):
    right = bottom[0]
    left = top[0]
    horizontal_lines_updated = []
    for i in range(0, len(horizontal_lines)):
        l = horizontal_lines[i]
        x1 = l[0]
        y1 = l[1]
        x2 = l[2]
        y2 = l[3]
        if x1 < left - 25 or x2 > right + 25:
            if y1 < bottom[1] - 100:
                m1 = abs(middle[0] - x1)
                m2 = abs(middle[0] - x2)
                minimum = min(m1, m2)
                if minimum < 80:
                    horizontal_lines_updated.append([x1, y1, x2, y2])
    
    sorted_array = sorted(horizontal_lines_updated, key=lambda x: x[1])
    
    return sorted_array

# center, top_left, bottom_right
def match_characters(image):
    dsize_x = baby_x * image.shape[0] / 100
    dsize_y = baby_y * image.shape[1] / 100
    dsize = (int(dsize_y), int(dsize_x))
    
    template_resize = cv.resize(template, dsize, fx=0, fy=0, interpolation=cv.INTER_LINEAR)
    
    h, w, _ = template_resize.shape
    res = cv.matchTemplate(image, template_resize, cv.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    top_left = min_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    center = (int(top_left[0] + w / 2),int(top_left[1] + h / 2))

    return center, top_left, bottom_right

# player_center, player_top_left, player_bottom_right
def get_player(image, log_center, log_bottom_right):
    player_center = center = (0,0)
    player_top_left = (0,0)
    player_bottom_right = (0,0)
    
    for template in templates.values():
        center, top_left, bottom_right = match_characters(image, template)
        x1, y1 = center
        x2 = log_center[0]
        y2 = log_bottom_right[1]

        distance  = ((x2 - x1)**2 +(y2 - y1)**2)**0.5
        if distance < 80:
            cv.circle(image, center, 2, (255, 0, 0), 5)
            player_center = center
            player_top_left = top_left
            player_bottom_right = bottom_right
            
    return  player_center, player_top_left, player_bottom_right

# window_top_left, window_bottom_right
def detect_game_window(template, full_screenshot):
    template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
    full_screenshot_gray = cv.cvtColor(full_screenshot, cv.COLOR_BGR2GRAY)

    window_top_left = None
    window_bottom_right = None

    sift = cv.SIFT_create()

    keypoints1, descriptors1 = sift.detectAndCompute(template_gray, None)
    keypoints2, descriptors2 = sift.detectAndCompute(full_screenshot_gray, None)

    bf = cv.BFMatcher(cv.NORM_L2)
    matches = bf.knnMatch(descriptors1, descriptors2, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    if good_matches:

        src_points = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_points = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        M, mask = cv.findHomography(src_points, dst_points, cv.RANSAC, 5.0)

        if M is not None:
            h, w = template_gray.shape
            corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
            transformed_corners = cv.perspectiveTransform(corners, M)

            # Extract coordinates
            window_top_left = tuple(np.int32(transformed_corners[0][0]))
            window_bottom_right = tuple(np.int32(transformed_corners[2][0]))

        else:
            print("Homography could not be computed.")
    else:
        print("No good matches found.")

    return window_top_left, window_bottom_right

# glass_center, glass_top_left, glass_bottom_right
def glass_filter(log_bottom_right, image):
    log_top_left = (int(image.shape[1] // 2) - 60, 0)
    log_bottom_right = (int(image.shape[1] // 2) + 60, log_bottom_right[1])

    top = log_top_left[1] 
    left = log_top_left[0] 
    width = log_bottom_right[0] - log_top_left[0]
    height = log_bottom_right[1] - log_top_left[1]  
    
    image = image[top : top + height, left : left + width]

    image = cv.cvtColor(image, cv.COLOR_BGR2HLS_FULL)
    image = cv.inRange(image, (94, 0, 0), (180, 208, 129))
    
    rows = image.shape[0] // 30

    verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, rows))
    vertical = cv.erode(image, verticalStructure)
    
    coordinates = np.argwhere(vertical == 255)
    
    if len(coordinates) < 4:
        return (0,0), (0,0), (0,0)
    
    top_left = coordinates.min(axis=0)
    bottom_right = coordinates.max(axis=0)
    
    glass_top_left = (left + top_left[1], top_left[0])
    glass_bottom_right = (left + bottom_right[1], bottom_right[0])
    glass_center = (int(glass_top_left[0] + (glass_bottom_right[0] - glass_top_left[0]) / 2),int(glass_top_left[1] + (glass_bottom_right[1] - glass_top_left[1]) / 2))
    
    if (glass_bottom_right[1] - glass_top_left[1]) > 100 or (glass_bottom_right[1] - glass_top_left[1]) < 40:
        return (0,0), (0,0), (0,0)
    
    return glass_center, glass_top_left, glass_bottom_right

# cut, number_center, number_top_left, number_bottom_right
def number_filter(image):
    log_top_left = (int(image.shape[1] // 2) - 40, 0)
    log_bottom_right = (int(image.shape[1] // 2) + 40, image.shape[0])

    top = log_top_left[1] 
    left = log_top_left[0]
    width = log_bottom_right[0] - log_top_left[0] 
    height = log_bottom_right[1] - log_top_left[1]

    cut = image[top : (top + height), left : left + width]
    
    image = cv.cvtColor(cut, cv.COLOR_BGR2YCrCb)
    image = cv.inRange(image, (180, 134, 52), (255, 159, 93))
    
    coordinates = np.argwhere(image == 255)
    
    if len(coordinates) < 4:
        return np.array([1]), (0, 0), (0, 0), (0, 0)
    
    top_left = coordinates.min(axis=0)
    bottom_right = coordinates.max(axis=0)
    
    # image = image[top_left[1] : top_left[1] + bottom_right[1] - top_left[1], top_left[0] : top_left[0] + bottom_right[0] - top_left[0] ]
    
    number_top_left = (left + top_left[1], top_left[0])
    number_bottom_right = (left + bottom_right[1], bottom_right[0])
    number_center = (int(number_top_left[0] + (number_bottom_right[0] - number_top_left[0]) / 2),int(number_top_left[1] + (number_bottom_right[1] - number_top_left[1]) / 2))
    
    if (number_bottom_right[1] - number_top_left[1]) > 50:
        return image, (0,0), (0,0), (0,0)
    
    return cut, number_center, number_top_left, number_bottom_right


def calculate_histogram(image, hsv_range, bins):
    image_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    hist = cv.calcHist([image_hsv], [0, 1], None, bins, hsv_range)
    cv.normalize(hist, hist, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
    return hist


def compare_numbers(image, templates, hsv_range, bins):
    hist_image = calculate_histogram(image, hsv_range, bins)
    scores = {}
    for number, template_path in templates.items():
        template = cv.imread(template_path)
        hist_template = calculate_histogram(template, hsv_range, bins)
        score = cv.compareHist(hist_image, hist_template, cv.HISTCMP_CORREL)
        scores[number] = score
    
    detected_number = max(scores, key=scores.get)
    return detected_number, scores

# number_value, number_center, number_top_left, number_bottom_right
def determine_number(image):
    cut, number_center, number_top_left, number_bottom_right = number_filter(image)
    
    if len(cut.shape) < 2:
        return 1, (0, 0), (0, 0), (0, 0)
    
    hsv_range = [24, 28, 0, 255]
    bins = (7, 7)  
    
    number_value, scores = compare_numbers(cut, number_templates, hsv_range, bins)
    return number_value, number_center, number_top_left, number_bottom_right

# power_ups_center
def power_ups_filter(image):
    copy = cv.cvtColor(image, cv.COLOR_BGR2YCrCb)
    green = cv.inRange(copy, (58, 55, 74), (163, 116, 116))
    blue = cv.inRange(copy, (58, 57, 145), (164, 116, 181))
    
    result = green + blue
    circles = cv.HoughCircles(result, cv.HOUGH_GRADIENT, dp=1.2, minDist=30, param1=50, param2=30, minRadius=10, maxRadius=50)
    center = None
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            center = (x, y)
            cv.circle(image, (x, y), r, (255, 255, 255), 4)

    return center

# player_placement, branches_positions, power_up_placement
def decision_making(player_center, log_center, branches, power_up_center):
    # player
    player_log_middle_distance = player_center[0] - log_center[0]
    if player_log_middle_distance > 0:
        player_placement = 'right'
    else:
        player_placement = 'left'
    
    # branches
    branches_positions = []
    for branch in branches:
        x1 = branch[0]
        y1 = branch[1]
        x2 = branch[2]
        distance1 = abs(x1 - log_center[0])
        distance2 = abs(x2 - log_center[0])
        if distance1 > distance2:
            distance = x1 - log_center[0]
            if distance > 0:
                branches_positions.append({'coordinate': y1, 'position': 'right'})
            else:
                branches_positions.append({'coordinate': y1, 'position': 'left'})
        else:
            distance = x2 - log_center[0]
            if distance > 0:
                branches_positions.append({'coordinate': y1, 'position': 'right'})
            else:
                branches_positions.append({'coordinate': y1, 'position': 'left'})
            

    #  power_ups
    power_up_distance = power_up_center[0] - log_center[0]
    if power_up_distance > 0:
        power_up_placement = 'right'
    else:
        power_up_placement = 'left'

    return player_placement, branches_positions, power_up_placement

def movement(player_center, player_placement, power_up_center, power_up_placement, branches_positions, glass_center, number_value, number_center, right_button_x, right_button_y, left_button_x, left_button_y):
    # make decision
    branch = branches_positions[len(branches_positions) - 1]
    if player_placement == 'right' and branch['position'] == player_placement and abs(player_center[1] - branch['coordinate']) < 120:
        player_placement = 'left'
    elif player_placement == 'left' and branch['position'] == player_placement and abs(player_center[1] - branch['coordinate']) < 120:
        player_placement = 'right'
    
    if player_placement == 'right' and power_up_placement != player_placement and abs(player_center[1] - power_up_center[1]) < 100:
        print('catch power up')
        player_placement = 'left'        
    elif player_placement == 'left' and power_up_placement != player_placement and abs(player_center[1] - power_up_center[1]) < 100:
        print('catch power up')
        player_placement = 'right'
    
    move_x = None
    move_y = None
    if player_placement == 'right':
        move_x = right_button_x
        move_y = right_button_y
    else:
        move_x = left_button_x
        move_y = left_button_y
    
    
    if abs(glass_center[1] - player_center[1]) < 40:
            print('hit glass')
            pyautogui.click(x=move_x, y=move_y)
    
    if abs(number_center[1] - player_center[1]) < 40:
        print(f'hit {number_value}')
        # for i in range(1, number_value):
        #     pyautogui.click(x=move_x, y=move_y)                
        pyautogui.click(x=move_x, y=move_y)                
    
    
    pyautogui.click(x=move_x, y=move_y)
        
    return

# frame 
def draw(frame, player_center, log_top_left, log_bottom_right, power_up_center, glass_top_left, glass_bottom_right, number_top_left, number_bottom_right, branches):
    cv.circle(frame, power_up_center, 3, (255, 255, 255), 2)
    cv.rectangle(frame, glass_top_left, glass_bottom_right, (255, 255, 255), 2)
    cv.rectangle(frame, number_top_left, number_bottom_right, (255, 255, 255), 2)
    for branch in branches: 
        x1 = branch[0]
        y1 = branch[1]
        x2 = branch[2]
        y2 = branch[3]

        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 10)      
    cv.rectangle(frame, log_top_left, log_bottom_right, (255, 0, 0), 2) 
    # cv.rectangle(frame, player_top_left, player_bottom_right, (0, 255, 0), 2)
    cv.circle(frame, player_center, 2, (0, 255, 0), 3)
    
    return frame







