"""
pip install opencv-contrib-python==3.4.2.16
"""

import json
import pprint
import numpy as np
import cv2 as cv

from classes.yolo import Yolo
from utils.drawing.draw import draw_final_results, draw_rects, ShowPeopleTable
from utils.keyPoints.AlgoritamKeyPoints import create_keypoints_descriptors
from utils.matchers.Matchers import compute_accuracy_table
from utils.preprocessing.preprocess import read_frames_from_video, check_frames_exist, reduce_noise, removeRemovalColor
from utils.tracking.TrackingByYolo import source_detection_by_yolo, tracking_by_yolo
from classes.results_details import ResultsDetails
from utils.cascade.cascade_detect import haarcascades_detect

if __name__ == "__main__":
    """# import images"""
    # init yolo
    yolo = Yolo()
    yolo.initYolo()
    pp = pprint.PrettyPrinter(indent=4)

    with open('./config.txt') as file_json:
        config = json.load(file_json)

        src_input_data = ResultsDetails(config["source"])
        trg_input_data = ResultsDetails(config["target"])

        """ source video """
        source_frames = read_frames_from_video(config["source"])  # a list of all frames extracted from source video
        if not check_frames_exist(source_frames):  # if not len(source_frames) > 0
            print("problem with source video input")
            exit(0)

        if config["source"]["Cascade"]:
            cascade = cv.CascadeClassifier('C:\\opencv\\\sources\\data\\haarcascades\\haarcascade_fullbody.xml')
            for img in source_frames:
                gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                gray = cv.equalizeHist(gray)

                rects = haarcascades_detect(gray, cascade)
                print(len(rects))
                vis = img.copy()
                draw_rects(vis, rects, (0, 255, 0))
                cv.imshow('cascade_detect', vis)

                k = cv.waitKey(5)
                if k == 27:
                    cv.destroyAllWindows()

        # preprocessing reduce noise background
        if config["source"]["reduceNoise"]:
            source_frames = reduce_noise(source_frames)
        if not check_frames_exist(source_frames):
            print("problem with reduce noise source video input")
            exit(0)

        if config["source"]["removeRemovalColor"]:
            source_frames = removeRemovalColor(source_frames)

        source_person = source_detection_by_yolo(source_frames, yolo, is_video=config["source"]["isVideo"], config=config["source"])
        if source_person is None:
            print("fail to detect human on source video")
            exit(0)

        src_input_data.num_of_frames = len(source_person.frames)
        print("src_input_data.num_of_frames: ", src_input_data.num_of_frames)

        create_keypoints_descriptors([source_person])  # gets source descriptors to each frame

        """ target video """
        target_frames = read_frames_from_video(config["target"])
        if not check_frames_exist(target_frames):
            print("problem with target video input")
            exit(0)

        if config["target"]["reduceNoise"]:
            target_frames = reduce_noise(target_frames)
        if not check_frames_exist(target_frames):
            print("problem with target video input - in reduce noise")
            exit(0)

        if config["target"]["removeRemovalColor"]:
            target_frames = removeRemovalColor(target_frames)
        if not check_frames_exist(target_frames):
            print("problem with target video input - in remove color")
            exit(0)

        target_people = tracking_by_yolo(target_frames, yolo, is_video=config["target"]["isVideo"], config=config["target"])
        if not check_frames_exist(target_people):
            print("fail to detect humans on target video")
            exit(0)

        print("number of people: ", len(target_people))
        trg_num_of_frames = 0
        for p in target_people:
            trg_num_of_frames += len(p.frames)
        trg_input_data.num_of_frames = trg_num_of_frames
        print("trg_num_of_frames: ", trg_input_data.num_of_frames)

        create_keypoints_descriptors(target_people)

        """
        acc_target looks like this:
         {
           id_0 : {
           maxAcc : double,
           # target : [arrayOfFrameObject]
           target_frames : FrameObject
           source_frames : FrameObject
           }
         }
        """
        acc_targets = compute_accuracy_table(source_person, target_people)

        ShowPeopleTable(target_people, config["target"])

        draw_final_results(acc_targets, options=config["output"])

