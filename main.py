from flask import Flask , render_template , request , redirect , url_for , session , flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime , date
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

curr_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quizmaster.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "QUIZ_MASTER"
app.config["UPLOAD_FOLDER"]= os.path.join(curr_dir , "static" , "imgs")

db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(80),nullable=False)
    email=db.Column(db.String(120), unique=True, nullable=False)
    password=db.Column(db.String(120), nullable=False)
    quali=db.Column(db.String(120), nullable=False)
    dob=db.Column(db.String(120), nullable=False)
    is_admin=db.Column(db.Boolean, nullable=False,default=False)
    scores=db.relationship('Scores', back_populates='user' ,cascade='all, delete-orphan')


class Subjects(db.Model):
    __tablename__ = 'subjects'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(80),nullable=False)
    description=db.Column(db.String(120), nullable=False)
    chap=db.relationship('Chapters', back_populates='sub', cascade='all, delete-orphan')


class Chapters(db.Model):
    __tablename__ = 'chapters'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(80),nullable=False)
    description=db.Column(db.String(120), nullable=False)
    subject_id=db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    sub=db.relationship('Subjects', back_populates='chap')
    quiz=db.relationship('Quizzes', back_populates='chapter', cascade='all, delete-orphan')

class Quizzes(db.Model):
    __tablename__ = 'quizzes'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), nullable=False)
    date_of_quiz=db.Column(db.Date, nullable=False)
    time_duration=db.Column(db.Integer, nullable=False)    
    remarks=db.Column(db.String(120), nullable=False)
    chapter_id=db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    chapter=db.relationship('Chapters', back_populates='quiz')
    question=db.relationship('Questions', back_populates='quiz', cascade='all, delete-orphan')
    scores=db.relationship('Scores', back_populates='quiz', cascade='all, delete-orphan')

class Questions(db.Model):
    __tablename__ = 'questions'
    id=db.Column(db.Integer, primary_key=True)
    question=db.Column(db.String(120), nullable=False)
    option1=db.Column(db.String(120), nullable=False)
    option2=db.Column(db.String(120), nullable=False)
    option3=db.Column(db.String(120), nullable=False)
    option4=db.Column(db.String(120), nullable=False)
    correct_option=db.Column(db.Integer, nullable=False)
    quiz_id=db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    quiz=db.relationship('Quizzes', back_populates='question')

class Scores(db.Model):
    __tablename__ = 'scores'
    id=db.Column(db.Integer, primary_key=True)
    score=db.Column(db.Integer, nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id=db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    time_stamp=db.Column(db.DateTime, nullable=False)
    total_score=db.Column(db.Integer, nullable=False)
    quiz=db.relationship('Quizzes', back_populates='scores')
    user=db.relationship('Users', back_populates='scores')


def create_admin():
    admin_user = Users.query.filter(Users.email == "admin@gmail.com").first()
    if not admin_user:
        admin=Users(name = "admin" , email = "admin@gmail.com" , password = "0000" , quali = "BS Data Science And Applications" , dob = "01-01-2001" , is_admin = True )
        db.session.add(admin)
        db.session.commit()

db.create_all()
create_admin()

@app.route("/")
def hello_world():
    return redirect("/login")

@app.route("/login" , methods = ["GET" , "POST"])
def login():
    if request.method == "GET" :
        return render_template("login.html")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = Users.query.filter_by(email = email).first()
        if user:
            if user.is_admin:
                if user.password == password:
                    #Session is a dictionary in flask
                    session["admin"] = user.id
                    return redirect("/admin")
                else:
                    flash ("Incorrect Password!" , "error")
                    return redirect("/login")
            else:
                if user.password == password:
                    session["user"] = user.id
                    return redirect("/user")
                else:
                    flash ("Incorrect Password!" , "error")
                    return redirect("/login")
        else:
            flash ("User does not exist!" , "error")
            return redirect("/login")
        

# Creating Register route
@app.route("/register" , methods = ["GET" , "POST"])
def register():
    if request.method == "GET" :
        return render_template("register.html")
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        quali = request.form["qualification"]
        dob = request.form["dob"]
        user = Users.query.filter_by(email = email).first()
        if user:
            flash ("User already exists!" , "error")
            return redirect("/register")
        else:
            user = Users(name = name , email = email , password = password , quali = quali , dob = dob)
            db.session.add(user)
            db.session.commit()
            flash ("Registered successfully!" , "success")
            return redirect("/login")


@app.route("/admin")
def admin_dashboard():
    if "admin" in session:
        subjects = Subjects.query.all()
        scores = Scores.query.all()
        return render_template("admin_dashboard.html", all_subjects = subjects , scores=scores)
    else:
        return redirect("/login")
    
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin")
    return redirect("/login")

@app.route("/view_subject/<int:subject_id>")
def view_subject(subject_id):
    if "admin" in session:
        subject = Subjects.query.filter_by(id=subject_id).first()
        chapters = Chapters.query.filter_by(subject_id=subject_id).all()
        return render_template("view_subject.html", subject = subject , chapters=chapters)
    return redirect("/login")

@app.route("/view_chapter/<int:chapter_id>")
def view_chapter(chapter_id):
    if "admin" in session:
        chapter = Chapters.query.filter_by(id=chapter_id).first()
        quizzes = Quizzes.query.filter_by(chapter_id=chapter_id).all()
        return render_template("view_chapter.html", chapter = chapter , quizzes=quizzes)
    return redirect("/login")
    
@app.route("/view_quiz/<int:quiz_id>")
def view_quiz(quiz_id):
    if "admin" in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        return render_template("view_quiz.html", quiz = quiz , questions=questions)
    return redirect("/login")

@app.route("/create_subject" , methods = ["GET" , "POST"])
def create_subject():
    if "admin" in session:
        if request.method == "POST" :
            name = request.form["name"]
            description = request.form["description"]
            new_subject = Subjects(name = name , description = description)
            db.session.add(new_subject)
            db.session.commit()
            flash ("Subject created successfully!" , "success")
            return redirect("/admin")
        else:
            return render_template("create_subject.html")
    else:
        return redirect("/login")
    
@app.route("/edit_subject/<int:subject_id>" , methods = ["GET" , "POST"])
def edit_subject(subject_id):
    if "admin" in session:
        subject = Subjects.query.filter_by(id = subject_id).first()
        if not subject:
            return redirect("/admin")
        
        if request.method == "POST" :
            name = request.form["name"]
            description = request.form["description"]

            subject.name = name
            subject.description = description

            db.session.commit()
            flash ("Subject updated successfully!", "success")
            return redirect("/admin")
        else:
            return render_template("edit_subject.html" , subject = subject)
    else:
        return redirect("/login")
    
@app.route("/delete_subject/<int:subject_id>" , methods = ["GET" , "POST"])
def delete_subject(subject_id):
    if "admin" in session:
        subject = Subjects.query.filter_by(id = subject_id).first()
        if not subject:
            return redirect("/admin")
        if request.method == "POST":
            db.session.delete(subject)
            db.session.commit()
            return redirect("/admin")
        return render_template("del_confirm.html" , subject=subject)
    else:
        return redirect("/login")


@app.route("/create_chapter/<int:subject_id>" , methods = ["GET" , "POST"])
def create_chapter(subject_id):
    if "admin" in session:
        if request.method == "POST" :
            name = request.form["name"]
            description = request.form["description"]
            new_chapter = Chapters(name = name , description = description , subject_id = subject_id)
            db.session.add(new_chapter)
            db.session.commit()
            flash ("Chapter created successfully!" , "success")
            return redirect(url_for("view_subject" , subject_id = subject_id))
        else:
            return render_template("create_chapter.html" , subject_id = subject_id)
    else:
        return redirect("/login")
    
@app.route("/edit_chapter/<int:chapter_id>" , methods = ["GET" , "POST"])
def edit_chapter(chapter_id):
    if "admin" in session:
        chapter = Chapters.query.filter_by(id = chapter_id).first()
        if not chapter:
            return redirect("/admin")
        
        if request.method == "POST" :
            name = request.form["name"]
            description = request.form["description"]
            subject_id = chapter.subject_id
            chapter.name = name
            chapter.description = description

            db.session.commit()
            flash("Chapter updated successfully!", "success")
            return redirect(url_for("view_subject" , subject_id = subject_id))
        else:
            return render_template("edit_chapter.html" , chapter = chapter)
    else:
        return redirect("/login")
    
@app.route("/delete_chapter/<int:chapter_id>" , methods = ["GET" , "POST"])
def delete_chapter(chapter_id):
    if "admin" in session:
        chapter = Chapters.query.filter_by(id = chapter_id).first()
        if not chapter:
            return redirect("/admin")
        if request.method == "POST":
            subject_id = chapter.subject_id
            db.session.delete(chapter)
            db.session.commit()
            return redirect(url_for("view_subject" , subject_id = subject_id))
        return render_template("del_confirm.html" , chapter=chapter)
    else:
        return redirect("/login")
    

@app.route("/create_quiz/<int:chapter_id>" , methods = ["GET" , "POST"])
def create_quiz(chapter_id):
    if "admin" in session:
        if request.method == "POST" :
            name = request.form["name"]
            date_of_quiz = request.form["date_of_quiz"]
            time_duration = request.form["time_duration"]
            remarks = request.form["remarks"]

            doq = datetime.strptime(date_of_quiz , "%Y-%m-%d")
            
            new_quiz = Quizzes(name = name , date_of_quiz = doq , time_duration = time_duration , remarks = remarks , chapter_id = chapter_id)
            db.session.add(new_quiz)
            db.session.commit()
            flash ("Quiz created successfully!" , "success")
            return redirect(url_for("view_chapter" , chapter_id = chapter_id))
        else:
            return render_template("create_quiz.html" , chapter_id = chapter_id)
    else:
        return redirect("/login")
    

@app.route("/edit_quiz/<int:quiz_id>" , methods = ["GET" , "POST"])
def edit_quiz(quiz_id):
    if "admin" in session:
        quiz = Quizzes.query.filter_by(id = quiz_id).first()
        if not quiz :
            return redirect("/admin")
        
        if request.method == "POST" :
            name = request.form["name"]
            date_of_quiz = request.form["date_of_quiz"]
            time_duration = request.form["time_duration"]
            remarks = request.form["remarks"]

            doq = datetime.strptime(date_of_quiz , "%Y-%m-%d")
            
            quiz.name = name
            quiz.date_of_quiz = doq
            quiz.time_duration = time_duration
            quiz.remarks = remarks

            db.session.commit()
            flash("Quiz updated successfully!", "success")
            return redirect(url_for("view_chapter" , chapter_id = quiz.chapter_id))
        else:
            return render_template("edit_quiz.html" , quiz = quiz)
        
    else:
        return redirect("/login")
    
@app.route("/delete_quiz/<int:quiz_id>" , methods = ["GET" , "POST"])
def delete_quiz(quiz_id):
    if "admin" in session:
        quiz = Quizzes.query.filter_by(id = quiz_id).first()
        if not quiz:
            return redirect("/admin")
        if request.method == "POST":
            chapter_id = quiz.chapter_id
            db.session.delete(quiz)
            db.session.commit()
            return redirect(url_for("view_chapter" , chapter_id = chapter_id))
        return render_template("del_confirm.html" , quiz=quiz)
    else:
        return redirect("/login")
    

@app.route("/create_question/<int:quiz_id>" , methods = ["GET" , "POST"])
def create_question(quiz_id):
    if "admin" in session:
        if request.method == "POST" :
            question= request.form["question"]
            option1 = request.form["option1"]
            option2 = request.form["option2"]    
            option3 = request.form["option3"]
            option4 = request.form["option4"]
            correct_option = request.form["correct_option"]
            new_question = Questions(question = question , option1 = option1 , option2 = option2 , option3 = option3 , option4 = option4 , correct_option = correct_option , quiz_id = quiz_id)
            db.session.add(new_question)
            db.session.commit()
            flash ("Question created successfully!" , "success")
            return redirect(url_for("view_quiz" , quiz_id = quiz_id))
        else:
            return render_template("create_question.html" , quiz_id = quiz_id)
    else:
        return redirect("/login")
    
    

@app.route("/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    if "admin" not in session:
        return redirect("/login")

    question = Questions.query.get(question_id)

    if not question:
        flash("Question not found!", "danger")
        return redirect("/admin")

    if request.method == "POST":
        question_text = request.form["question"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_option = request.form["correct_option"]

        # Update question details
        question.question = question_text
        question.option1 = option1
        question.option2 = option2
        question.option3 = option3
        question.option4 = option4
        question.correct_option = correct_option

        db.session.commit()
        flash("Question updated successfully!", "success")

        return redirect(url_for("view_quiz", quiz_id=question.quiz_id))

    return render_template("edit_question.html", question=question)
  
    

@app.route("/delete_question/<int:question_id>" , methods = ["GET" , "POST"])
def delete_question(question_id):
    if "admin" in session:
        question = Questions.query.filter_by(id = question_id).first()
        if not question:
            return redirect("/admin")
        if request.method == "POST":
            quiz_id = question.quiz_id
            db.session.delete(question)
            db.session.commit()
            return redirect(url_for("view_quiz" , quiz_id = quiz_id))
        return render_template("del_confirm.html" , question=question)
    else:
        return redirect("/login")
    
# Creating user dashboard for showcasing all the quizzes.
@app.route("/user")
def user_dashboard():
    if "user" in session:
        quizzes = Quizzes.query.all()
        user = Users.query.filter_by(id = session["user"]).first()
        return render_template("user_dashboard.html" , quizzes = quizzes , user = user)
    else:
        return redirect("/login")
    
@app.route("/user_logout")
def user_logout():
    session.pop("user")
    return redirect("/login")

# Creating start quiz routes for a particular quiz

@app.route("/start_quiz/<int:quiz_id>")
def start_quiz(quiz_id):
    if "user" in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        quiz_date = quiz.date_of_quiz
        if quiz_date > date.today():
            flash("Quiz is not available yet!", "danger")
            return redirect("/user")
        if len(questions) == 0:
            flash("No questions found for this quiz!", "danger")
            return redirect("/user")
        session['timestamp'] = datetime.now().isoformat()
        return redirect("/quiz/" + str(quiz_id))
    return redirect("/login")

@app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
def quiz_page(quiz_id):
    if "user" in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        user = Users.query.filter_by(id=session['user']).first()
        return render_template('quiz.html', questions=questions , user=user , quiz=quiz)
    return redirect("/login")


from datetime import datetime
from flask import render_template, request, session, redirect

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    if 'user' in session:
        user = Users.query.filter_by(id=session['user']).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        score = 0
        total_score = len(questions)

        for question in questions:
            user_answer = request.form.get(str(question.id), "").strip()  
            correct_answer = str(question.correct_option).strip()

            if user_answer == correct_answer:
                score += 1  # Increase score if correct

        new_score = Scores(
            score=score,
            total_score=total_score,
            user_id=user.id,
            quiz_id=quiz_id,
            time_stamp=datetime.utcnow()
        )

        db.session.add(new_score)
        db.session.commit()

        return render_template('result.html', score=score, total_score=total_score, user=user )

    return redirect('/login')

# Creating user/history route to show all the previous attempted quizzes to the user
@app.route('/user/history')
def user_history():
    if 'user' in session:
        user = Users.query.filter_by(id=session['user']).first()
        scores = Scores.query.filter_by(user_id=user.id).all()
        return render_template('history.html' , scores = scores , user = user)
    return redirect('/login')

# Creating route for admin search for users , subjects , chapters and quizzes based on their names
@app.route('/admin/search' , methods = ["GET" , "POST"])
def admin_search():
    if 'admin' in session :
        if request.method == "GET" :
            search_query = request.args.get('search_query')
            users = Users.query.filter(Users.name.ilike('%' + search_query + '%')).all()
            subjects = Subjects.query.filter(Subjects.name.ilike('%' + search_query + '%')).all()
            chapters = Chapters.query.filter(Chapters.name.ilike('%' + search_query + '%')).all()
            quizzes = Quizzes.query.filter(Quizzes.name.ilike('%' + search_query + '%')).all()
            return render_template('admin_search.html', users=users, subjects=subjects, chapters=chapters, quizzes=quizzes)
    return redirect('/login')
            
    
# Creating route for admin summary to show no. Of quizzes in each subject in bargraph and showing subject wise user attempts in pie chart
@app.route('/admin/summary')
def admin_summary():
    if 'admin' in session :
        subjects = Subjects.query.all()
        chapters = Chapters.query.all()
        users = Users.query.all()
        img_1 = os.path.join(curr_dir , "static" , "imgs" , "imgs1.png")
        quizzes = 0
        quiz_count_dict = {}
        for subject in subjects:
            quiz_count_dict[subject.name] = 0
            chapters = Chapters.query.filter_by(subject_id=subject.id).all()
            for chapter in chapters:
                quiz_count_dict[subject.name] += len(Quizzes.query.filter_by(chapter_id=chapter.id).all())
        subject_names = [key for key in quiz_count_dict]
        quiz_count = quiz_count_dict.values()
        plt.figure(figsize=(6,4))
        sns.barplot(x=subject_names , y=quiz_count)
        plt.title("Quiz per subject")
        plt.xlabel("Subjects")
        plt.ylabel("No. of Quizzes")
        plt.tight_layout()
        plt.savefig(img_1 , format="png")

        img_2 = os.path.join(curr_dir , "static" , "imgs" , "imgs2.png")
        user_attempts_dict = {}
        for user in users:
            if user.name.lower() != "admin":
                user_attempts_dict[user.name] = 0
                scores = Scores.query.filter_by(user_id=user.id).all()
                for score in scores:
                    user_attempts_dict[user.name] += 1
        labels = user_attempts_dict.keys()
        sizes = user_attempts_dict.values()
        plt.figure(figsize=(6,4))
        plt.pie(sizes, labels=None, autopct='%1.1f%%',shadow=True , startangle=90 , pctdistance=0.85, labeldistance=1.25)
        plt.legend(labels, title="Users", loc="upper right", bbox_to_anchor=(1.2, 1))
        plt.title("User Attempts per subject")
        plt.savefig(img_2 , format="png")
        return render_template('admin_summary.html', img_1=img_1, img_2=img_2)


@app.route('/user/summary')
def user_summary():
    if 'user' in session:
        user = session['user']
        user = Users.query.get(user)
        user_name = user.name

        img_1 = os.path.join(curr_dir, "static", "imgs", "user_imgs1.png")
        img_2 = os.path.join(curr_dir, "static", "imgs", "user_imgs2.png")

        # Quiz Attempts per Subject (Bar Chart)
        quiz_attempts = {}
        subjects = Subjects.query.all()
        for subject in subjects:
            quiz_attempts[subject.name] = 0
            chapters = Chapters.query.filter_by(subject_id=subject.id).all()
            for chapter in chapters:
                quizzes = Quizzes.query.filter_by(chapter_id=chapter.id).all()
                for quiz in quizzes:
                    if Scores.query.filter_by(user=user, quiz_id=quiz.id).first():
                        quiz_attempts[subject.name] += 1

        # Plot Bar Chart
        plt.figure(figsize=(7, 4))
        sns.barplot(x=list(quiz_attempts.keys()), y=list(quiz_attempts.values()))
        plt.title(f"{user_name}'s Quiz Attempts per Subject")
        plt.xlabel("Subjects")
        plt.ylabel("Attempts")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(img_1, format="png")

        #  User Quiz Distribution (Pie Chart)
        total_attempts = sum(quiz_attempts.values())
        if total_attempts > 0:
            plt.figure(figsize=(7,4))
            plt.pie(quiz_attempts.values(),labels=quiz_attempts.keys(),autopct='%1.1f%%',shadow=True,startangle=90 ,pctdistance=0.85, labeldistance=1.2)
            plt.legend(quiz_attempts.keys(), title="Subjects", loc="center right", bbox_to_anchor=(-0.2, 0.5))
            plt.title(f"{user_name}'s Quiz Distribution")
            plt.savefig(img_2, format="png")
        else:
            img_2 = None  # No attempts → No pie chart

        return render_template('user_summary.html', user_name=user_name, img_1=img_1, img_2=img_2)
    else:
        return redirect('/login')  # Redirect if not logged in


if __name__ == "__main__":
    app.run(debug=True)