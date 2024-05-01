from flask_app import app, db, bcrypt
from sqlalchemy import and_, or_, case, func, text
from flask import redirect, url_for, render_template, request, Response
from flask_login import current_user, login_user, logout_user, login_required
from flask_app.models import load_user, User, Profile, Accounts, DepWithID, Transfers
from flask_app.utils import accgen, trpingen, accdis, withdepid
from datetime import datetime
import csv
from io import StringIO
@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("login_page"))
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    if prof.userType == "MANAGER":
        return redirect(url_for("manager_screen"))
    acc = Accounts.query.filter(Accounts.user_id==current_user.id).first()
    transactions = DepWithID.query.filter(and_(
        DepWithID.accno==acc.accno,
        DepWithID.approve=="CLOSE"
        )).order_by(DepWithID.id.desc()).limit(3).all()
    transfers = Transfers.query.filter(or_(
        Transfers.from_acc==acc.accno,
        Transfers.to_acc==acc.accno
        )).order_by(Transfers.posted.desc()).limit(3).all()
    if len(transactions) == 0 and len(transfers) == 0:
        return render_template("home.html", profile=prof, account=acc)
    elif len(transfers) == 0:
        return render_template("home.html", profile=prof, account=acc, trExists=True, transacts=transactions)
    elif len(transactions) == 0:
        return render_template("home.html", profile=prof, account=acc, tfExists=True, transfers=transfers)
    else:
        return render_template("home.html", profile=prof, account=acc, tfExists=True, trExists=True, transfers=transfers, transacts=transactions)
@app.route("/manager/", methods=["GET", "POST"])
def manager_screen():
    if not current_user.is_authenticated:
        return redirect(url_for("login_page"))
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    if prof.userType != "MANAGER":
        return redirect(url_for("index"))
    if request.method=="GET":
        return render_template("manager.html")
    trpid=request.form["trcode"]
    obj = DepWithID.query.filter(DepWithID.trid==trpid).first()
    if obj is None:
        return render_template("manager.html", error=True)
    else:
        holder = Accounts.query.filter(Accounts.accno==obj.accno).first()
        if obj.approve == "CLOSE":
            return render_template("manager.html", error=True)
        DepWithID.query.filter(DepWithID.trid==trpid).update({DepWithID.approve: "CLOSE", DepWithID.posted: datetime.now()},synchronize_session=False)
        if obj.tran_type == "DEPOSIT":
            Accounts.query.filter(Accounts.accno==obj.accno).update({Accounts.balance: holder.balance+obj.amt},synchronize_session=False)
        if obj.tran_type == "WITHDRAW":
            Accounts.query.filter(Accounts.accno==obj.accno).update({Accounts.balance: holder.balance-obj.amt},synchronize_session=False)
        db.session.commit()
        return render_template("manager.html", error=False)

@app.route("/login/", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html", error=False)
    user = load_user(request.form["username"])
    if user is None:
        return render_template("login.html", error=True)
    if not user.check_password(request.form["password"]):
        return render_template("login.html", error=True)

    login_user(user)
    return redirect(url_for('index'))

@app.route("/register/", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html", error=False);
    if int(request.form["age"]) < 18:
        return render_template("register.html", error_age=True)
    if request.form["password"] != request.form["conf_password"]:
        return render_template("register.html", error_pass=True)
    user = load_user(request.form["username"])
    if not user is None:
        return render_template("register.html", error_use=True)
    reguser = User(username = request.form["username"], password_hash=bcrypt.generate_password_hash(request.form["password"]).decode("utf-8"))
    profile = Profile(first=request.form["firstname"],last=request.form["lastname"],age=int(request.form["age"]),gender=request.form["gender"],pano=request.form["pano"], phone=int(request.form["phone"]), address=request.form["address"], user=reguser, userType="CUSTOMER")
    pin = trpingen()
    acc = accgen()
    account = Accounts(user=reguser, balance=0.0, accno=acc, trpin=pin, visual='false')
    db.session.add_all([reguser, profile, account])
    db.session.commit()
    login_user(reguser)
    return redirect(f"/trpin/{acc}")

@app.route("/trpin/<int:Number>/")
@login_required
def trpage(Number):
    status = Accounts.query.filter(Accounts.user_id==current_user.id).first()
    if status.visual=="false":
        Accounts.query.filter(Accounts.user_id==current_user.id).update({Accounts.visual: "true"}, synchronize_session=False)
        db.session.commit()
        return render_template('trpin.html', pin = status)
    else:
        return render_template('trerror.html')
@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/profile/")
@login_required
def profile_screen():
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    acc = Accounts.query.filter(Accounts.user_id==current_user.id).first()
    disaccno = accdis(str(acc.accno))
    ph = str(prof.phone)
    return render_template("profile.html", phone=ph, profile=prof, account=disaccno)

@app.route("/deposit/", methods=["GET", "POST"])
@login_required
def deposit_screen():
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    acc = Accounts.query.filter(Accounts.user_id==current_user.id).first()
    disaccno = accdis(str(acc.accno))
    if request.method=="GET":
        return render_template("deposit.html",profile=prof, account=disaccno)
    amount = float(request.form["amount"])
    depid=withdepid(amount)
    depgen=DepWithID(accno=acc.accno,trid=depid,amt=amount,tran_type="DEPOSIT",approve="OPEN",posted=datetime.now())
    db.session.add(depgen)
    db.session.commit()
    return render_template("deposit.html",profile=prof, account=disaccno, amt=amount, displayPin=True, pin=depid)

@app.route("/withdraw/", methods=["GET", "POST"])
@login_required
def withdraw_screen():
    acc = Accounts.query.filter(Accounts.user_id==current_user.id).first()
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    disaccno = accdis(str(acc.accno))
    if request.method == "GET":
        return render_template("withdraw.html",profile=prof, account=disaccno)
    tpin = int(request.form['trpin'])
    if acc.trpin != tpin:
        return render_template("withdraw.html",profile=prof, account=disaccno, trpin_error=True)
    amount = float(request.form["amount"])
    if acc.balance <= amount:
        return render_template("withdraw.html",profile=prof, account=disaccno, amt_error=True)
    depid=withdepid(amount)
    depgen=DepWithID(accno=acc.accno,trid=depid,amt=amount,tran_type="WITHDRAW",approve="OPEN",posted=datetime.now())
    db.session.add(depgen)
    db.session.commit()
    return render_template("withdraw.html",profile=prof, account=disaccno, amt=amount, displayPin=True, pin=depid)

@app.route("/transfer/", methods=["GET", "POST"])
@login_required
def transfer_screen():
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    acc = Accounts.query.filter(Accounts.user_id==current_user.id).first()
    disaccno = accdis(str(acc.accno))
    if request.method == "GET":
        return render_template("transfer.html", profile=prof, account=disaccno)
    tpin = int(request.form['trpin'])
    if acc.trpin != tpin:
        return render_template("transfer.html",profile=prof, account=disaccno, trpin_error=True)
    amount = float(request.form["amount"])
    if acc.balance <= amount:
        return render_template("transfer.html",profile=prof, account=disaccno, bal_error=True)
    rec_accno=int(request.form["receive"])
    rec_acc = Accounts.query.filter(Accounts.accno==rec_accno).first()
    if rec_acc is None:
        return render_template("transfer.html",profile=prof, account=disaccno, acc_error=True)
    Accounts.query.filter(Accounts.accno==rec_acc.accno).update({Accounts.balance: rec_acc.balance+amount},synchronize_session=False)
    Accounts.query.filter(Accounts.user_id==current_user.id).update({Accounts.balance: acc.balance-amount},synchronize_session=False)
    transfer = Transfers(from_acc=acc.accno, to_acc=rec_acc.accno, amt=amount, posted=datetime.now())
    db.session.add(transfer)
    db.session.commit()
    return render_template("transfer.html",profile=prof, account=disaccno, tr_success=True)

@app.route("/generate/", methods=["GET", "POST"])
@login_required
def generate_screen():
    prof = Profile.query.filter(Profile.user_id==current_user.id).first()
    if request.method=="GET":
        return render_template("generate.html", profile=prof)
    acc= Accounts.query.filter(Accounts.user_id==current_user.id).first()
    acno = acc.accno
    if request.form['start']=="" and request.form['end']=="":
        withdraw_query=DepWithID.query.filter(and_(DepWithID.accno==acno,DepWithID.tran_type=="WITHDRAW",DepWithID.approve=="CLOSE")).with_entities(
        DepWithID.tran_type,
        -DepWithID.amt,
        text("'SELF'"),
        DepWithID.posted)
        deposit_query=DepWithID.query.filter(and_(DepWithID.accno==acno,DepWithID.tran_type=="DEPOSIT",DepWithID.approve=="CLOSE")).with_entities(
        DepWithID.tran_type,
        DepWithID.amt,
        text("'SELF'"),
        DepWithID.posted)
        transfer_query=Transfers.query.filter(or_(Transfers.from_acc==acno, Transfers.to_acc==acno)).with_entities(
        text("'TRANSFER'"),
        case([
            (Transfers.from_acc==acno, -Transfers.amt),
            (Transfers.to_acc==acno, Transfers.amt),
            ]),
        case([
            (Transfers.from_acc==acno, Transfers.to_acc),
            (Transfers.to_acc==acno, Transfers.from_acc),
            ]),
        Transfers.posted
        )
        combined = withdraw_query.union_all(deposit_query, transfer_query).order_by(Transfers.posted)
        result = combined.order_by(Transfers.posted).all()
        csv_buffer=StringIO()
        csv_writer=csv.writer(csv_buffer)
        csv_writer.writerow(["TYPE OF TRANSACTION","AMOUNT","ACCOUNT NO.","DATE OF TRANSACTION"])
        for row in result:
            csv_writer.writerow(row)
        headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="combined_data.csv"'
        }
        return Response(
        csv_buffer.getvalue(),
        headers=headers,
        status=200
        )
    start = datetime.strptime(request.form['start'],'%Y-%m-%d')
    end = datetime.strptime(request.form['end'], '%Y-%m-%d')
    withdraw_query=DepWithID.query.filter(and_(DepWithID.accno==acno,DepWithID.tran_type=="WITHDRAW",DepWithID.approve=="CLOSE", func.date(DepWithID.posted)>=start, func.date(DepWithID.posted)<=end)).with_entities(
        DepWithID.tran_type,
        -DepWithID.amt,
        text("'SELF'"),
        DepWithID.posted)
    deposit_query=DepWithID.query.filter(and_(DepWithID.accno==acno,DepWithID.tran_type=="DEPOSIT",DepWithID.approve=="CLOSE", func.date(DepWithID.posted)>=start, func.date(DepWithID.posted)<=end)).with_entities(
        DepWithID.tran_type,
        DepWithID.amt,
        text("'SELF'"),
        DepWithID.posted)
    transfer_query=Transfers.query.filter(and_(or_(Transfers.from_acc==acno, Transfers.to_acc==acno),func.date(Transfers.posted)>=start, func.date(Transfers.posted)<=end)).with_entities(
        text("'TRANSFER'"),
        case([
            (Transfers.from_acc==acno, -Transfers.amt),
            (Transfers.to_acc==acno, Transfers.amt),
            ]),
        case([
            (Transfers.from_acc==acno, Transfers.to_acc),
            (Transfers.to_acc==acno, Transfers.from_acc),
            ]),
        Transfers.posted
        )
    combined = withdraw_query.union_all(deposit_query, transfer_query).order_by(Transfers.posted)
    result = combined.order_by(Transfers.posted).all()
    csv_buffer=StringIO()
    csv_writer=csv.writer(csv_buffer)
    csv_writer.writerow(["TYPE OF TRANSACTION","AMOUNT","ACCOUNT NO.","DATE OF TRANSACTION"])
    for row in result:
        csv_writer.writerow(row)
    headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="trhis.csv"'
    }
    return Response(
        csv_buffer.getvalue(),
        headers=headers,
        status=200
    )