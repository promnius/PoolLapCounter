import cv2
import time
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera

print "Program Running?"

# SETUP:
img_width = 0
img_height = 0 # try to keep the aspect ratio similar to the camera, .5MP is good enough for most detection
BlurAmount = 21 # measured in pixels, so tuning this depends on image size
framerate = 1 # approximate delay in ms, so this is more like 1/framerate, and this simple algorithem
    # doesn't take into account processing time, so actual framerate depends on how fast everything is.
fgbg = cv2.BackgroundSubtractorMOG2(history=35, varThreshold= 70)#35) # initializing forground detection tool
    # history is how many previous pictures are used to generate background. more pictures means more processing time
    # too few and errors will be detected as objects. too many and slow background changes like lighting may not be
    # filtered out. note that what is too many will also depend on framerate.
PersonDetectThreshold = 1000#750 # area measured in pixels that must be extracted as foreground to indicate the presence of
    # someone swimming by. note that this will be dependant on image size, and should be tuned experimentally.
MaxDetectionFrequency = 35 # to prevent counting multiple laps even if the target is seen in multiple photos in short proximity,
    # we simply require the last detection to have occured some amount of time ago. this is measured in frames, so time in seconds
    # is maxdetectionfrequency * framerate / 1000, assuming processing time is minimal. a good target is 5-10 seconds, since even for 
    # short laps nobody can swim a lap faster than this (which would cause you to miss a lap), but also even slow swimmers should fully
    # clear the field of view in this length of time.

#cam = cv2.VideoCapture(0)
camera = PiCamera()
camera.resolution = ([320, 240])
camera.framerate = 6
#camera.brightness = 70
#camera.contrast = 50
#camera.awb_mode = 'off'
#camera.exposure_mode = 'off'

frame_motion_counter = 0

rawCapture = PiRGBArray(camera)

time.sleep(3)

# setup visual windows
txt_frameBlurred = "Frame Blurred"
cv2.namedWindow(txt_frameBlurred)
cv2.moveWindow(txt_frameBlurred, 160, 0)
txt_foregroundRaw = "Foreground Raw"
cv2.namedWindow(txt_foregroundRaw)
cv2.moveWindow(txt_foregroundRaw, 480, 0)
txt_foregroundBinary = "Foreground binary"
cv2.namedWindow(txt_foregroundBinary)
cv2.moveWindow(txt_foregroundBinary, 160, 240)
txt_foregroundContours = "Contours"
cv2.namedWindow(txt_foregroundContours)
cv2.moveWindow(txt_foregroundContours, 480, 240)

#cv2.startWindowThread()

detection_counter = 0
lap_counter = 0

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    rawCapture.truncate(0)
    img_frame = f.array
    #print img_frame
    #ret, img_frame = cam.read() # grab a frame from the camera
    #cv2.imshow("Frame", img_frame) # INTERMEDIATE DISPLAY
    #if not ret: # double check that we could actually access the camera
    #    break
    # img_small = # resize the image for faster processing speed
    img_blurred = cv2.GaussianBlur(img_frame,(BlurAmount,BlurAmount),0) # blur the entire picture so that the background detector doesn't pick
        # up on small variations
    cv2.imshow(txt_frameBlurred, img_blurred) # INTERMEDIATE DISPLAY
    img_foreground = fgbg.apply(img_blurred, None, .01) # use the MOG2 algorithem to extract a dynamic forground
    cv2.imshow(txt_foregroundRaw, img_foreground) # INTERMEDIATE DISPLAY
    img_foreground_blurred = cv2.GaussianBlur(img_foreground,(BlurAmount,BlurAmount),0) # blur the forground, so that wandering background pixels disperse
    ret, img_foreground_binary = cv2.threshold(img_foreground_blurred,25,255,cv2.THRESH_BINARY) # turn the forground into black and white to eliminate the 
        # dispersed pixels

    cv2.imshow(txt_foregroundBinary, img_foreground_binary) # INTERMEDIATE DISPLAY
        
    #img_foreground_binary = cv2.bitwise_not(img_foreground_binary)
    #cv2.imshow("Foreground Inverted", img_foreground_binary) # INTERMEDIATE DISPLAY
    contours, hierarchy = cv2.findContours(img_foreground_binary,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE) # extract outlines as shapes so we
        # can figure out exactly how much of the image is moving. note that counting number of white pixels will give the same result, but by using
        # contours we could do additional filtering by eliminating contours that are smaller than some threshold.
    img_foreground_binary_wColor = cv2.cvtColor(img_foreground_binary, cv2.COLOR_GRAY2BGR) # convert image to RGB, mainly for display so we 
        # can draw contours of a different color on the image.
    cv2.drawContours(img_foreground_binary_wColor, contours, -1, (0,255,0), 3) #, -1, (0,255,0), 3)# UPDATE IMAGE FOR INTERMEDIATE DISPLAY
    #print (contours)
    cv2.imshow(txt_foregroundContours, img_foreground_binary_wColor) # INTERMEDIATE DISPLAY



    total_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        total_area = total_area + area
    #print total_area

    if total_area > PersonDetectThreshold:
        if detection_counter > MaxDetectionFrequency:
            frame_motion_counter = frame_motion_counter + 1
            if frame_motion_counter > 3:
                lap_counter = lap_counter + 1
                print (("Laps Swam: ") + str(lap_counter))
                detection_counter = 0
    else:
        frame_motion_counter = 0
    # print lap_counter

    k = cv2.waitKey(framerate) & 0xFF


    detection_counter = detection_counter + 1
    rawCapture.truncate(0)


    # USER INTERACTION:
    # print k

    if k == ord("q"):
        time.sleep(1)
        #cv2.destroyWindow(txt_frameBlurred)
        #cv2.destroyWindow(txt_foregroundRaw)
        #cv2.destroyWindow(txt_foregroundBinary)
        #cv2.destroyWindow(txt_foregroundContours)
        #cv2.destroyAllWindows()
        # VERY neccessary, since destroyallwindows is sort of broken in linux
        #k2 = cv2.waitKey(framerate) & 0xFF
        #k2 = cv2.waitKey(framerate) & 0xFF
        #k2 = cv2.waitKey(framerate) & 0xFF
        #k2 = cv2.waitKey(framerate) & 0xFF
        #k2 = cv2.waitKey(500) & 0xFF
        break
    """
    if k%256 == 27:
        # ESC pressed
        print("Escape hit, closing...")
        cv2.destroyAllWindows()
        break
    elif k%256 == 114: # r pressed
        print("Resetting lap count")
        lap_counter = 0
    """
    """ elif k%256 == 32:
        # SPACE pressed
        img_name = "opencv_frame_{}.png".format(img_counter)
        cv2.imwrite(img_name, frame)
        print("{} written!".format(img_name))
        img_counter += 1 """

                        
#cam.release()
cv2.destroyAllWindows()

