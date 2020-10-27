# GeorgeConstanzeBot's Spotify Module

## Description
This allows the GeorgeBot for Discord to save Spotify track links posted through out the week into a playlist.
At the beginning of the week a playlist is generated, pinned, and will be able to be added to by George.  Then, on Friday,
the bot will post the playlist for users to catch up on.  It uses the Discord.py package, but does not use Spotipy.

## Installing
Add this file to your modules of your bot.  Start a localserver at port :8888 or whatever you like.  Run .authorizeaccess.
Go to the link provided and copy the code, and add it to the "code" variable in the script (it is commented and labelled).
Then run .authorizeuser, which will authenticate the playlist owner.  From there George will manage everything else.  He will
self refresh if his Spotify token expires.

## Future Plans
Use Youtube's API to take the data from a song posted and find it on Spotify, and add that to the playlist for the week.


# Notes
This module is uploaded directly to github to show the program.  The module is mine, but is part of a collaboration on a bot and is not shown 
on the bot's repo yet.