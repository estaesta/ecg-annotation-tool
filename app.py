from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    record_list = []
    # dummy data
    # format: 10s-name.npy
    record_list.append("10s-abc.npy")
    record_list.append("10s-def.npy")
    record_list.append("10s-ghi.npy")
    return render_template("index.html", record_list=record_list)

# @app.route("/upload", methods=["POST"])
# def upload():
#     return render_template("upload.html")

@app.route("/select", methods=["POST"])
def select():
    return render_template("beats-template.html")

# @app.route("/recordAnnotation", methods=["POST"])
# def recordAnnotation():
#     record_name = request.form["record_name"]
#     return 

if __name__ == "__main__":
    app.run(port=5000)
