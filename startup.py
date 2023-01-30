# import the necessary packages
import RPi.GPIO as GPIO
from imutils.video import VideoStream
from imutils.video import FPS
from mailjet_rest import client
import face_recognition
from datetime import datetime
import requests
import imutils
import pickle
import time
import cv2
import os

GPIO.setmode(GPIO.BOARD)    # Consider complete raspberry-pi board
GPIO.setwarnings(False)
servoPin  = 12
led_waiting = 11
led_success = 13
led_failure = 15
switch = 16

GPIO.setup(led_waiting, GPIO.OUT)
GPIO.setup(led_success, GPIO.OUT)
GPIO.setup(led_failure, GPIO.OUT)
GPIO.setup(servoPin, GPIO.OUT)
GPIO.setup(switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.output(led_waiting, GPIO.LOW)
GPIO.output(led_success, GPIO.LOW)
GPIO.output(led_failure, GPIO.LOW)

pwm_servo = GPIO.PWM(servoPin, 50)
pwm_servo.start(0)


def facial_rec():
    #Initialize 'currentname' to trigger only when a new person is identified.
    currentname = "unknown"
    #Determine faces from encodings.pickle file model created from train_model.py
    encodingsP = "training/encodings.pickle"

    # load the known faces and embeddings along with OpenCV's Haar
    # cascade for face detection
    print("[INFO] loading encodings + face detector...")
    data = pickle.loads(open(encodingsP, "rb").read())

    # initialize the video stream and allow the camera sensor to warm up
    # Set the ser to the followng
    # src = 0 : for the build in single web cam, could be your laptop webcam
    # src = 2 : I had to set it to 2 inorder to use the USB webcam attached to my laptop
    #vs = VideoStream(src=2,framerate=10).start()
    vs = cv2.VideoCapture(0)
    time.sleep(2.0)

    # start the FPS counter
    fps = FPS().start()
    start_time = time.time()
    # loop over frames from the video file stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to 500px (to speedup processing)
        ret, frame = vs.read()
        frame = imutils.resize(frame, width=500)
        # Detect the fce boxes
        boxes = face_recognition.face_locations(frame)
        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(frame, boxes)
        names = []

        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(data["encodings"],
                encoding)
            name = "unknown" #if face is not recognized, then print Unknown

            cv2.imwrite("snapshot.jpg", frame)
            
            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)

                
                #If someone in your dataset is identified, print their name on the screen
                if currentname != name:
                    currentname = name
                    return currentname
                    #print(currentname)
                    

            # update the list of names
            names.append(name)

        # loop over the recognized faces
        for ((top, right, bottom, left), name) in zip(boxes, names):
            # draw the predicted face name on the image - color is in BGR
            cv2.rectangle(frame, (left, top), (right, bottom),
                (0, 255, 225), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                .8, (0, 255, 255), 2)

        # display the image to our screen
        cv2.imshow("Facial Recognition is Running", frame)
        key = cv2.waitKey(1) & 0xFF

        elapsed_time = time.time() - start_time
        if elapsed_time > 10:
            break
        
        # quit when 'q' key is pressed
        if key == ord("q"):
            break

        # update the FPS counter
        fps.update()

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.release()
    return currentname



def send_email():
    tstamp = datetime.fromtimestamp(os.path.getctime("snapshot.jpg")).strftime('%Y-%m-%d %H:%M:%S')
    return requests.post(
        "https://api.mailgun.net/v3/sandbox79a5f057d83a4c21a7d44d6fecd3e891.mailgun.org/messages",
        auth=("api", "4dc6d4f03aad66df6dac66eabf5398a5-bdb2c8b4-a4cf0826"),
        files=[("attachment", ("snapshot.jpg", open("snapshot.jpg","rb").read()))],
        data={"from": "Excited User <mailgun@sandbox79a5f057d83a4c21a7d44d6fecd3e891.mailgun.org>",
            "to": "pradyutkumar01@gmail.com",
            "subject": "Unrecognized Student Alert!!",
            "text": "A student attempted to enter Lab at: "+ tstamp + " and failed. Find attached the image."})




while True:
    if(GPIO.input(switch) == GPIO.HIGH):                            # When button is not clicked
        continue
    
    # Process Starts
    GPIO.output(led_waiting, GPIO.HIGH)
    person = facial_rec()
    if person == "unknown":
        GPIO.output(led_waiting, GPIO.LOW)
        GPIO.output(led_failure, GPIO.HIGH)
        send_email()
        time.sleep(5.0)
        GPIO.output(led_failure, GPIO.LOW)
    else:
        print(person)
        GPIO.output(led_waiting, GPIO.LOW)
        GPIO.output(led_success, GPIO.HIGH)
        pwm_servo.ChangeDutyCycle(1)
        time.sleep(0.3)
        pwm_servo.ChangeDutyCycle(2)
        time.sleep(0.3)
        pwm_servo.ChangeDutyCycle(3)
        time.sleep(0.3)
        pwm_servo.ChangeDutyCycle(4)
        time.sleep(0.3)
        pwm_servo.ChangeDutyCycle(5)
        time.sleep(0.3)
        pwm_servo.ChangeDutyCycle(6)
        time.sleep(5.0)
        pwm_servo.ChangeDutyCycle(0)
        GPIO.output(led_success, GPIO.LOW)
    continue

