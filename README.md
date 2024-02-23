Song Year: Guess The Year

A game where you're shown a YouTube video of a popular song and you must guess the year it was released.

Your score is calculated as the number of years "off" you were. If the year the song came out was 1956 and you guessed
1960, your score would be 4. If it came out in 2001 and you guessed 2000, your score would be 1. If the year was 1999
and you guess 1999, your score would be 0 - the best possible score.

You can guess as many times as you'd like, but only your first score is saved for each instance of the game. You will
have to get a new song started to continue updating your score. Also, once you've asked to reveal the year the song
came out (or guessed correctly), there will be nothing available to do except start a new song guess.

Your overall average score is tracked, and the 10 best scores (by registered user) are displayed on a leaderboard.

The final-project database has two tables: "users" and "songs". Users keeps track of the registered users playing the
game, and songs keeps track of the songs that are randomly offered for guessing. "users" keeps track of each user's
id, username, a hash of their password, their total score points so far, their total number of guesses so far, and
their average score (calculated with the previous two values). The average score is what's used to track the player's
progress, as well as the leaderboard.

The leaderboard displays users from lowest score to highest (since a low score is better).

The app.py section was the main one I worked on. Some of the queries were tricky, especially getting them to work
correctly within flask and the connection between python and the html files in the templates folder.

The update_stats() helper function does the average score calculation and updates the database. I kept getting
errors involving the way the query was written - especially involving the "WHERE" clause - but it eventually worked.

Another issue was getting some of the variables that app.py sent to index.html to return when the user submits a
POST request. Making some of these variables "global" fixed that, although I'm not sure if that's best practice.

Getting YouTube embedding to work correctly was also difficult, but I think it makes the web game much better to
see a video for the song on the same web page that you're playing on.

Originally, I wanted to query an API for the random song. I was going to use "musicbrainz". However, the layout of
that database and rules for querying it proved very difficult, so instead I found a list of 10,000 popular songs
and added them to the database in a "songs" table. That proved much simpler to query for a random song.

And finally, some of the jinja nested if statements got pretty complicated, and it became difficult to avoid errors
involving unnecessary brackets or nonsensical logic. It worked out nicely in the end.
