from flask import Flask, render_template, redirect, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('f1db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():

    conn = get_db_connection()
    seasons = conn.execute('select * from seasons order by year').fetchall()
    conn.close()

    # return render_template('index.html', seasons = seasons)
    return render_template('bulma.html', seasons = seasons)

@app.route('/<int:year>')
def season(year):
    """
    TODO: validate year as it is user input
    """
    return redirect("/{year}/1".format(year = str(year)))

@app.route('/<int:year>/<int:race_round>')
def race(year, race_round):
    
    conn = get_db_connection()
    try:
        # This checking seems a tad excessive
        assert isinstance(year, int)
        q = 'select min(year), max(year) from seasons' 
        minmaxyear = conn.execute(q).fetchone()
        assert minmaxyear[0] <= year <= minmaxyear[1]

        assert isinstance(race_round, int)
        q = 'select min(round), max(round) from races where year = ?' 
        minmaxround = conn.execute(q, (str(year),)).fetchone()
        assert minmaxround[0] <= race_round <= minmaxround[1]
    except:
        conn.close()
        abort(404)

    # Get all previous races
    q = 'select raceId from races where year = ? and round < ?'
    races = conn.execute(q, (str(year),str(race_round))).fetchall()
    race_ids = [race['raceId'] for race in races]
    
    # Get info for this race
    q = 'select * from races where year = ? and round = ?'
    racefatze = conn.execute(q, (str(year),str(race_round))).fetchone()

    # Get info on all races of this season
    q = 'select round, name from races where year = ?'
    rounds = conn.execute(q, (str(year),)).fetchall()

    # Get all results from previous races
    q = """
        select *, constructors.url as curl from results
        inner join drivers on results.driverId=drivers.driverId
        inner join constructors on results.constructorId = constructors.constructorId
        where results.raceid in ({seq})
        """
    q = q.format(
            seq=','.join(['?']*len(race_ids)))
    results = conn.execute(q, race_ids)

    standings = {} 
    for result in results:
        driver_id = result['driverId']
        if driver_id in standings:
            # add up all points over the previous rounds
            standings[driver_id]['points'] = standings[driver_id]['points'] + result['points']
        else:
            # save the race result row as a dict
            standings[driver_id] = {k: result[k] for k in result.keys()}  
    # sort by points
    standings_sorted = sorted(
            list(standings.values()), 
            key=lambda x:x['points'], 
            reverse=True)

    conn.close()
    return render_template(
            'round.html', 
            year = year, 
            race = racefatze,
            race_round = race_round, 
            rounds = rounds,
            standings = standings_sorted)
