from flask import Flask, render_template, request
import random

app = Flask(__name__)

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]

TIMINGS = [
    "8:30-9:20","9:20-10:10","10:10-11:00",
    "BREAK",
    "11:15-12:05","12:05-12:55",
    "LUNCH",
    "1:25-2:15","2:15-3:05",
    "3:20-4:10","4:10-5:00","5:00-5:50"
]

# 🎨 UNIQUE COLOR GENERATOR
def generate_unique_colors(n):
    colors = []
    for i in range(n):
        hue = int(360 * i / n)
        colors.append(f"hsl({hue}, 70%, 80%)")
    return colors

def generate(subjects, slot):
    timetable = {day: ["EMPTY"] * len(TIMINGS) for day in DAYS}

    subject_hours = {s['name']: int(s['hours']) for s in subjects}

    # 🎨 Assign unique colors
    color_list = generate_unique_colors(len(subjects))
    subject_colors = {s['name']: color_list[i] for i, s in enumerate(subjects)}

    theory = [s for s in subjects if "lab" not in s['name'].lower()]
    labs = [s for s in subjects if "lab" in s['name'].lower()]

    # only 3 continuous days
    continuous_days = random.sample(DAYS, 3)

    for day in DAYS:
        used_today = set()
        lab_done = False

        # ---------- LAB ----------
        if slot == "Slot 1":
            lab_slots = [7, 8]   # afternoon
        else:
            lab_slots = [4, 5]   # morning

        for lab in labs:
            if subject_hours[lab['name']] >= 2 and not lab_done:
                timetable[day][lab_slots[0]] = {
                    "type": "LAB",
                    "name": lab['code'],
                    "color": subject_colors[lab['name']]
                }
                timetable[day][lab_slots[1]] = "SKIP"
                subject_hours[lab['name']] -= 2
                lab_done = True
                break

        # ---------- THEORY ----------
        if slot == "Slot 1":
            valid_slots = [0,1,2,4,5]
        else:
            valid_slots = [7,8,9,10,11]

        for i in valid_slots:
            if timetable[day][i] != "EMPTY":
                continue

            # allow gaps for 2 days
            if day not in continuous_days and random.random() < 0.5:
                continue

            random.shuffle(theory)
            for sub in theory:
                if subject_hours[sub['name']] > 0 and sub['name'] not in used_today:
                    timetable[day][i] = {
                        "type": "SUB",
                        "name": sub['code'],
                        "color": subject_colors[sub['name']]
                    }
                    subject_hours[sub['name']] -= 1
                    used_today.add(sub['name'])
                    break

        # ---------- MIN 3 ----------
        filled = sum(1 for x in timetable[day] if isinstance(x, dict))
        if filled < 3:
            for i in valid_slots:
                if timetable[day][i] == "EMPTY":
                    for sub in theory:
                        if subject_hours[sub['name']] > 0:
                            timetable[day][i] = {
                                "type": "SUB",
                                "name": sub['code'],
                                "color": subject_colors[sub['name']]
                            }
                            subject_hours[sub['name']] -= 1
                            filled += 1
                            break
                if filled >= 3:
                    break

        # ---------- BREAK/LUNCH ----------
        for i, t in enumerate(TIMINGS):
            if t == "BREAK":
                timetable[day][i] = {"type": "BREAK"}
            elif t == "LUNCH":
                timetable[day][i] = {"type": "LUNCH"}

    return timetable, subject_colors


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        dept = request.form["dept"]
        year = request.form["year"]
        slot = request.form["slot"]

        names = request.form.getlist("name")
        codes = request.form.getlist("code")
        faculty = request.form.getlist("faculty")
        hours = request.form.getlist("hours")

        subjects = []
        for i in range(len(names)):
            subjects.append({
                "name": names[i],
                "code": codes[i],
                "faculty": faculty[i],
                "hours": hours[i]
            })

        timetable, subject_colors = generate(subjects, slot)

        return render_template("index.html",
                               timetable=timetable,
                               subjects=subjects,
                               dept=dept,
                               year=year,
                               slot=slot,
                               timings=TIMINGS,
                               colors=subject_colors)

    return render_template("index.html", timetable=None)


if __name__ == "__main__":
    app.run(debug=True)