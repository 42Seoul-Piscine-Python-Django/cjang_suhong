import sys
import random
from django.utils.functional import Promise
import requests
import pickle
from django.conf import settings

class GameObject:
    def __init__(self, x = 0, y = 0):
        self.pos_x = x
        self.pos_y = y

    def x_position(self):
        return self.pos_x

    def y_position(self):
        return self.pos_y

    def position(self):
        return self.pos_x, self.pos_y

    def set_power(self, power = 0):
        self.power = power

    def add_power(self, inc = 1):
        self.power += inc

    def strength(self):
        return self.power

class Player(GameObject):

    def __init__(self, x = 0, y = 0):
        super().__init__(x, y)
        self.set_power()

    def load_data(self, cache):
        if cache == None:
            raise Player.PlayerClassError("loading Error in Class:Player < Game.py : no cache file")
        self.pos_x = cache['player_pos'][0]
        self.pos_y = cache['player_pos'][1]
        self.set_power(cache['strength'])

    def move(self, x_inc, y_inc):
        dest_pos_x = self.pos_x + x_inc
        dest_pos_y = self.pos_y + y_inc
        return dest_pos_x, dest_pos_y

    def percentage(self, monster_power):
        atk = 50 - int(monster_power * 10) + (self.strength() * 5)
        if atk < 1:
            atk = 1
        if atk > 90:
            atk = 90
        return atk

    def attack(self, monster_power):
        atk = self.percentage(monster_power)
        r_num = random.randrange(0, 100)
        if r_num < atk:
            return True
        return False

    @staticmethod
    class PlayerClassError(Exception):
        def __init__(self, str = 'Error in Class:Player < Game.py'):
            super().__init__(str)

class Movimon(GameObject):
    #영화 정보
    def __init__(self, id = "", power = 0):
        super().__init__()
        self.id = id
        self.set_power(power)

    # def movie_id(self):
    #     return self._info['id']

class World:

    def __init__(self, size_x = 10, size_y = 10):
        self.grid_x = size_x
        self.grid_y = size_y

    def load_data(self, cache):
        None

class Movie:

    def __init__(self):
        self.captured = []

    def load_data(self, cache):
        if cache == None:
            raise Movie.MovieClassError("loading Error in Class:Movie < Game.py : no cache file")
        self.captured = cache['captured']
        self.moviedex = cache['moviedex']

    def capture(self, id):
        self.captured.append(id)

    def get_random_movie(self):
        result = True
        while result:
            dup = self.captured
            id = random.choice(settings.MOVIES)
            dup.append(id)
            if len(dup) == len(set(dup)):
                result = False
            dup.remove(id)
        return id, self.moviedex[id]

    @staticmethod
    def get_movie(id = ''):
        params = { 'i':id, 'r':'json', 'apikey':"c94fad6" }
        URL = 'http://www.omdbapi.com/'
        response = requests.get(URL, params = params)
        if response.ok == False:
            raise Movie.MovieClassError("request Error in Class:Movie < Game.py")
        my_json = response.json()
        return my_json

    def load_default_settings(self, lst = settings.MOVIES):
        try:
            dic = {}
            for movie in lst:
                this_json = Movie.get_movie(movie)
                dic[movie] = this_json
            self.moviedex = dic
        except Movie.MovieClassError as e:
            print(e)

    @staticmethod
    class MovieClassError(Exception):
        def __init__(self, str = 'Error in Class:Movie < Game.py'):
            super().__init__(str)


class Game:

    def __init__(self, ball_count = 10):
        self.player = Player()
        self.world = World()
        self.movie = Movie()
        self.movie_balls = ball_count
        self.battle = False

    #////////////////
    #//data control//
    #////////////////

    def dump_data(self):
        return {
            'player_pos' : self.player.position(),
            'ball_count' : self.movie_balls,
            'strength' : self.player.strength(),
            'captured' : self.movie.captured,
            'moviedex' : self.movie.moviedex,
            'battle' : self.battle
        }

    def load_data(self, cache):
        try:
            if cache == None:
                raise Game.GameClassError("loading Error in Class:Game < Game.py : no cache file")
            self.player.load_data(cache)
            self.world.load_data(cache)
            self.movie.load_data(cache)
            self.movie_balls = cache['ball_count']
            self.battle = cache['battle']
        except Exception as e:
            print(e)

    #////////////////
    #/Player control/
    #////////////////

    def __move_player_Up(self):
        if self.player.y_position() >= self.world.grid_y - 1:
            return None
        return self.player.move(0, 1)
    def __move_player_Down(self):
        if self.player.y_position() <= 0:
            return None
        return self.player.move(0, -1)
    def __move_player_Right(self):
        if self.player.x_position() >= self.world.grid_x - 1:
            return None
        return self.player.move(1, 0)
    def __move_player_Left(self):
        if self.player.x_position() <= 0:
            return None
        return self.player.move(-1, 0)
    _player_move = {
        'Up'    :   __move_player_Down,
        'Down'  :   __move_player_Up,
        'Left'  :   __move_player_Left,
        'Right' :   __move_player_Right
    }

    def move_player(self, order):
        return (self._player_move[order](self))

    def get_strength(self):
        return self.player.strength()

    #////////////////
    #/////battle/////
    #////////////////

    def battle_start(self):
        self.battle = True

    def battle_end(self):
        self.battle = False

    def battle_status(self):
        return self.battle

    def player_Attack(self, m_id = None):
        if self.movie_balls <= 0:
            return None
        self.movie_balls -= 1
        if self.player.attack(float(self.movie.moviedex[m_id]['imdbRating'])) == True:
            self.movie.captured.append(m_id)
            self.player.add_power()
            #잡았을 때 분기
            return True
        else:
            #놓쳤을 때 분기
            return False

    #////////////////
    #//pickle_cache//
    #////////////////

    def dump_cache(self, _cache):
        try:
            with open('cache.pkl', 'wb') as cache:
                pickle.dump(_cache, cache)
        except Game.GameClassError as e:
            print (e)

    def load_cache(self):
        try:
            self.cache = {}
            with open('cache.pkl', 'rb') as cache:
                self.cache = pickle.load(cache)
            return self.cache
        except Game.GameClassError as e:
            print(e)

    @staticmethod
    class GameClassError(Exception):
        def __init__(self, str = 'Error in Class:Game < Game.py'):
            super().__init__(str)

# def main():
#     game = Game()
#     game.movie.load_default_settings()
#     print(game.movie.moviedex.items())

# if __name__ == "__main__":
#     main()
