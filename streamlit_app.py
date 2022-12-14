import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoHTMLAttributes
import av
import cv2
import numpy as np
import threading
import imutils
import time 
from collections import deque

lock = threading.Lock()

airball_container = {'airball': False, 'airball_reseted': True,'state':False}


st.title("My first Streamlit app")
st.write("Hello, world")



pts = deque(maxlen=16)


low_hue = st.slider('Lower HUE',0,255,2)
low_sat = st.slider('Lower Saturation',0,255,178)
low_val = st.slider('Lower Value',0,255,183)
high_hue = st.slider('Upper HUE',0,255,30)
high_sat = st.slider('Upper Saturation',0,255,255)
high_val = st.slider('Upper Value',0,255,253)

mask_activated = st.checkbox('Mask on')
airball_detection_activated = st.checkbox('Airball detection on')


color_lower = (low_hue, low_sat, low_val)
color_upper = (high_hue, high_sat, high_val)
start = st.slider(
    'Height Right',
    0, 480,240)



end = st.slider('Height Left',0,480,240)

# threshold1 = st.slider("Threshold1", min_value=0, max_value=1000, step=1, value=200)
# threshold2 = st.slider("Threshold2", min_value=0, max_value=1000, step=1, value=200)
st.write('Values:', start)


def callback(frame):
    t = time.time()

    img = frame.to_ndarray(format="bgr24")

    blurred = cv2.GaussianBlur(img, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, color_lower, color_upper)

    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    if mask_activated:
        img = cv2.bitwise_and(img,img,mask = mask)

    # find contours in the mask and initialize the current
	# (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    center = None

    under_table =np.array([[0,480],[0,start],[640, end],[640,480]],np.int32)
    cv2.polylines(img,[under_table],True,(0, 0, 255), 8)

	# only proceed if at least one contour was found
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and

        # centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        # only proceed if the radius meets a minimum size
        if radius > 10:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(img, (int(x), int(y)), int(radius),
                (0, 255, 255), 2)
            cv2.circle(img, center, 5, (0, 0, 255), -1)
        result = cv2.pointPolygonTest(under_table, center, False) 
        if result >0:
                # with lock:
            if airball_container['state'] == False:
                print('AIRBALL DETECTED!')
                airball_container['airball'] = True
    pts.appendleft(center)

    thickness = 16

    for i in range(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
        if pts[i - 1] is None or pts[i] is None:
            continue
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
        thickness = int(np.sqrt(16 / float(i + 1)) * 2.5)
        cv2.line(img, pts[i - 1], pts[i], (0, 0, 255), thickness)

    # detected airball bellow the line



    # with lock:
    #     if airball_container['state'] == False:
    #         time.sleep(3)
    #         print('10 sec passes  statement')

    #         airball_container['airball'] = True
    print(time.time()-t)
    return av.VideoFrame.from_ndarray(img,format="bgr24")










ctx = webrtc_streamer(key="example", video_frame_callback=callback,
                      rtc_configuration={  # Add this config
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
# media_stream_constraints={
#     "video": {
#         "width": {"min": 1024, "ideal": 1024, "max": 1024 },
#         "height":{"min": 768, "ideal": 768, "max": 768 }
#     }},
        video_html_attrs=VideoHTMLAttributes(
    autoPlay=True, controls=True, style={"width": "100%"}, muted=True
),)



airball_error = st.empty()
reset_button = st.empty()

if airball_detection_activated:
    while ctx.state.playing:
        time.sleep(0.5)
        if airball_container['airball'] and airball_container['state'] == False:
            with lock:
                airball_container['state'] = True
            break
        


with lock:
    if airball_container['airball'] and airball_container['state'] == False:
        airball_container['state'] = True
        print('lock?33')
    if airball_container['state']:
        if airball_container['airball']:
            airball_error.error('Airball Detected', icon="🚨")
        
        def reset_airball():
            airball_error.empty()
            airball_container['airball'] = False
            airball_container['state'] = False
            reset_button.empty()

            
        reset_button.button('Shot taken?', on_click= reset_airball, key=None, help=None, args=None, kwargs=None,  type="secondary", disabled=False)
