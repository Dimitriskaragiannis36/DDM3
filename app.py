# ΑΝΔΡΟΥΤΣΟΠΟΥΛΟΣ ΜΙΧΑΗΛ 1115202200005
# ΚΑΡΑΓΙΑΝΝΗΣ ΔΗΜΗΤΡΙΟΣ 1115202200293
# ΣΤΙΒΑΚΤΑΚΗΣ ΑΝΤΩΝΙΟΣ 1115202200258

# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import sys, os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
import pymysql
from collections import defaultdict

def connection():
    ''' User this function to create your connections '''    
    con = pymysql.connect(host='127.0.0.1', port=3306, user='newuser', passwd='Mixalhs372002!', db='movies') #update with your settings
    return con

def updateRank(rank1, rank2, movieTitle):
    try:
        rank1 = float(rank1)
        rank2 = float(rank2)
        if rank1 < 0 or rank1 > 10 or rank2 < 0 or rank2 > 10:
            return [("status",), ("error",)]
    except ValueError:
        return [("status",), ("error",)]

    con = connection()
    cur = con.cursor()

    try:
        sql = "select rank from movie where title = %s"
        cur.execute(sql, (movieTitle,))
        results = cur.fetchall()

        if len(results) != 1:
            con.close()
            return [("status",), ("error",)]
        
        current_rank = results[0][0]

        if current_rank is None:
            newrank = (rank1 + rank2) / 2
        else:
            newrank = (rank1 + rank2 + current_rank) / 3

        sql_update = "update movie set rank = %s where title = %s"
        cur.execute(sql_update, (newrank, movieTitle))
        con.commit()
    except pymysql.Error:
        con.rollback()
        con.close()
        return [("status",), ("error",)]

    con.close()
    return [("status",), ("ok",)]

def colleaguesOfColleagues(actorId1, actorId2):
    con = connection()
    cur = con.cursor()

    # Smart single query based on the restrictions. Subqueries in WHERE are allowed.
    sql = """
    SELECT DISTINCT m.title, r1.actor_id, r2.actor_id, %s, %s
    FROM role r1, role r2, movie m
    WHERE r1.movie_id = r2.movie_id
      AND r1.movie_id = m.movie_id
      AND r1.actor_id != r2.actor_id
      AND r1.actor_id IN (
          SELECT rc.actor_id FROM role ra, role rc
          WHERE ra.movie_id = rc.movie_id AND ra.actor_id = %s AND rc.actor_id != %s
      )
      AND r2.actor_id IN (
          SELECT rd.actor_id FROM role rb, role rd
          WHERE rb.movie_id = rd.movie_id AND rb.actor_id = %s AND rd.actor_id != %s
      )
    """
    
    cur.execute(sql, (actorId1, actorId2, actorId1, actorId1, actorId2, actorId2))
    results = cur.fetchall()
    con.close()

    header = [("movieTitle", "colleagueOfActor1", "colleagueOfActor2", "actor1", "actor2")]
    return header + list(results)

def actorPairs(actorId):
    con = connection()
    cur = con.cursor()

    sql = """
    SELECT r.actor_id
    FROM role r, movie_has_genre mhg
    WHERE r.movie_id = mhg.movie_id AND r.actor_id != %s
    GROUP BY r.actor_id
    HAVING COUNT(DISTINCT mhg.genre_id) + (
        SELECT COUNT(DISTINCT mhg1.genre_id)
        FROM role r1, movie_has_genre mhg1
        WHERE r1.movie_id = mhg1.movie_id AND r1.actor_id = %s
    ) >= 7
    AND SUM(CASE WHEN mhg.genre_id IN (
        SELECT mhg2.genre_id
        FROM role r2, movie_has_genre mhg2
        WHERE r2.movie_id = mhg2.movie_id AND r2.actor_id = %s
    ) THEN 1 ELSE 0 END) = 0
    """
    
    cur.execute(sql, (actorId, actorId, actorId))
    results = cur.fetchall()
    con.close()

    return [("actorId",)] + [(row[0],) for row in results]

def selectTopNactors(n):
    n = int(n)
    con = connection()
    cur = con.cursor()

    sql = """
    SELECT g.genre_name, r.actor_id, COUNT(mhg.genre_id) as movie_count
    FROM movie_has_genre mhg, role r, genre g
    WHERE mhg.movie_id = r.movie_id AND g.genre_id = mhg.genre_id
    GROUP BY r.actor_id, mhg.genre_id, g.genre_name
    ORDER BY mhg.genre_id, COUNT(mhg.genre_id) DESC
    """
    cur.execute(sql)
    topactors = cur.fetchall()
    con.close()

    genre_counts = defaultdict(int)
    returnedlist = []

    for genre_name, actor_id, count in topactors:
        if genre_counts[genre_name] < n:
            returnedlist.append((genre_name, actor_id, count))
            genre_counts[genre_name] += 1

    return [("genreName", "actorId", "numberOfMovies")] + returnedlist

def traceActorInfluence(actorId):
    actorId = int(actorId)
    con = connection()
    cur = con.cursor()

    visited = set()
    queue = [actorId]
    influenced = set()

    while queue:
        current_actor = queue.pop(0)
        
        if current_actor in visited:
            continue
            
        visited.add(current_actor)

        # Βρίσκουμε τις επιρροές αυτού του ηθοποιού (b)
        sql = """
        SELECT DISTINCT r2.actor_id
        FROM role r1, role r2, movie m1, movie_has_genre mhg1,
             role r3, movie m2, movie_has_genre mhg2
        WHERE r1.movie_id = r2.movie_id
          AND r1.actor_id = %s
          AND r2.actor_id != r1.actor_id
          AND r1.movie_id = m1.movie_id
          AND r1.movie_id = mhg1.movie_id
          
          AND r3.actor_id = r2.actor_id
          AND r3.movie_id = m2.movie_id
          AND r3.movie_id = mhg2.movie_id
          
          AND mhg1.genre_id = mhg2.genre_id
          AND m2.year > m1.year
        """
        cur.execute(sql, (current_actor,))
        
        for (b_actor,) in cur.fetchall():
            if b_actor not in visited and b_actor not in queue:
                queue.append(b_actor)
                influenced.add(b_actor)

    con.close()
    
    return [("influencedActorId",)] + [(act_id,) for act_id in influenced]