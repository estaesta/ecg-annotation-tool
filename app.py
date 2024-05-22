from flask import Flask, render_template, request, make_response
from utils import utils
import numpy as np
import os
from math import ceil

# from flask_wtf import CSRFProtect
import db

# csrf = CSRFProtect()
app = Flask(__name__)
# csrf.init_app(app)
db.init_app(app)


@app.route("/", methods=["GET"])
def index():
    record_list = []
    return render_template("index.html", record_list=record_list)


@app.route("/record", methods=["POST"])
def upload():
    # save file to /records
    # save name and path to database
    ecg_file = request.files["file"]
    # if empty, use filename
    record_name = request.form.get("record_name") or ecg_file.filename[:-4]

    # check if already exists
    for file in os.listdir("beats"):
        if file.endswith(".npy") and "_annotation" not in file:
            if record_name == file[:-4]:
                return render_template("errors/alert.html", message="Record name already exists")


    # turn ecg into beats (incliding the resampling)
    beats, annotation = utils.ecg_save_beats(ecg_file, record_name)

    beats = beats[:20]
    r_peaks = annotation[0][:20]

    page = 1
    end = page * 20
    start = end - 20
    total_pages = ceil(len(beats) / 20)

    # index for the title of the beat
    for i in range(len(beats)):
        beats[i] = (i, beats[i])

    print("Beats:", type(beats[0][1]))

    r = make_response(render_template("beats-template.html", beats=beats, r_peaks=r_peaks, page=page, total_pages=total_pages, record_name=record_name))
    # HX-Trigger Response Headers
    r.headers["HX-Trigger"] = "refreshRecordList"
    return r

    # return render_template("beats-template.html", beats=beats, r_peaks=r_peaks)


@app.route("/record/<record_name>", methods=["GET"])
def record(record_name):
    # user input record_name and the page
    # record_name = request.args.get("record_name")
    page = request.args.get("page")
    print("page:", page)
    # check if page is number
    if page is None:
        page = 1

    try:
        beats_r = np.load("beats/" + str(record_name) + ".npy", mmap_mode="r")
        annotation = np.load("beats/" + str(record_name) + "_annotation.npy", mmap_mode="r")
    except:
        return render_template("errors/404.html")

    # per page show 20 beats
    try:
        page = int(page)
    except:
        page = 1
    end = page * 20
    start = end - 20
    beats = beats_r[start:end].tolist().copy()

    #include the index for the title of the beat
    # for i in range(len(beats)):
    #     # beats[i] = beats[i].tolist()
    #     beats[i] = (i, beats[i])
    # adjust the index with the page number
    for i in range(len(beats)):
        beats[i] = (i + start, beats[i])

    r_peaks = annotation[0][start:end]
    annotation = annotation[1][start:end]
    annotation_copy = []
    for i in range(len(annotation)):
        if annotation[i] == 0:
            annotation_copy.append("N")
        elif annotation[i] == 1:
            annotation_copy.append("S")
        elif annotation[i] == 2:
            annotation_copy.append("V")
        elif annotation[i] == 3:
            annotation_copy.append("F")
        elif annotation[i] == 4:
            annotation_copy.append("Q")
        else:
            annotation_copy.append("Clear")
    print("Annotation:", annotation)

    total_pages = ceil(len(beats_r) / 20)
    print("len(beats_r):", len(beats_r))
    print("Total pages:", total_pages)

    return render_template("beats-template.html", beats=beats, r_peaks=r_peaks, page=page, total_pages=total_pages, record_name=record_name, annotation=annotation_copy)

@app.route("/record/<path:record_name>", methods=["DELETE"])
def deleteRecord(record_name):
    # record_name = request.args.get("record_name")
    print("Record name:", record_name)
    try:
        os.remove("beats/" + str(record_name) + ".npy")
        os.remove("beats/" + str(record_name) + "_annotation.npy")
    except:
        return render_template("errors/alert.html", message="Record not found")
    return recordList()

@app.route("/recordlist", methods=["GET"])
def recordList():

    # read all the files in the beats folder
    record_list = []
    # for file in os.listdir("beats"):
    #     if file.endswith(".npy") and "_annotation" not in file:
    #         record_list.append(file[:-4])
    # walk through the child directories too
    # make it display like /name/record1.npy
    for root, dirs, files in os.walk("beats"):
        for file in files:
            if file.endswith(".npy") and "_annotation" not in file:
                record_list.append(os.path.join(root, file)[6:-4])

    print(record_list)
    return render_template("recordList.html", record_list=record_list)


@app.route("/annotate/<path:record_name>", methods=["POST"])
def annotate(record_name):
    label = request.form.get("label")
    index = request.form.get("index")
    print("Label:", label)
    print("Record name:", record_name)
    print("Index:", index)

    # map the label into int
    if label == "N":
        int_label = 0
    elif label == "S":
        int_label = 1
    elif label == "V":
        int_label = 2
    elif label == "F":
        int_label = 3
    elif label == "Q":
        int_label = 4
    else:
        int_label = -1

    try:
        annotation = np.load("beats/" + str(record_name) + "_annotation.npy", mmap_mode="r+")
        annotation[1][int(index)] = int_label
        # np.save("beats/" + str(record_name) + "_annotation.npy", annotation)
    except:
        return render_template("errors/500.html")

    return render_template("label-button.html", record_name=record_name, annotation=label, index=index)


@app.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


if __name__ == "__main__":
    app.run(port=5000)
