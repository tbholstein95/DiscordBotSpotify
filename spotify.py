from . import module
import json
import requests
import base64
from datetime import datetime, timedelta, date
import discord

class Spotify(module.Module):

	def __init__(self, config):
		self.config = config
		self.user_id = self.config["spotify_user_id"]
		self.authorization_header = ""
		self.auth_token = ""
		self.client_id = self.config["client_id"]
		self.client_secret = self.config["client_secret"]
		self.redirect_uri = "http://localhost:8888/"
		self.message_object = []

	async def create_playlist(self, name):
		# Holds the information you want to put in your playlist upon creation.
		request_body = json.dumps({
			"name": name,
			"description": "Songs posted in Forte",
			"public": True
		})

		# Posting a new playlist with the information provided.
		query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
		post_playlist_response = requests.post(
			query,
			data=request_body,
			headers={
				"Content-Type": "application/json",
				"Authorization": "Bearer {}".format(self.data[0])
			}
		)
		response_json = json.loads(post_playlist_response.text)
		return post_playlist_response

	# Get authorization. This opens up a new website in your default redirect URI that you must put into the YAML
	# file to gain access to the tokens
	async def get_auth_code(self):
		grant_type = 'client_credentials'
		body_params = {'grant_type': grant_type}
		spotify_url = 'https://accounts.spotify.com/api/token'
		response = requests.post(spotify_url, data=body_params, auth=(self.client_id, self.client_secret))
		token_raw = json.loads(response.text)
		token = token_raw["access_token"]
		get_code = requests.get(
			'https://accounts.spotify.com/authorize?client_id=dc1854c4ab244db5a6903be5ff769af5'
			'&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8888%2F&scope=playlist-modify'
			'-public playlist-modify-private user-top-read playlist-read-private '
			'playlist-read-collaborative user-library-modify user-read-playback-position user-read-email '
			'user-library-read ugc-image-upload user-follow-modify user-modify-playback-state '
			'user-read-recently-played user-read-private user-follow-read user-read-playback-state '
			'user-read-currently-playing',
			headers={
				"Content-Type": "data",
				"Authorization": "Bearer {}".format(token)
			}
		)
		return get_code.url

	# Allows bot to access user's spotify account to make all the requests.
	async def get_tokens(self):
		auth_str = bytes('{}:{}'.format(self.client_id, self.client_secret), 'utf-8')
		b64authstring = base64.b64encode(auth_str).decode('utf-8')
		code_payload = {
			"grant_type": "authorization_code",
			# The code from the website created from get_auth_code
			"code": "AQBPD6e2dec104iNeG4RIyxPi3oxS4IVjm6FTm7QHSYEUME_x5EkhC9qPCHX4XAFHP0jgseAOt0kyP2VW6intQZ4xV5Louzlthczsd5NHLeBXhfYYuhJiUfTLXjAlj6OFvSZ35HqAKAGZ8cEm9MQXiBid7T8uocunlx2inwJtscO9DWzrN31xaWStIwdr5VOSpY",
			"redirect_uri": "{}".format(self.redirect_uri)
		}

		tokens = requests.post(
			'https://accounts.spotify.com/api/token',
			data=code_payload,
			headers={
				"Authorization": "Basic {}".format(b64authstring)
			}
		)
		response_data = json.loads(tokens.text)
		access_token = response_data["access_token"]
		refresh_token = response_data["refresh_token"]

		# authorization_header = {"Authorization": "Bearer {}".format(access_token)}
		self.auth_token = access_token
		self.data = [access_token, refresh_token]
		self.serialize()

	async def get_spotify_uri(self, song_name, artist, event):
		query = 'https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20'.format(
			song_name,
			artist
		)
		get_song_uri_response = requests.get(
			query,
			headers={
				"Content-Type": "application/json",
				"Authorization": "Bearer {}".format(self.data[0])
			}
		)
		response_json = get_song_uri_response.json()
		songs = response_json["tracks"]["items"]

		# use first song from search
		uri = songs[0]['uri']
		id = songs[0]['id']

		result = []
		result.append("This song's spotify URI is" + uri)

		query = 'https://api.spotify.com/v1/audio-features/'+ id
		response1 = requests.get(
			query,
			headers={
				"Content-Type": "application/json",
				"Authorization": "Bearer {}".format(self.data[0])
			}
		)
		response1_json = response1.json()
		track_info = json.dumps(response1_json)
		await event.reply(track_info)

	async def message(self, event):
		message = event.get_message()

		if message.is_command():
			command, args = message.get_command_song()
			if command == "spotifysonginfo":
				song = args[0]
				song = song.replace('_', ' ')
				artist = args[1]
				artist = artist.replace('_', ' ')
				if len(args) < 1 or len(args) > 3:
					await event.reply(".songinfo <song_title>,<song_artist> No spaces, only use underscores")
				else:
					await self.get_spotify_uri(song_name=song, artist=artist, event=event)

			if command == "authorizeaccess":
				await event.reply("https://accounts.spotify.com/authorize?client_id=dc1854c4ab244db5a6903be5ff769af5&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8888%2F&scope=playlist-modify-public")
				self.auth_token = await self.get_auth_code()
				await event.reply("Authorizing. Go to website and copy-paste code into spotify.py in field codepayload:code to get access token")
			if command == "authorizeuser":
				self.authorization_header = await self.get_tokens()
				await event.reply("Should be creating authorization_header.")

			return True

		else:
			messagecontent = message.get_content()
			if len(messagecontent) > 0:
				if "https://open.spotify.com/track/" in messagecontent:
					current_date = date.today()
					current_day_of_week = datetime.today().weekday()

					await self.create_weekly_playlist(current_date, current_day_of_week, event=event)


					await self.add_track_to_playlist(messagecontent, self.data[4], event=event)

	async def refresh_token_check(self, checkrequest, event):
		substring = "401"
		substring2 = "403"
		checking = json.loads(checkrequest.text)
		error_code = ''
		if "error" in checking:
			print(checking["error"], "error")
			error_code = str(checking["error"]['status'])

		if error_code == substring or error_code == substring2:
			print(error_code, "error_code")
			await event.reply("Lord have mercy my tokens have expired.")
			auth_str = bytes('{}:{}'.format(self.client_id, self.client_secret), 'utf-8')
			b64authstring = base64.b64encode(auth_str).decode('utf-8')
			code_payload = {
				"grant_type": "refresh_token",
				"refresh_token": "{}".format(self.data[1])
			}
			refresh_request = requests.post(
				url="https://accounts.spotify.com/api/token",
				data=code_payload,
				headers={
					"Authorization": "Basic {}".format(b64authstring)
				}
			)

			response_data = json.loads(refresh_request.text)
			access_token = response_data['access_token']
			self.data[0] = access_token
			return True
		else:
			return False

	async def add_track_to_playlist(self, message, playlistid, event):
		uri = message.split("/track/")[1].split("?")[0]
		# Adds track to playlist
		query = "https://api.spotify.com/v1/users/1210477844/playlists/{}/tracks?uris=spotify:track:".format(playlistid) + uri
		add_response = requests.post(
			query,
			headers={
				"Accept": "application/json",
				"Content-Type": "application/json",
				"Authorization": "Bearer {}".format(self.data[0])
			}
		)
		temp = await self.refresh_token_check(add_response, event=event)
		if temp:
			await self.add_track_to_playlist(message, playlistid, event)


	async def create_weekly_playlist(self, currentdate, currentdayofweek, event):
		message = event.get_message()

		# If it is Friday
		if currentdayofweek == 4:
			# If the playlist is already initialized for the channel
			if len(self.data) == 7:
				# If there already exists a playlist, but it is a week from now, post the playlist.
				if self.data[2] and currentdate == self.data[3]:
					await event.reply("Sandcaaat's Weekly Round-Up! \n {}".format(self.data[2]))
					# If this isn't the first time a playlist was created and pinned, it will unpin the last.
					if self.data[5]:
						test_channel = event.get_bot().raw().get_channel(id=self.data[6])
						msg = await test_channel.fetch_message(self.data[5])
						await discord.Message.unpin(msg)
				# If it is the week after creating the playlist, create a new one and update when the next
				# playlist should post
				if currentdate == self.data[3] or self.data[3] == 0:
					next_week = currentdate + timedelta(days=7)
					created_playlist = await self.create_playlist(
						"Forte Posts From {} ".format(currentdate))
					# Checks if there is an authentication issue, and if there is reauthenticates and retries
					# making a new playlist.
					temp = await self.refresh_token_check(created_playlist, event=event)
					if temp:
						refreshed_playlist = await self.create_weekly_playlist(currentdate, currentdayofweek, event)
						created_playlist = refreshed_playlist

					playlist_info = json.loads(created_playlist.text)
					spotify_link = playlist_info["external_urls"]["spotify"]
					self.data[2] = [spotify_link]
					self.data[3] = next_week
					self.data[4] = playlist_info["id"]

					# Post the new link to the channel
					playlist_message = await message.reply("{}".format(spotify_link))
					print(playlist_message, "playlist_message")
					message_id = playlist_message
					self.data[5] = message_id.id
					self.data[6] = message_id.channel.id
					self.message_object = message_id
					print(self.message_object, "message object")
					# Pin new playlist to channel
					pin = await discord.Message.pin(message_id)
			# If a playlist hasn't been made for the channel yet there will only be 2 self.data entries
			if len(self.data) < 7:
				next_week = currentdate + timedelta(days=7)
				created_playlist = await self.create_playlist(
					"Forte Posts From {} ".format(currentdate))
				# Check for an error creating the playlist.
				temp = await self.refresh_token_check(created_playlist, event=event)
				if temp:
					created_playlist = await self.create_playlist("Forte Posts From {} ".format(currentdate))
				playlist_info = json.loads(created_playlist.text)
				print(playlist_info, "playlist info")
				spotify_link = playlist_info["external_urls"]["spotify"]
				# Since this is the first time creating the playlist we need to append these to our list.
				self.data.append(spotify_link)
				self.data.append(next_week)
				self.data.append(playlist_info["id"])

				playlist_message = await message.send("{}".format(spotify_link))

				message_id = playlist_message

				self.data.append(message_id.id)
				self.data.append(message_id.channel.id)
				self.message_object = message_id

				pin = await discord.Message.pin(message_id)
