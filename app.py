from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

#from datetime import datetime
#from werkzeug.exceptions import BadRequest

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baza.db'

db = SQLAlchemy(app)


# --------------------- API ključ ----------------------- #

from dotenv import load_dotenv
import os

load_dotenv("api_kljuc.env")
API_KLJUC_OPENWEATHERMAP = os.environ.get("API_KLJUC_OPENWEATHERMAP")



# --------------------- TABELE BAZE ----------------------- #

class Drzava(db.Model):
    __tablename__ = 'Drzava'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    Naziv = db.Column(db.String(100), nullable=False)
    ISO2 = db.Column(db.String(2), nullable=False)
    Povrsina = db.Column(db.Integer)
    Broj_stanovnika = db.Column(db.Integer)
    Kontinent = db.Column(db.String(20), nullable=False)
    Valuta = db.Column(db.String(20), nullable=False)
    Jezici = db.Column(db.String(100), nullable=False)

    naselja = db.relationship('Naselje', backref='drzava', cascade='all, delete-orphan')


class Naselje(db.Model):
    __tablename__ = 'Naselje'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    Naziv = db.Column(db.String(100), nullable=False)
    Kategorija_naselja = db.Column(db.String, nullable=False)
    Zemljopisna_sirina = db.Column(db.Float)
    Zemljopisna_duzina = db.Column(db.Float)
    Povrsina = db.Column(db.Integer)
    Broj_stanovnika = db.Column(db.Integer)
    Poznate_osobe = db.Column(db.String(1000))
    Drzava_ID = db.Column(db.Integer, db.ForeignKey('Drzava.ID'), nullable=False)



# --------------------- HTML ----------------------- #

@app.route("/")
def pocetna():
    return render_template("index.html")



# --------------------- DRŽAVE ----------------------- #

@app.route('/drzave')
def drzave():
    lista_drzava = db.session.query(Drzava).order_by(Drzava.Naziv).all()
    return render_template('drzave.html', lista_drzava=lista_drzava)


@app.route('/drzava_obrazac/<int:drzava_id>', methods=['GET', 'POST'])
def drzava_obrazac(drzava_id):
    kontinenti = ["Afrika", "Antarktika", "Australija", "Azija", "Europa", "Južna Amerika", "Sjeverna Amerika"]
    if request.method == "GET":
        drzava = None
        if drzava_id != 0:
            drzava = db.session.query(Drzava).where(Drzava.ID == drzava_id).first()
        return render_template("drzava_obrazac.html", drzava=drzava, kontinenti=kontinenti)
    else:
        if drzava_id == 0:
            db.session.add(
                Drzava(
                    Naziv=request.form["naziv"],
                    ISO2=request.form["iso2"],
                    Povrsina=request.form["povrsina"],
                    Broj_stanovnika=request.form["broj_stanovnika"],
                    Kontinent=request.form["kontinent"],
                    Valuta=request.form["valuta"],
                    Jezici=request.form["jezici"]
                )
            )
        else:
            drzava = db.session.query(Drzava).where(Drzava.ID == drzava_id).first()
            if drzava:
                drzava.Naziv = request.form["naziv"]
                drzava.ISO2 = request.form["iso2"]
                drzava.Povrsina = request.form["povrsina"]
                drzava.Broj_stanovnika = request.form["broj_stanovnika"]
                drzava.Kontinent = request.form["kontinent"]
                drzava.Valuta = request.form["valuta"]
                drzava.Jezici = request.form["jezici"]
        db.session.commit()
        return redirect(app.url_for("drzave"))


@app.route('/drzava_brisi/<int:drzava_id>')
def drzava_brisi(drzava_id):
    drzava = db.session.query(Drzava).where(Drzava.ID == drzava_id).first()
    db.session.delete(drzava)
    db.session.commit()
    return redirect(app.url_for("drzave"))



# --------------------- NASELJA ----------------------- #

@app.route('/naselja')
def naselja():
    lista_naselja = db.session.query(Naselje).order_by(Naselje.Naziv).all()
    return render_template('naselja.html', lista_naselja=lista_naselja)


@app.route('/naselje_obrazac/<int:naselje_id>', methods=['GET', 'POST'])
def naselje_obrazac(naselje_id):
    if request.method == "GET":
        naselje = db.session.query(Naselje).where(Naselje.ID == naselje_id).first()
        dostupne_drzave = db.session.query(Drzava).order_by(Drzava.Naziv).all()
        return render_template("naselje_obrazac.html", naselje=naselje, dostupne_drzave=dostupne_drzave)
    else:
        naziv = request.form["naziv"]
        kategorija = request.form["kategorija"]
        povrsina = request.form["povrsina"]
        broj_stanovnika = request.form["broj_stanovnika"]
        poznate_osobe = request.form["osobe"]
        drzava_id = request.form["drzava_id"]

        drzava = db.session.query(Drzava).filter(Drzava.ID == drzava_id).first()
        if not drzava:
            return "Država nije pronađena", 400

        geo_url = f'https://api.openweathermap.org/geo/1.0/direct?q={naziv},{drzava.ISO2}&limit=1&appid={API_KLJUC_OPENWEATHERMAP}'
        response = requests.get(geo_url)
        koordinate = response.json()

        if koordinate and len(koordinate) > 0:
            zemljopisna_sirina = round(koordinate[0]["lat"], 5)
            zemljopisna_duzina = round(koordinate[0]["lon"], 5)
        else:
            #zemljopisna_sirina = None
            #zemljopisna_duzina = None
            return "Koordinate za uneseno naselje nisu pronađeni. Molimo pokušajte ponovno ili unesite drugačiji naziv.", 400

        if naselje_id == 0:
            naselje = Naselje(
                Naziv=naziv,
                Kategorija_naselja=kategorija,
                Zemljopisna_sirina=zemljopisna_sirina,
                Zemljopisna_duzina=zemljopisna_duzina,
                Povrsina=povrsina,
                Broj_stanovnika=broj_stanovnika,
                Poznate_osobe=poznate_osobe,
                Drzava_ID=drzava_id
            )
            db.session.add(naselje)
        else:
            naselje = db.session.query(Naselje).where(Naselje.ID == naselje_id).first()
            if naselje:
                naselje.Naziv = naziv
                naselje.Kategorija_naselja = kategorija
                naselje.Zemljopisna_sirina = zemljopisna_sirina
                naselje.Zemljopisna_duzina = zemljopisna_duzina
                naselje.Povrsina = povrsina
                naselje.Broj_stanovnika = broj_stanovnika
                naselje.Poznate_osobe = poznate_osobe
                naselje.Drzava_ID = drzava_id

        db.session.commit()
        return redirect(app.url_for("naselja"))


@app.route('/naselje_brisi/<int:naselje_id>')
def naselje_brisi(naselje_id):
    naselje = db.session.query(Naselje).where(Naselje.ID == naselje_id).first()
    db.session.delete(naselje)
    db.session.commit()
    return redirect(app.url_for("naselja"))



# --------------------- VRIJEME ----------------------- #
import requests

@app.route('/obrazac_vremena', methods=['GET', 'POST'])
def obrazac_vremena():
    drzave = Drzava.query.order_by(Drzava.Naziv).all()
    naselja = []
    odabrana_drzava_id = None
    odabrano_naselje_id = None

    if request.method == 'POST':
        odabrana_drzava_id = request.form.get('drzava')
        odabrano_naselje_id = request.form.get('naselje')
        action = request.form.get('action', '')

        if odabrana_drzava_id:
            odabrana_drzava_id = int(odabrana_drzava_id)
            naselja = Naselje.query.filter_by(Drzava_ID=odabrana_drzava_id).order_by(Naselje.Naziv).all()

            if odabrano_naselje_id:
                odabrano_naselje_id = int(odabrano_naselje_id)

                if action == "vremenska_prognoza":
                    return redirect(url_for('prikaz_vremena', naselje_id=odabrano_naselje_id, drzava_id=odabrana_drzava_id))
                elif action == "kvaliteta_zraka":
                    return redirect(url_for('kvaliteta_zraka', naselje_id=odabrano_naselje_id, drzava_id=odabrana_drzava_id))
                elif action == "informacije_naselja":
                    return redirect(url_for('informacije_naselja', naselje_id=odabrano_naselje_id, drzava_id=odabrana_drzava_id))

    return render_template('obrazac_vremena.html', drzave=drzave, naselja=naselja, odabrana_drzava_id=odabrana_drzava_id)


@app.route('/prikaz_vremena/<int:naselje_id>/<int:drzava_id>')
def prikaz_vremena(naselje_id, drzava_id):
    naselje = Naselje.query.filter_by(ID=naselje_id).first()
    drzava = Drzava.query.filter_by(ID=drzava_id).first()
    weather_data = None

    if naselje and drzava:
        geo_url = f'https://api.openweathermap.org/geo/1.0/direct?q={naselje.Naziv},{drzava.ISO2}&limit=1&appid={API_KLJUC_OPENWEATHERMAP}'
        geo_response = requests.get(geo_url)

        if geo_response.status_code == 200:
            geo_data = geo_response.json()
            if geo_data:
                latitude = geo_data[0]['lat']
                longitude = geo_data[0]['lon']

                weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KLJUC_OPENWEATHERMAP}&units=metric&lang=hr'
                weather_response = requests.get(weather_url)

                if weather_response.status_code == 200:
                    weather_data = weather_response.json()

    return render_template('prikaz_vremena.html', weather_data=weather_data, naselje=naselje, drzava=drzava)


@app.route('/kvaliteta_zraka/<int:naselje_id>/<int:drzava_id>')
def kvaliteta_zraka(naselje_id, drzava_id):
    naselje = Naselje.query.filter_by(ID=naselje_id).first()
    drzava = Drzava.query.filter_by(ID=drzava_id).first()
    weather_data = None

    if naselje and drzava:
        geo_url = f'https://api.openweathermap.org/geo/1.0/direct?q={naselje.Naziv},{drzava.ISO2}&limit=1&appid={API_KLJUC_OPENWEATHERMAP}'
        geo_response = requests.get(geo_url)

        if geo_response.status_code == 200:
            geo_data = geo_response.json()
            if geo_data:
                latitude = geo_data[0]['lat']
                longitude = geo_data[0]['lon']

                weather_url = f'https://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={API_KLJUC_OPENWEATHERMAP}&units=metric&lang=hr'
                weather_response = requests.get(weather_url)

                if weather_response.status_code == 200:
                    weather_data = weather_response.json()

    return render_template('kvaliteta_zraka.html', weather_data=weather_data, naselje=naselje, drzava=drzava)


@app.route('/informacije_naselja/<int:naselje_id>/<int:drzava_id>')
def informacije_naselja(naselje_id, drzava_id):
    naselje = Naselje.query.filter_by(ID=naselje_id).first()
    drzava = Drzava.query.filter_by(ID=drzava_id).first()

    return render_template('informacije_naselja.html', naselje=naselje, drzava=drzava)



# --------------------- API ----------------------- #

@app.route('/api')
def api():
    return render_template('api.html')


# --------------------- MAIN ----------------------- #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)