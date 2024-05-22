import copy
import numpy as np
from scipy import signal
from utils import preprocess
import os


def ecg_save_beats(ecg_file, record_name=None):
    if record_name is None:
        record_name = ecg_file.filename[:-4]
    # load ecg file
    try:
        ecg = np.load(ecg_file)
        # ecg = ecg[1010:]
    except:
        return "Error: File format not supported"

    ecg = signal.resample(ecg, int(len(ecg) / 130 * 360))

    # preprocess
    unprocessed_ecg = copy.deepcopy(ecg)
    ecg = preprocess.preprocess(ecg)
    r_peaks = preprocess.pan_tompkins(ecg)

    # slice ecg
    beats = []
    beats, r_peaks = preprocess.windowing(ecg, r_peaks, unprocessed_ecg)
    # beats, r_peaks = preprocess.windowing(unprocessed_ecg, r_peaks)
    beats = [beat.tolist() for beat in beats]
    
    # save beats
    # name = filename
    file_path = "beats/" + str(record_name) + ".npy"
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save the beats data to the specified file
    np.save(file_path, beats)

    # save annotation
    # annotation [0][0] = rpeak, annotation [0][1] = label
    # name = filename_annotation
    annotation = [r_peaks, [-1 for i in range(len(r_peaks))]]
    # print(annotation)
    file_path = "beats/" + str(record_name) + "_annotation.npy"
    np.save(file_path, annotation)

    return beats, annotation
