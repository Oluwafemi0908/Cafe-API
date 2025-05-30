from flask import Flask, jsonify, render_template, request
from flask.cli import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
import random
import dotenv
import os
from flask_bootstrap import Bootstrap5


load_dotenv()
api_key = os.getenv("TopSecretAPIKey")
app = Flask(__name__)

# CREATE DB
class Base(DeclarativeBase):
    pass
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)
Bootstrap5(app)

# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name:getattr(self, column.name) for column in
                self.__table__.columns}


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")


# HTTP GET - Read Record
@app.route("/random")
def get_random_cafe():
    with app.app_context():
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        random_cafe = random.choice(cafes)
    return jsonify(cafe=random_cafe.to_dict())

@app.route("/all")
def get_all():
    with app.app_context():
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        all_cafes = [cafe.to_dict() for cafe in cafes]
    return jsonify(cafes=all_cafes)


@app.route("/search")
def search():
    query_location = request.args.get("loc")
    with app.app_context():
        cafes = db.session.execute(db.select(Cafe).where(
            Cafe.location==query_location)).scalars().all()
        matched_cafe = [cafe.to_dict() for cafe in cafes]
    if matched_cafe:
        return jsonify(cafes=matched_cafe)
    else:
        return jsonify(error={"Not Found": f"Sorry, we don't have a cafe at "
                                           f"{query_location}."}), 404
# HTTP POST - Create Record
@app.route("/add", methods=["GET", "POST"])
def add_cafe():
    new_cafe = Cafe(
        name = request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return  jsonify(response={"Success": (f"Successfully added "
                                              f"{request.form.get('name')}")})

# HTTP PUT/PATCH - Update Record
@app.route("/update_price/<cafe_id>", methods=["GET", "POST", "PATCH"])
def update_price(cafe_id):
    try:
        new_price = request.args.get("price")
        with app.app_context():
            cafe = db.session.execute(db.select(Cafe).where(
                Cafe.id==cafe_id)).scalar()
            cafe.coffee_price = new_price
            db.session.commit()
        return jsonify(response={"Success": f"Price updated "
                                            f"successfully."})
    except AttributeError:
        return jsonify(Error= {"Not Found": "No cafe with such id in the "
                                            "database"}), 404

# HTTP DELETE - Delete Record
@app.route('/report-closed/<cafe_id>', methods=["GET", "POST","DELETE"])
def report_closed(cafe_id):
    key = request.args.get('key')
    if key.strip() == api_key.strip():
        try:
            with app.app_context():
                cafe = db.session.execute(
                    db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
                db.session.delete(cafe)
                db.session.commit()
            return jsonify(response={"Success": f"Cafe Deleted "
                                                f"successfully."})
        except AttributeError:
            return jsonify(Error={"Not Found": "No cafe with such id in the "
                                               "database"}), 404


    else:
        return  jsonify(Error={"Wrong API key": "You are not allowed to "
                                                "delete this cafe info."})


if __name__ == '__main__':
    app.run(debug=True)
