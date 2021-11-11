from tkinter import *
from tkinter import ttk
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk

import socket, threading, sys, traceback, os

import time

from RtpPacket import RtpPacket

import sys
# from time import time
import datetime

CACHE_FILE_NAME = "cache-"

CACHE_FILE_EXT = ".jpg"



class Client:

	INIT = 0

	READY = 1

	PLAYING = 2

	state = INIT

	

	SETUP = 0

	PLAY = 1

	PAUSE = 2

	TEARDOWN = 3

	FASTFORWARD = 4

	BACKWARD = 5

	SWITCH = 6

	DESCRIBE = 7

	total_frame = 0

	#=====================
	sum_size_packet = 0
	

	# Initiation..

	def __init__(self, master, serveraddr, serverport, rtpport, filename):

		self.master = master

		self.master.protocol("WM_DELETE_WINDOW", self.handler)

		self.createWidgets()

		self.serverAddr = serveraddr

		self.serverPort = int(serverport)

		self.rtpPort = int(rtpport)

		self.fileName = filename

		self.rtspSeq = 0

		self.sessionId = 0

		self.requestSent = -1

		self.teardownAcked = 0

		self.connectToServer()

		self.frameNbr = 0
		self.setupMovie()

		

	def createWidgets(self):
		"""Build GUI."""

		# Create Setup button

		self.setup = Button(self.master, width=20, padx=3, pady=3)

		self.setup["text"] = "Setup"

		self.setup["command"] = self.setupMovie

		self.setup.grid(row=2, column=0, padx=2, pady=2)

		

		# Create Play button		

		self.start = Button(self.master, width=20, padx=3, pady=3)

		self.start["text"] = "Play"

		self.start["command"] = self.playMovie

		self.start.grid(row=2, column=1, padx=2, pady=2)

		

		# Create Pause button			

		self.pause = Button(self.master, width=20, padx=3, pady=3)

		self.pause["text"] = "Pause"

		self.pause["command"] = self.pauseMovie

		self.pause.grid(row=2, column=2, padx=2, pady=2)

		

		# Create Teardown button

		self.teardown = Button(self.master, width=20, padx=3, pady=3)

		self.teardown["text"] = "Teardown"

		self.teardown["command"] =  self.exitClient

		self.teardown.grid(row=2, column=3, padx=2, pady=2)

		# Create Describe button
		self.Describe = Button(self.master, width=20, padx=3, pady=3)
		self.Describe["text"] = "Describe"
		self.Describe["command"] =  self.describe
		self.Describe.grid(row=3, column=0, padx=2, pady=2)

		# fast forward button 
		self.forward = Button(self.master, width=20, padx=3, pady=3)
		self.forward["text"] = "Forward"
		self.forward["command"] = self.fastForward
		self.forward.grid(row=3, column=2, padx=2, pady=2)

		# backward button 
		self.backward = Button(self.master, width=20, padx=3, pady=3)
		self.backward["text"] = "Backward"
		self.backward["command"] = self.fastBackward
		self.backward.grid(row=3, column=1, padx=2, pady=2)

		# Switch button
		self.switch = Button(self.master, width=20, padx=3, pady=3)
		self.switch["text"] = "switch"
		self.switch["command"] = self.switchMovie
		self.switch.grid(row=3, column=3, padx=2, pady=2)	


		# Label for remain and total time
		self.remainTimeLabel = Label(self.master, text="Remain time: ")
		self.remainTimeLabel.grid(row=1, column=1, padx=4, pady=0)
		self.totalTimeLabel = Label(self.master, text="Total time: ")
		self.totalTimeLabel.grid(row=1, column=2, padx=4, pady=0)
		

		# Create a label to display the movie

		self.label = Label(self.master, height=19)

		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=1, pady=1)

		# Combobox list Film

		self.listMovie = ttk.Combobox(self.master, width=10)
		self.listMovie['values'] = ('movie', 'movie1', 'movie2')
		self.listMovie.current(0) 
		self.listMovie.grid(row=0, column=3) 

	def setupMovie(self):

		"""Setup button handler."""

		if self.state == self.INIT:

			self.sendRtspRequest(self.SETUP)

	

	def exitClient(self):

		"""Teardown button handler."""

		self.sendRtspRequest(self.TEARDOWN)		

		self.master.destroy() # Close the gui window

		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video



	def pauseMovie(self):

		"""Pause button handler."""

		if self.state == self.PLAYING:

			self.sendRtspRequest(self.PAUSE)

	def describe(self):
		"""Describe."""
		# if self.state == self.PLAYING:
		self.sendRtspRequest(self.DESCRIBE)
		
		# self.master.destroy() # Close the gui window
		# os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video

	def playMovie(self):

		"""Play button handler."""

		if self.state == self.READY:

			# Create a new thread to listen for RTP packets

			threading.Thread(target=self.listenRtp).start()

			self.playEvent = threading.Event()

			self.playEvent.clear()

			self.sendRtspRequest(self.PLAY)
	
	def fastForward(self): 
		if self.state != self.INIT: 
			self.sendRtspRequest(self.FASTFORWARD)
	
	def fastBackward(self): 
		if self.state != self.INIT: 
			self.sendRtspRequest(self.BACKWARD)
	
	def switchMovie(self): 
		self.state == self.INIT 
		self.sendRtspRequest(self.SWITCH)


	def listenRtp(self):		

		"""Listen for RTP packets."""

		while True:

			try:
				data = self.rtpSocket.recv(20480)
				if data:
					print ("size = " + str (sys.getsizeof(data)) + "\n")
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					self.curr_rtpPck = rtpPacket
					currFrameNbr = rtpPacket.seqNum()
					self.total_frame = rtpPacket.seqNum()

					print("Current Seq Num: " + str(currFrameNbr))
					remainTime = int(currFrameNbr*0.04)	
					remainTime = time.strftime('%H:%M:%S', time.gmtime(remainTime))			
					self.remainTimeLabel.config(text="Remain time: "+remainTime)
					self.totalTimeLabel.config(text="Total time: "+time.strftime('%H:%M:%S', time.gmtime(self.total_time)))
					# if currFrameNbr > self.frameNbr: # Discard the late packet

					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.sum_size_packet += sys.getsizeof(data)
						print ("Current Seq Num in if: " + str(currFrameNbr))
						print ("dsize / dt = " + str(sys.getsizeof(data) / 0.05 / 1024) + " KB/s")
						#--------------------------------------------------------
						self.frameNbr = currFrameNbr
# 						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

					self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

			except:

				# Stop listening upon requesting PAUSE or TEARDOWN

				if self.playEvent.isSet(): 

					break

				

				# Upon receiving ACK for TEARDOWN request,

				# close the RTP socket

				if self.teardownAcked == 1:

					self.rtpSocket.shutdown(socket.SHUT_RDWR)

					self.rtpSocket.close()

					break

					

	def writeFrame(self, data):

		"""Write the received frame to a temp image file. Return the image file."""

		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT

		file = open(cachename, "wb")

		file.write(data)

		file.close()

		return cachename

	

	def updateMovie(self, imageFile):

		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo

		

	def connectToServer(self):

		"""Connect to the Server. Start a new RTSP/TCP session."""

		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:

			self.rtspSocket.connect((self.serverAddr, self.serverPort))

		except:

			tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)

	

	def sendRtspRequest(self, requestCode):

		"""Send RTSP request to the server."""

		

		# Setup request

		if requestCode == self.SETUP and self.state == self.INIT:

			threading.Thread(target=self.recvRtspReply).start()

			# Update RTSP sequence number.

			self.rtspSeq += 1

			

			# Write the RTSP request to be sent.

			# request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
			request = 'SETUP ' + self.listMovie.get() + '.Mjpeg' + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			

			# Keep track of the sent request.

			self.requestSent = self.SETUP 

		

		# Play request

		elif requestCode == self.PLAY and self.state == self.READY:

			self.rtspSeq += 1

			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.PLAY

		

		# Pause request

		elif requestCode == self.PAUSE and self.state == self.PLAYING:

			self.rtspSeq += 1

			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.PAUSE

			

		# Teardown request

		elif requestCode == self.TEARDOWN and not self.state == self.INIT:

			self.rtspSeq += 1

			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) 

			self.requestSent = self.TEARDOWN
		
		elif requestCode == self.FASTFORWARD: 
			self.rtspSeq += 1

			request = 'FASTFORWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.FASTFORWARD
		
		elif requestCode == self.BACKWARD: 
			self.rtspSeq += 1

			request = 'BACKWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			self.requestSent = self.BACKWARD
		
		elif requestCode == self.SWITCH: 
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = 'SWITCH ' + self.listMovie.get() + '.Mjpeg' + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			# Keep track of the sent request.
			self.requestSent = self.SWITCH
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)


		elif requestCode == self.DESCRIBE: 
			self.rtspSeq += 1
			request = 'DESCRIBE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.DESCRIBE
		else:

			return

		

		# Send the RTSP request using rtspSocket.

		self.rtspSocket.send(request.encode())

		

		print('\nData sent:\n' + request)

	

	def recvRtspReply(self):

		"""Receive RTSP reply from the server."""

		while True:

			reply = self.rtspSocket.recv(1024)

			if reply: 
				self.parseRtspReply(reply)

				#============================
				if self.requestSent == self.DESCRIBE:
					# print(self.curr_rtpPck)
					print ("describe: " + str(self.curr_rtpPck.seqNum()))
					print ("version: " + str(self.curr_rtpPck.version()))
					print ("PT: " + str(self.curr_rtpPck.payloadType()))
					print ("sequent number " + str(self.curr_rtpPck.seqNum()))
					# print ()

					timestamp = datetime.datetime.fromtimestamp(self.curr_rtpPck.timestamp())
					print ("Time: " + timestamp.strftime('%Y-%m-%d %H:%M:%S'))
					print ("SSRC: " + str(self.curr_rtpPck.getSSRC()))
     
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:

				self.rtspSocket.shutdown(socket.SHUT_RDWR)

				self.rtspSocket.close()

				break

	

	def parseRtspReply(self, data):

		"""Parse the RTSP reply from the server."""
		if str(type(data)).find("byte") == -1:
			data = data.encode()

		lines = data.decode().split('\n')
		seqNum = int(lines[1].split(' ')[1])

		

		# Process only if the server reply's sequence number is the same as the request's

		if seqNum == self.rtspSeq:

			session = int(lines[2].split(' ')[1])

			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:

				if int(lines[0].split(' ')[1]) == 200: 

					if self.requestSent == self.SETUP:

						# Update RTSP state.

						self.state = self.READY

						# Open RTP port.
						self.total_time = int(lines[-1].split(' ')[1])
						self.openRtpPort()

					elif self.requestSent == self.PLAY:

						self.state = self.PLAYING

					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						print ("Sum of frames " + lines[3] + "\n")
						# print (str(int(lines[3])/self.total_frame * 100) + " %")
						print ("Loss rate: " + str( 100.0 - float(lines[3])/self.total_frame * 100) + " %")
						print ("data rate average = " + str(self.sum_size_packet / (self.total_frame * 0.05) / 1024) + " KB/s")
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					
					elif self.requestSent == self.SWITCH:

						self.state = self.READY

						# The play thread exits. A new thread is created on resume.
						self.total_time = int(lines[-1].split(' ')[1])
						self.playEvent.set()
					
					elif self.requestSent == self.DESCRIBE:
						self.state = self.READY
						print ("Sum of frames " + lines[3] + "\n")
						# print (str(int(lines[3])/self.total_frame * 100) + " %")
						print ("Loss rate: " + str( 100.0 - float(lines[3])/self.total_frame * 100) + " %")
						print ("data rate average = " + str(self.sum_size_packet / (self.total_frame * 0.05) / 1024) + " KB/s")
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
						self.state = self.READY

					# 	# Open RTP port.
					# 	self.openRtpPort()

					# elif self.requestSent == self.PLAY:
					# 	self.state = self.PLAYING

					# elif self.requestSent == self.PAUSE:
					# 	self.state = self.READY
					# 	print ("Sum of frames " + lines[3] + "\n")
					# 	# print (str(int(lines[3])/self.total_frame * 100) + " %")
					# 	print ("Loss rate: " + str( 100.0 - float(lines[3])/self.total_frame * 100) + " %")
					# 	print ("data rate average = " + str(self.sum_size_packet / (self.total_frame * 0.05) / 1024) + " KB/s")
					# 	# The play thread exits. A new thread is created on resume.
					# 	self.playEvent.set()

					# elif self.requestSent == self.DESCRIBE:
					# 	self.state = self.READY
					# 	print ("Sum of frames " + lines[3] + "\n")
					# 	# print (str(int(lines[3])/self.total_frame * 100) + " %")
					# 	print ("Loss rate: " + str( 100.0 - float(lines[3])/self.total_frame * 100) + " %")
					# 	print ("data rate average = " + str(self.sum_size_packet / (self.total_frame * 0.05) / 1024) + " KB/s")
					# 	# The play thread exits. A new thread is created on resume.
					# 	self.playEvent.set()
      
      
					elif self.requestSent == self.TEARDOWN:

						self.state = self.INIT

						# Flag the teardownAcked to close the socket.

						self.teardownAcked = 1 
						print ("Sum of frames " + lines[3] + "\n")
						print ("Loss rate: " + str( 100.0 - float(lines[3])/self.total_frame * 100) + " %")
						print ("data rate average = " + str(self.sum_size_packet / (self.total_frame * 0.05) / 1024) + " KB/s")
      

	

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""

		# Create a new datagram socket to receive RTP packets from the server

		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec

		self.rtpSocket.settimeout(0.5)

		try:
			# Bind the socket to the address using the RTP port given by the client user

			self.rtpSocket.bind(("", self.rtpPort))

		except:
			# tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)
			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)



	def handler(self):

		"""Handler on explicitly closing the GUI window."""

		self.pauseMovie()

		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):

			self.exitClient()

		else: # When the user presses cancel, resume playing.

			self.playMovie()

