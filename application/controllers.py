from flask import Flask, request,redirect, url_for,session,flash
from flask import jsonify
import json
from flask import render_template
from flask import current_app as app
from application.models import User,Subjects,Chapters,Questions,Options,QuizDetails,Scores,QuizResponse,File
from flask import request
from .database import db
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy
from datetime import datetime, date, timedelta
from flask_mail import Message
from main import app,mail
import os
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET","POST"])
def first():
    return render_template("index.html")
@app.route("/user_register", methods=["GET","POST"])
def register():
    return render_template("user_register.html")
@app.route("/register/login",methods=["GET","POST"])
def login1():
    username = request.form.get("username")
    fullname = request.form.get("fullname")
    dob = request.form.get("dob")
    qualification = request.form.get("qualification")
    password = request.form.get("password")
    if not username or not password or not fullname or not dob or not qualification:
        return render_template("user_register.html", warningg="All fields are required.")
    existing_user = db.session.query(User).filter_by(username=username).first()
    if existing_user:
        return render_template("index.html", warningg="Account already exists.")
    else:
        new_user = User(username=username, fullname=fullname,dob=dob,qualification=qualification,password=password)
        db.session.add(new_user)  
        db.session.commit()
        return render_template("index.html")
@app.route("/admin",methods=["GET","POST"])
def admin():
    ausername=request.form.get("ausername")
    apassword=request.form.get("apassword")
    if not ausername or not apassword:
        return render_template("index.html", warningg="All fields are required.")
    query = text("SELECT password FROM admin WHERE username = :ausername")
    result = db.session.execute(query, {"ausername": ausername}).fetchone()
    if result:
        stored_password = result[0]
        if apassword==stored_password:
           return redirect(f"/adminhome")
        else:
            return render_template("index.html",warningg="Incorrect password.")
@app.route("/login",methods=["GET","POST"])
def login():
    username=request.form.get("username")
    password=request.form.get("password")
    if not username or not password:
        return render_template("index.html", warningg="All fields are required.")
    query = text("SELECT password FROM user WHERE username = :username")
    result = db.session.execute(query, {"username": username}).fetchone()
    if result:
        stored_password = result[0]
        if password==stored_password:
           session['username'] = username
           session['password'] = password
           query2 = text("SELECT fullname FROM user WHERE username = :username")
           fullname = db.session.execute(query2, {"username": username}).fetchone()
           return redirect(f"/user/{fullname[0]}")
        else:
            return render_template("index.html",warningg="Incorrect password.")
    return render_template("user_register.html", warningg="Username not found.")
@app.route("/profile", methods=["GET","POST"])
def profile():
    return render_template("profile.html")
@app.route("/personal_details",methods=["GET","POST"])
def personal_details():
    username = session.get('username')
    password=session.get('password')
    if not username:
        return redirect("/login")
    query = text("""
    SELECT uid, fullname, dob, qualification
    FROM user
    WHERE username = :username
    """)
    result = db.session.execute(query, {"username": username}).fetchone()
    if result:
        uid, fullname, dob, qualification = result
    else :
        return render_template("home.html")
    result2=db.session.execute(text("select file_url from File where uid=:uid"),{"uid":uid})
    img_url=result2.fetchone()
    url=img_url
    print(url)
    if not url:
        url=("/static/user.png",)

        
    return render_template("personal_details.html",id=uid,name=fullname,dob=dob,img_url=url[0],username=username,qualification=qualification,password=password)
@app.route("/upload/<int:uid>",methods=["GET","POST"])
def upload(uid):
    old_file = db.session.execute(text("SELECT file_url FROM File WHERE uid=:uid"), {"uid": uid}).fetchone()
    
    if old_file and old_file[0]:
        old_filepath = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(old_file[0]))
        if os.path.exists(old_filepath):
            os.remove(old_filepath)
    db.session.execute(text("delete from File where uid=:uid"),{"uid":uid})
    db.session.commit()
    file=request.files["image"]
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        file_url = f"/static/upload/{file.filename}"
        new_file = File(uid=uid,file_url=file_url) 
        db.session.add(new_file)
        db.session.commit()
    return redirect(f"/personal_details")

@app.route("/academic_details",methods=["GET","POST"])
def academic_details():
    username=session.get('username')
    userid=db.session.execute(text("select uid from user where username= :username"),{"username":username})
    uid=userid.scalar()
    result=db.session.execute(text("select distinct(quizid) from quizresponse where uid=:userid"),{"userid":uid})
    quizid=result.fetchall()
    quizids=[]
    for id in quizid:
        quizids.append(id[0])
    result2=db.session.execute(text("select subject_name from subjects"))
    subject=result2.fetchall()
    subjectnames=[]
    for subjectname in subject:
        subjectnames.append(subjectname[0])
    subjectcount=[]
    result3=db.session.execute(text("select * from quiz_details q join chapters c on c.chaoter_id=q.chapter_id join subjects s on s.subject_id=c.subject_id"))
    column_names=result3.keys()
    details=[dict(zip(column_names,rows)) for rows in result3.fetchall()]
    for subjectname in subjectnames:
        counter=0
        for quizid1 in quizids:
            for detail in details:
                if detail['quizid']==quizid1 and detail['subject_name']== subjectname:
                    counter=counter+1
        subjectcount.append({"subject_name":subjectname , "count": counter})
    subjectmarks=[]
    for subjectname in subjectnames:
        result5=db.session.execute(text("select sum(score) from scores where quiz_id in (select quizid from quiz_details where chapter_id in (select chaoter_id from chapters where subject_id in (select subject_id from subjects where subject_name=:subject))) and uid=:uid"),{"subject":subjectname,"uid":uid})
        subjectsum=result5.scalar() or 0
        subject_entry = next((item for item in subjectcount if item["subject_name"] == subjectname), None)
        if subject_entry:
            subjectavg = subjectsum/subject_entry["count"] if subject_entry["count"] > 0 else 0
        else:
            subjectavg = 0
        subjectmarks.append({"subject_name":subjectname,"avg":round(subjectavg,2)})
    
    result4=db.session.execute(text("select * from scores s join quiz_details q on q.quizid=s.quiz_id join chapters c on c.chaoter_id=q.chapter_id where s.uid=:userid  order by s.uid,s.quiz_id"),{"userid":uid})
    column_names4=result4.keys()
    quizdetails=[dict(zip(column_names4,rows4)) for rows4 in result4.fetchall()]
    
        
    return render_template("academic_details.html",subjectcount=subjectcount,quizdetails=quizdetails,uid=uid,subjectmarks=subjectmarks)
@app.route("/home",methods=["GET","POST"])
def home():
    username=session.get('username')
    fullname = db.session.execute(text("select fullname from user where username= :username"), {"username": username}).fetchone()
    return redirect(f"/user/{fullname[0]}")
@app.route("/contact",methods=["GET","POST"])
def contact():
    return render_template("contact.html")
@app.route("/complaint",methods=["GET","POST"])
def complaint():
    name = request.form['name']
    email = session.get("username")
    issue = request.form['issue']
    details=request.form.get('details')
    msg = Message("Complaint Received", recipients=[email])
    msg.body = f"""
Hello {name},

We have received your complaint under: **{issue}**

------------------------------
"{details}"
------------------------------

Our team will get back to you soon.

Best Regards,  
Support Team
"""

    try:
        mail.send(msg)
        flash("Your complaint has been submitted successfully. Check your email for confirmation!", "success")
    except Exception as e:
        flash(f"Error sending email: {str(e)}", "danger")

    return redirect("/contact")
@app.route("/adminhome",methods=["GET","POST"])
def adminhome():
     try:
        result = db.session.execute(text("SELECT * FROM quiz_details"))
        result2 = db.session.execute(text("SELECT * FROM questions"))
        result3 = db.session.execute(text("SELECT * FROM chapters"))
        column_names = result.keys()
        column_names2=result2.keys()
        column_names3 = result3.keys()
        quiz_details = [dict(zip(column_names, row)) for row in result.fetchall()]
        questions=[dict(zip(column_names2,rows2)) for rows2 in result2.fetchall()]
        chapters = [dict(zip(column_names3, rows)) for rows in result3.fetchall()]
        counter=[]
        for chapter in chapters:
            count=0
            for question in questions:
                if question["chapter_id"]==chapter["chaoter_id"]:
                    count=count+1
            counter.append({'chapter_id':chapter["chaoter_id"],"question_count":count})
           
     except Exception as e:
         return f"Error: {str(e)}"
     else:
         return render_template("adminhome.html",quiz_details=quiz_details,chapters=chapters,counter=counter)  
@app.route("/subjects",methods=["GET","POST"])
def subjects():
    result = db.session.execute(text("SELECT * FROM subjects"))
    result2 = db.session.execute(text("SELECT * FROM chapters"))
    column_names = result.keys()
    column_names2 = result2.keys()
    subjects = [dict(zip(column_names, row)) for row in result.fetchall()]
    chapters = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    return render_template("subjects.html",subjects=subjects,chapters=chapters,message="Here are the subjects")
@app.route("/chapters",methods=["GET","POST"])
def chapters():
    result = db.session.execute(text("SELECT * FROM subjects"))
    result2 = db.session.execute(text("SELECT * FROM chapters"))
    column_names = result.keys()
    column_names2 = result2.keys()
    subjects = [dict(zip(column_names, row)) for row in result.fetchall()]
    chapters = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    return render_template("chapters.html",subjects=subjects,chapters=chapters,message1="Here are the chapters")

@app.route("/questions", methods=["GET", "POST"])
def questions():
    try:
        result = db.session.execute(text("SELECT * FROM subjects"))
        column_names = result.keys()
        subjects = [dict(zip(column_names, row)) for row in result.fetchall()]
        result2 = db.session.execute(text("SELECT * FROM chapters"))
        column_names2 = result2.keys()
        chapters = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
        questions_query = db.session.execute(text("""
            SELECT q.qid, q.chapter_id, q.question, o.option, o.option_id, q.answer
            FROM questions q
            LEFT JOIN options o ON q.qid = o.question_id
        """))
        questions = {}
        for row in questions_query:
            if row.qid not in questions:
                questions[row.qid] = {
                    "chapter_id": row.chapter_id,
                    "question_text": row.question,
                    "options": [],
                    "answer": row.answer
                }
            if row.option:
                questions[row.qid]["options"].append({"text": row.option, "id": row.option_id})
        questions_list = []
        for qid, qdata in questions.items():
            questions_list.append({
               "question_id": qid,
               "chapter_id": qdata["chapter_id"],
               "question_text": qdata["question_text"],
               "options": qdata["options"],
               "answer": qdata["answer"]
    })
    except Exception as e:
        return f"Error: {str(e)}"
    if not subjects:
        return render_template("adminhome.html")
    else:
        return render_template(
            "questions.html",
            subjects=subjects,
            message="Here are the subjects",
            message1="Here are the chapters",
            chapters=chapters,
            questions=questions_list,
            message2="Here are the questions"
        )

@app.route("/student_academic_details",methods=["GET","POST"])
def student_academic_details():
    usid=db.session.execute(text("select uid from user"))
    userids=usid.fetchall()
    userquiz=[]
    for userid in userids:
        result=db.session.execute(text("select distinct quizid from quizresponse where uid=:userid "),{"userid":userid[0]})
        quizid1=result.fetchall()
        for quizid in quizid1:
            userquiz.append({"uid":userid[0],"quizid":quizid})
    result2=db.session.execute(text("select subject_name from subjects"))
    subject=result2.fetchall()
    subjectnames=[]
    for subjectname in subject:
        subjectnames.append(subjectname[0])
    subjectcount=[]
    result3=db.session.execute(text("select distinct * from scores a join quiz_details q on a.quiz_id=q.quizid join chapters c on c.chaoter_id=q.chapter_id join subjects s on s.subject_id=c.subject_id"))
    column_names=result3.keys()
    details=[dict(zip(column_names,rows)) for rows in result3.fetchall()]
    for subjectname in subjectnames:
        counter=0
        for detail in details:
            if detail['subject_name']==subjectname:
                counter=counter+1
        subjectcount.append({"subject_name":subjectname,"count":counter})
   
    subjectmarks=[]
    for subjectname in subjectnames:
        result5=db.session.execute(text("select sum(score) from scores where quiz_id in (select quizid from quiz_details where chapter_id in (select chaoter_id from chapters where subject_id in (select subject_id from subjects where subject_name=:subject))) "),{"subject":subjectname})
        subjectsum=result5.scalar() or 0
        subject_entry = next((item for item in subjectcount if item["subject_name"] == subjectname), None)
        if subject_entry:
            subjectavg = subjectsum/subject_entry["count"] if subject_entry["count"] > 0 else 0
        else:
            subjectavg = 0
        subjectmarks.append({"subject_name":subjectname,"avg":round(subjectavg,2)})
    
    result4=db.session.execute(text("select * from scores s join quiz_details q on q.quizid=s.quiz_id join chapters c on c.chaoter_id=q.chapter_id order by s.uid, s.quiz_id"))
    column_names4=result4.keys()
    quizdetails=[dict(zip(column_names4,rows4)) for rows4 in result4.fetchall()]
    
    return render_template("student_academic_details.html",subjectcount=subjectcount,quizdetails=quizdetails,subjectmarks=subjectmarks)
@app.route("/edit/username",methods=["GET","POST"])
def editusername():
    username=session.get('username')
    return render_template("edit.html",option1="Username", option="username",dynamic_name="username",option3=" ",text="text",dynamic_name2=username)
@app.route("/edit/dob",methods=["GET","POST"])
def editdob():
    username=session.get('username')
    dob=db.session.execute(text("select dob from user where username=:username"),{"username":username})
    return render_template("edit.html",option1="Date of birth", option="Date of birth",dynamic_name="dob",option3=" ",text="date",dynamic_name2=dob.scalar())
@app.route("/edit/name",methods=["GET","POST"])
def editname():
    username=session.get('username')
    fullname=db.session.execute(text("select fullname from user where username=:username"),{"username":username})

    return render_template("edit.html",option1="Fullname", option="Fullname",dynamic_name="name",option3=" ",text="text",dynamic_name2=fullname.scalar())
@app.route("/edit/qualification",methods=["GET","POST"])
def editqualification():
    username=session.get('username')
    qualification=db.session.execute(text("select qualification from user where username=:username"),{"username":username})

    return render_template("edit.html",option1="Qualification", option="Qualification",dynamic_name="qualification",option3=" ",text="text",dynamic_name2=qualification.scalar())
@app.route("/edit/password",methods=["GET","POST"])
def editpassword():
    return render_template("edit.html",option1="Password", option=" New Password",dynamic_name="password1",option3=" old ",text="password")
@app.route("/editcomplete", methods=["GET", "POST"])
def editcomplete():
    new_username = request.form.get("username")
    new_dob = request.form.get("dob")
    new_qualification = request.form.get("qualification")
    new_name = request.form.get("name")
    new_password=request.form.get("password1")
    password = request.form.get("password")
    if not password:
        return render_template("edit.html", warningg="Password is required")
    current_username = session.get("username")
    storedpass = session.get("password")
    updates = {}
    if new_username:
        updates['username'] = new_username
        if password != storedpass:
          return redirect(f"/edit/username")
    if new_dob:
        updates['dob'] = new_dob
        if password != storedpass:
          return redirect(f"/edit/dob")
    if new_qualification:   
        updates['qualification'] = new_qualification
        if password != storedpass:
          return redirect(f"/edit/qualification")
    if new_name:
        updates['fullname'] = new_name
        if password != storedpass:
          return redirect(f"/edit/name")
    if new_password:
        updates['password'] = new_password
        if password != storedpass:
          return redirect(f"/edit/password")
    if not updates:
        return redirect(f"/personal_details")
    try:
        for field, value in updates.items():
            query = text(f"UPDATE user SET {field} = :value WHERE username = :current_username")
            db.session.execute(query, {"value": value, "current_username": current_username})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return redirect(f"/personal_details",warinngg="Unable to edit")
    if new_username:
        result = db.session.execute(text("SELECT username FROM user WHERE username = :username"), {"username": new_username}).fetchone()
        if result and result[0] == new_username:
            session["username"] = new_username
    if new_password:
        result = db.session.execute(text("SELECT password FROM user WHERE username = :username"), {"username": current_username}).fetchone()
        if result and result[0] == new_password:
            session["password"] = new_password
    return redirect(f"/personal_details")
@app.route("/student_personal_details", methods=["GET", "POST"])
def student_personal_details():
    try:
        result = db.session.execute(text("SELECT * FROM user"))
        column_names = result.keys()
        users = [dict(zip(column_names, row)) for row in result.fetchall()]
    except Exception as e:
        return f"Error: {str(e)}"
    if not users:
        return render_template("student_personal_details.html", heading="No users registered")
    else:
        return render_template("student_personal_details.html",heading="Here are the details of all the users registered",users=users)
@app.route("/addsubject",methods=["GET","POST"])
def addsubject():
    return render_template("addnew.html",option="Subject", option1="Subject",dynamic_name="subject",option5="Add",option4="add",option6="add")
@app.route("/edit/<int:subject_id>",methods=["GET","POST"])
def edit_subject(subject_id):
    sub = db.session.execute(
    text("SELECT subject_name FROM subjects WHERE subject_id = :subject_id"),
    {"subject_id": subject_id}).fetchone()
    descript = db.session.execute(
    text("SELECT description FROM subjects WHERE subject_id = :subject_id"),
    {"subject_id": subject_id}).fetchone()
    subject1=sub[0]
    description=descript[0]
    return render_template("addnew.html",option="Subject", option1="Subject",dynamic_name="subject",option5="Edit",option6="editsubject",option4="edit",s_id=subject_id,s_name=subject1,description=description)
@app.route("/editch/<int:chapter_id>", methods=["GET", "POST"])
def edit_chapter(chapter_id):
    try:
        result = db.session.execute(text("SELECT * FROM subjects"))
        column_names = result.keys()
        subjects1 = [dict(zip(column_names, row)) for row in result.fetchall()]
        chapter = db.session.execute(
            text("SELECT chapter_name, subject_id, description FROM chapters WHERE chaoter_id = :chapter_id"),
            {"chapter_id": chapter_id}
        ).fetchone()
        if not chapter:
            return "Error: Chapter not found.", 404
        chapter_name = chapter[0]
        current_subject_id = chapter[1]
        description = chapter[2]
        return render_template(
            "addnewchapter.html",
            option="Chapter",
            option1="Chapter",
            dynamic_name="chapter",
            subjects1=subjects1,
            option3="Edit",
            option4="edit",
            chapter_id=chapter_id,
            chapter_name=chapter_name,
            current_subject_id=current_subject_id,
            description=description
        )
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
@app.route("/edit_quiz/<int:quiz_id>",methods=["GET","POST"])
def edit_quiz(quiz_id):
    result = db.session.execute(text("SELECT * FROM quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    column_names = result.keys()
    quiz_detail = [dict(zip(column_names, row)) for row in result.fetchall()]
    quiz_details=quiz_detail[0]
    result2 = db.session.execute(text("SELECT * FROM chapters"))
    column_names2 = result2.keys()
    chapters = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    return render_template( "addnewquiz.html",chapters=chapters,quiz_id=quiz_id,option4="edit",option5="edit",option3="Edit",option1="Quiz",date=quiz_details["quiz_date"],duration=int(quiz_details["duration"]),current_chapter_id=int(quiz_details["chapter_id"]))
@app.route("/editcompletequiz/<int:quiz_id>",methods=["GET","POST"])
def editcompletequiz(quiz_id):
    date=request.form.get("date")
    chapter_id=request.form.get("chapter_id")
    duration=request.form.get("duration")
    if not date or not chapter_id or not duration:
        return redirect(f"/adminhome")
    db.session.execute(text("update quiz_details set quiz_date=:date,duration=:duration,chapter_id=:chapter_id where quizid=:quizid"),{"quizid":quiz_id,"chapter_id":chapter_id,"duration":duration,"date":date})
    db.session.commit()
    return redirect(f"/adminhome")

@app.route("/editcompletech/<int:chapter_id>", methods=["POST"])
def edit_chapter_complete(chapter_id):
    try:
        new_chapter_name = request.form.get("chapter")
        new_subject_id = request.form.get("sub_id")
        new_description = request.form.get("description")
        if not chapter_id or not new_chapter_name or not new_subject_id or not new_description:
            return "Error: Missing data. Please provide all required fields.", 400
        db.session.execute(
            text("UPDATE chapters SET chapter_name = :new_chapter_name, subject_id = :new_subject_id, description = :new_description WHERE chaoter_id = :chapter_id"),
            {
                "new_chapter_name": new_chapter_name,
                "new_subject_id": new_subject_id,
                "new_description": new_description,
                "chapter_id": chapter_id
            }
        )
        db.session.commit()

        return redirect(f"/chapters")
    except Exception as e:
        db.session.rollback() 
        return f"An error occurred: {str(e)}", 500
@app.route("/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    try:
        chapters_result = db.session.execute(text("SELECT * FROM chapters"))
        chapters = [dict(row._mapping) for row in chapters_result.fetchall()] 
        question = db.session.execute(
            text("SELECT question, chapter_id, answer FROM questions WHERE qid = :question_id"),
            {"question_id": question_id}
        ).fetchone()

        if not question:
            return "Error: Question not found.", 404
        options_result = db.session.execute(
            text("SELECT option_id, `option` FROM options WHERE question_id = :question_id"),
            {"question_id": question_id}
        ).fetchall()
        options = [dict(row._mapping) for row in options_result] 
        question_text = question[0]
        current_chapter_id = question[1]
        current_answer_id = question[2]

        return render_template(
            "addquestion.html",
            option="Question",
            option1="Question",
            dynamic_name="question",
            chapters=chapters,
            options=options,
            question_id=question_id,
            question_text=question_text,
            current_chapter_id=current_chapter_id,
            current_answer_id=current_answer_id,
            option3="edit",
            option4="Edit",
            option5="edit",
            enumerate=enumerate
        )

    except Exception as e:
        return f"An error occurred: {e}", 500


@app.route("/editcompleteque/<int:question_id>", methods=["GET", "POST"])
def editcompleteque(question_id):
    try:
        new_question_text = request.form.get("question_text")
        new_answer = request.form.get("correct_option")
        new_chapter_id = request.form.get("chapter_id")
        options=[]
        optionids=[]
        for i in range (1,5):
            opt=request.form.get(f"option{i}")
            options.append(opt)
        optids=db.session.execute(text("select option_id from options where question_id=:question_id"),{"question_id":question_id})
        optid=optids.fetchall()
        for optid1 in optid:
            optionids.append(optid1[0])
        for i in range(0,4):
            db.session.execute(
                text("""
                    UPDATE options
                    SET `option` = :new_option
                    WHERE question_id = :question_id AND option_id = :option_id
                """),
                {
                    "new_option": options[i],
                    "question_id": question_id,
                    "option_id": optionids[i],
                }
            )
        db.session.commit()
    
        corrid = optionids[int(new_answer) - 1]
        db.session.execute(
            text("""
                UPDATE questions
                SET question = :new_question_text, chapter_id = :new_chapter_id, answer = :opt_id
                WHERE qid = :question_id
            """),
            {
                "new_question_text": new_question_text,
                "new_chapter_id": new_chapter_id,
                "opt_id": corrid,
                "question_id": question_id,
            }
        )
        db.session.commit()
        return redirect("/questions")

    except Exception as e:
        db.session.rollback()
        return "An error occurred", 500

@app.route("/editsubjectcomplete/<int:subject_id>", methods=["POST"])
def edit_subject_complete(subject_id):
    try:
        new_subject_name = request.form.get("subject")
        new_description = request.form.get("description")
        if not subject_id or not new_subject_name or not new_description:
            return "Error: Missing data. Please provide all required fields.", 400
        db.session.execute(
            text("UPDATE subjects SET subject_name = :new_subject_name, description = :new_description WHERE subject_id = :subject_id"),
            {
                "new_subject_name": new_subject_name,
                "new_description": new_description,
                "subject_id": subject_id
            }
        )
        db.session.commit()

        return redirect(f"/subjects")
    except Exception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}", 500

@app.route("/addcomplete/",methods=["GET","POST"])
def addcomplete():
    new_subject=request.form.get("subject")
    new_description=request.form.get("description")
    if not new_subject or not new_description:
        return render_template("addnew.html",option="Subject", option1="Subject",dynamic_name="subject",warningg="Fill the required field",option5="Add",option4="add")
    else:
        new_entry=Subjects(subject_name=new_subject,description=new_description)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(f"/subjects")

@app.route("/addchapter",methods=["GET","POST"])
def addchapter():
     result = db.session.execute(text("SELECT * FROM subjects"))
     column_names = result.keys()
     subjects1= [dict(zip(column_names, row)) for row in result.fetchall()]
     return render_template("addnewchapter.html",option="Chapter", option1="Chapter",dynamic_name="chapter",subjects1=subjects1,option3="Add",option4="add")
@app.route("/addquiz",methods=["GET","POST"])
def addquiz():
     result = db.session.execute(text("SELECT * FROM chapters"))
     column_names = result.keys()
     chapters= [dict(zip(column_names, row)) for row in result.fetchall()]
     return render_template("addnewquiz.html",option="Quiz", option1="Quiz",chapters=chapters,option3="Add",option4="add")
@app.route("/addcompletequiz",methods=["GET","POST"])
def addcompletequiz():
    date=request.form.get("date")
    chapter_id=request.form.get("chapter_id")
    duration=request.form.get("duration")
    result = db.session.execute(text("SELECT * FROM chapters"))
    column_names = result.keys()
    chapters= [dict(zip(column_names, row)) for row in result.fetchall()]
    if not date or not chapter_id or not duration:
        return render_template("addnewquiz.html",option="Quiz", option1="Quiz",chapters=chapters,option3="Add",option4="add",warningg="Fill the required field")
    new_quiz=QuizDetails(quiz_date=date,duration=duration,chapter_id=chapter_id)
    db.session.add(new_quiz)
    db.session.commit()
    return redirect(f"/adminhome")
@app.route("/addcompletech/",methods=["GET","POST"])
def addcompletech():
    new_chapter=request.form.get("chapter")
    sub_id=request.form.get("sub_id")
    new_description=request.form.get("description")
    exist_sub_query = db.session.execute(text("SELECT subject_id FROM subjects"))
    exist_sub = [row.subject_id for row in exist_sub_query] 
    if not new_chapter or not new_description or not sub_id:
        return render_template("addnewchapter.html",option="Subject", option1="Subject",dynamic_name="subject",warningg="Fill the required field")
    if int(sub_id) not in exist_sub:
        return render_template("addnewchapter.html",warningg="Subject don't exist",option="Chapter", option1="Chapter",dynamic_name="chapter")
    else:
        new_entry=Chapters(subject_id=sub_id,chapter_name=new_chapter,description=new_description)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(f"/chapters")
@app.route("/addquestion", methods=["GET", "POST"])
def addquestion():
    result = db.session.execute(text("SELECT * FROM chapters"))
    column_names = result.keys()
    chapters = [dict(zip(column_names, row)) for row in result.fetchall()]
    return render_template( "addquestion.html",chapters=chapters,option4="Add",enumerate=enumerate,option5="add")

@app.route("/addcompleteque", methods=["POST"])
def addcompletequestion():
    question_text = request.form.get("question_text")
    chapter_id = request.form.get("chapter_id")
    options = [
        request.form.get("option1"),
        request.form.get("option2"),
        request.form.get("option3"),
        request.form.get("option4"),
    ]
    correct_option = request.form.get("correct_option")
    if not question_text or not chapter_id or not all(options) or not correct_option:
        return render_template(
            "addquestion.html",
            chapters=db.session.execute(text("SELECT * FROM chapters")).fetchall(),
            warningg="All fields are required.",
        )
    if not chapter_id.isdigit() or int(correct_option) not in range(1, 5):
        return render_template(
            "addquestion.html",
            chapters=db.session.execute(text("SELECT * FROM chapters")).fetchall(),
            warningg="Invalid chapter ID or correct option.",
        )
    try:
        new_question = Questions(
            chapter_id=int(chapter_id),
            question=question_text, 
        )
        db.session.add(new_question)
        db.session.commit()
        question_id = new_question.qid  
        for option in options:
            new_option = Options(
                question_id=question_id,
                option=option,
            )   
            db.session.add(new_option)
        db.session.commit()
        corr=options[int(correct_option)-1]
        result2=db.session.execute(text("select option_id from options where option=:option and question_id= :question_id"),{"option":corr, "question_id":question_id})

        opt_id = result2.scalar()
        db.session.execute(text("UPDATE questions SET answer = :opt_id WHERE qid = :question_id"), {"opt_id": opt_id, "question_id": question_id})
        db.session.commit()
        return redirect("/questions")
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"
@app.route("/deletesubject/<int:subject_id>",methods=["GET","POST"])
def delete_subject(subject_id):
    db.session.execute(text("delete from subjects where subject_id=:subject_id"),{"subject_id":subject_id})
    db.session.execute(text("delete from options where question_id in (Select qid from questions where chapter_id in (select chaoter_id from chapters WHERE subject_id = :subject_id))"), {"subject_id": subject_id})
    db.session.execute(text(" DELETE FROM questions where chapter_id in (select chaoter_id from chapters WHERE subject_id = :subject_id)"), {"subject_id": subject_id})
    db.session.execute(text("delete from chapters where subject_id=:subject_id"),{"subject_id":subject_id})
    db.session.commit()
    return redirect(f"/subjects")
@app.route("/deletechapter/<int:chapter_id>",methods=["GET","POST"])
def delete_chapter(chapter_id):
    db.session.execute(text("delete from chapters where chaoter_id=:chapter_id"),{"chapter_id":chapter_id})
    db.session.execute(text("delete from options where question_id in (Select qid from questions where chapter_id=:chapter_id)"),{"chapter_id": chapter_id})
    db.session.execute(text("delete from questions where chapter_id=:chapter_id"),{"chapter_id":chapter_id})
    db.session.commit()
    return redirect(f"/chapters")
@app.route("/delete_question/<int:question_id>",methods=["GET","POST"])
def delete_question(question_id):
    db.session.execute(text("delete from options where question_id=:question_id"),{"question_id":question_id})
    db.session.execute(text("delete from questions where qid=:question_id"),{"question_id":question_id})
    db.session.commit()
    return redirect(f"/questions")
@app.route("/delete_quiz/<int:quiz_id>",methods=["GET","POST"])
def delete_quiz(quiz_id):
    db.session.execute(text("delete from quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    db.session.commit()
    db.session.execute(text("delete from quizresponse where quizid=:quiz_id"),{"quiz_id":quiz_id})
    db.session.commit()
    db.session.execute(text("delete from scores where quiz_id=:quiz_id"),{"quiz_id":quiz_id})
    db.session.commit()
    return redirect(f"/adminhome")
@app.route("/delete_user/<int:userid>",methods=["GET","POST"])
def delete_user(userid):
    db.session.execute(text("delete from user where uid=:uid"),{"uid":userid})
    db.session.execute(text("delete from File where uid=:uid"),{"uid":userid})
    db.session.commit()
    return redirect(f"/student_personal_details")
@app.route("/logout",methods=["GET","POST"])
def logout():
    session.clear()
    return redirect(f"/")
@app.route('/user/<fullname>', methods=['GET','POST'])
def user_profile(fullname):
    result = db.session.execute(text("SELECT * FROM subjects"))
    result2 = db.session.execute(text("SELECT * FROM chapters"))
    column_names = result.keys()
    column_names2 = result2.keys()
    subjects = [dict(zip(column_names, row)) for row in result.fetchall()]
    chapters = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    return render_template("user.html",subjects=subjects,chapters=chapters)
@app.route("/quizbysubject/<int:subject_id>",methods=["Get","POST"])
def quizbysubject(subject_id):
    return render_template("quizinstructions.html",name="subject",id=subject_id,duration=120)
@app.route("/quizbychapter/<int:chapter_id>",methods=["Get","POST"])
def quizbychapter(chapter_id):
    return render_template("quizinstructions.html",name="chapter",id=chapter_id,duration=45)
@app.route("/startquizbysubject/<int:subject_id>",methods=["GET","POST"])
def startquizbysubject(subject_id):
    result = db.session.execute(text("SELECT * FROM questions where chapter_id IN (select chaoter_id from chapters where subject_id=:subject_id)"),{"subject_id":subject_id})
    result2 = db.session.execute(text("SELECT * FROM options"))
    column_names = result.keys()
    column_names2 = result2.keys()
    questions = [dict(zip(column_names, row)) for row in result.fetchall()]
    options = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    return render_template("quiz.html",questions=questions,options=options,duration=45)
@app.route("/quizinstructions/<int:quiz_id>",methods=["Get","POST"])
def quizinstructions(quiz_id):
    result=db.session.execute(text("select duration from quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    duration=result.scalar()

    return render_template("quizinstructions.html",name="chapter",id=quiz_id,duration=duration)
@app.route("/startquiz/<int:quiz_id>",methods=["Get","POST"])
def startquiz(quiz_id):
    result3=db.session.execute(text("select * from quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    column_names3=result3.keys()
    quiz_details=[dict(zip(column_names3,rows3)) for rows3 in result3.fetchall()]
    result = db.session.execute(text("SELECT * FROM questions where chapter_id= :chapter_id"),{"chapter_id": quiz_details[0]["chapter_id"]})
    result2 = db.session.execute(text("SELECT * FROM options"))
    column_names = result.keys()
    column_names2 = result2.keys()
    questions = [dict(zip(column_names, row)) for row in result.fetchall()]
    options = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    return render_template("quiz.html",questions=questions,options=options,duration=quiz_details[0]["duration"],quiz_id=quiz_id)
@app.route("/submitquiz/<int:quiz_id>",methods=["GET","POST"])
def submitquiz(quiz_id):
    result=db.session.execute(text("select chapter_id from quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    chapter_id=result.scalar()
    result2 = db.session.execute(text("SELECT * FROM questions where chapter_id= :chapter_id"),{"chapter_id": chapter_id}).mappings()
    questions = [dict(row) for row in result2.fetchall()]
    for question in questions :
        username=session.get('username')
        userid=db.session.execute(text("select uid from user where username= :username"),{"username":username})
        opt_id=request.form.get(f"question_{question['qid']}")
        new_quizresponse=QuizResponse(quizid=quiz_id,uid=userid.scalar(),questionid=question['qid'],optionid=opt_id)
        db.session.add(new_quizresponse)
        db.session.commit()
    userid=db.session.execute(text("select uid from user where username= :username"),{"username":username})
    uid=userid.scalar()
    time_taken=request.form.get("time_taken")
    return redirect(f"/scores/{quiz_id}/{uid}/{time_taken}")
@app.route("/scores/<int:quiz_id>/<int:uid>/<int:time_taken>",methods=["GET","POST"])
def scores(quiz_id,uid,time_taken):
    minutes=int(time_taken/60)
    seconds=time_taken%60
    result3=db.session.execute(text("select * from quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    column_names3=result3.keys()
    quiz_details=[dict(zip(column_names3,rows3)) for rows3 in result3.fetchall()]
    result = db.session.execute(text("SELECT * FROM questions where chapter_id= :chapter_id"),{"chapter_id": quiz_details[0]["chapter_id"]})
    result2 = db.session.execute(text("SELECT * FROM options"))
    column_names = result.keys()
    column_names2 = result2.keys()
    questions = [dict(zip(column_names, row)) for row in result.fetchall()]
    options = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    result4=db.session.execute(text("select * from quizresponse where quizid=:quiz_id"),{"quiz_id":quiz_id})
    column_names4=result4.keys()
    quizresponses=[dict(zip(column_names4,rows4))for rows4 in result4.fetchall()]
    scorecount=0
    questioncount=0
    result3 = db.session.execute(text("SELECT * FROM quizresponse where quizid= :quiz_id AND uid=:userid"),{"quiz_id": quiz_id,"userid":uid}).mappings()
    responses = [dict(row) for row in result3.fetchall()]
    for response in responses :
        for question in questions :
            if question['qid']== response['questionid'] :
                questioncount=questioncount+1
                if question['answer']==response['optionid']:
                    scorecount=scorecount+1
    result6=db.session.execute(text("select * from scores where quiz_id=:quiz_id and uid=:uid"),{"quiz_id":quiz_id,"uid":uid})
    result7=result6.fetchall()
    if not result7:
        new_score=Scores(quiz_id=quiz_id,uid=uid,time_stamp=time_taken,score=scorecount,total=questioncount)
        db.session.add(new_score)
        db.session.commit()
    return render_template("scores.html",score=scorecount,minutes=minutes,seconds=seconds,dynamic_name1="home",dynamic_name2="academic_details",dynamic_name3="Attempted Quizzes",total=questioncount,questions=questions,options=options,quizresponses=quizresponses)
@app.route("/viewchapter/<int:chapter_id>",methods=["GET","POST"])
def viewchapter(chapter_id):
    chapter = Chapters.query.get(chapter_id)
    if chapter:
        return render_template('chapter_page.html', chapter=chapter)
    else:
        return "Chapter not found", 404
@app.route("/livequiz",methods=["GET","POST"])
def livequiz():
    tdate=date.today()
    result=db.session.execute(text("select * from quiz_details where quiz_date>=:date order by (quiz_date) "),{"date":str(tdate)})
    column_names=result.keys()
    quiz_details=[dict(zip(column_names,row)) for row in result.fetchall()]
    result2=db.session.execute(text("select * from chapters"))
    column_names2=result2.keys()
    chapters=[dict(zip(column_names2,row2)) for row2 in result2.fetchall()]
    result3=db.session.execute(text("select * from subjects"))
    column_names3=result3.keys()
    subjects=[dict(zip(column_names3,row3)) for row3 in result3.fetchall()]
    username=session.get('username')
    userid=db.session.execute(text("select uid from user where username= :username"),{"username":username})
    uid=userid.scalar()
    result4=db.session.execute(text("select distinct(quizid) from quizresponse where uid=:uid"),{"uid":uid})
    column_names4=result4.keys()
    quizresponses=[dict(zip(column_names4,rows4))for rows4 in result4.fetchall()]
    listforquiz=[]
    for quiz_detail in quiz_details:
        arg=0
        if quiz_detail["quiz_date"]==str(tdate):
            arg=1
        for chapter in chapters:
            for subject in subjects:
                if quiz_detail["chapter_id"]==chapter["chaoter_id"]:
                    if chapter["subject_id"]==subject["subject_id"]:
                        result4=db.session.execute(text("select count(*)from questions where chapter_id in (select chaoter_id from chapters where chaoter_id=:chapter_id) order by(qid);"),{"chapter_id":chapter["chaoter_id"]})
                        listforquiz.append({"quizid":quiz_detail["quizid"],"chapter_id":chapter["chaoter_id"],"chapter_name":chapter["chapter_name"],"subjectname":subject["subject_name"],"questioncount":result4.scalar(),"arg":arg})

    return render_template("livequiz.html",listforquiz=listforquiz,quiz_details=quiz_details,quizresponses=quizresponses,curr_id=uid)
@app.route("/transcript/<int:quiz_id>/<int:uid>",methods=["GET","POST"])
def transcript  (quiz_id,uid):
    time_taken=request.form.get("time_taken")
    result3=db.session.execute(text("select * from quiz_details where quizid=:quiz_id"),{"quiz_id":quiz_id})
    column_names3=result3.keys()
    quiz_details=[dict(zip(column_names3,rows3)) for rows3 in result3.fetchall()]
    result = db.session.execute(text("SELECT * FROM questions where chapter_id= :chapter_id"),{"chapter_id": quiz_details[0]["chapter_id"]})
    result2 = db.session.execute(text("SELECT * FROM options"))
    column_names = result.keys()
    column_names2 = result2.keys()
    questions = [dict(zip(column_names, row)) for row in result.fetchall()]
    options = [dict(zip(column_names2, rows)) for rows in result2.fetchall()]
    result4=db.session.execute(text("select * from quizresponse where quizid=:quiz_id"),{"quiz_id":quiz_id})
    column_names4=result4.keys()
    quizresponses=[dict(zip(column_names4,rows4))for rows4 in result4.fetchall()]
    scorecount=0
    questioncount=0
    result3 = db.session.execute(text("SELECT * FROM quizresponse where quizid= :quiz_id AND uid=:userid"),{"quiz_id": quiz_id,"userid":uid}).mappings()
    responses = [dict(row) for row in result3.fetchall()]
    for response in responses :
        for question in questions :
            if question['qid']== response['questionid'] :
                questioncount=questioncount+1
                if question['answer']==response['optionid']:
                    scorecount=scorecount+1
    time=db.session.execute(text("select time_stamp from scores where quiz_id=:quiz_id and uid=:uid"),{"quiz_id": quiz_id,"uid":uid})
    timestamps=time.fetchone()
    timestamp=timestamps[0]
    minutes=int(int(timestamp)/60)
    seconds=int(int(timestamp)%60)
    
    return render_template("scores.html",minutes=minutes,seconds=seconds,score=scorecount,total=questioncount,dynamic_name1="adminhome",dynamic_name2="student_academic_details",dynamic_name3="Academics",questions=questions,options=options,quizresponses=quizresponses)
"""@app.route("/adminsearch",methods=["GET","POST"])
def adminsearch():
    return render_template("adminsearch.html")
@app.route("/usersearch",methods=["GET","POST"])
def usersearch():
    search=request.form.get("search")
    query = text("SELECT * FROM chapters WHERE chapter_name LIKE :search")
    result = db.session.execute(query, {"search": f"%{search}%"})
    column_names=result.keys()
    chapters=[dict(zip(column_names,row)) for row in result.fetchall()]
    query2 = text("SELECT * FROM quiz_details WHERE chapter_id in (select chaoter_id from chapters where chapter_name LIKE :search)")
    result2 = db.session.execute(query2, {"search": f"%{search}%"})
    column_names2=result2.keys()
    quizzes=[dict(zip(column_names2,row2)) for row2 in result2.fetchall()]

    return render_template("search.html",chapters=chapters,quizzes=quizzes)"""
