import datetime
import time
import math
import gc
import os
import time
import sys
import gtk
import gobject
import pango
from gettext import ngettext, gettext as _

from zeitgeist_gui.zeitgeist_util import launcher, gconf_bridge
from zeitgeist_gui.zeitgeist_util_widgets import *
from zeitgeist_shared.xdgdirs import xdg_directory
from zeitgeist_gui.zeitgeist_util import launcher, icon_factory
from zeitgeist_gui.zeitgeist_engine_wrapper import engine
from zeitgeist_shared.zeitgeist_shared import *

class CairoTimeline (gtk.DrawingArea):
	# TODO:
	# - Update self.week when the day changes
	# - Connect to the engine's signals and redraw when necessary
	# - Bling up the timeline
	# - Do something when the user clicks on a tag
	# - Add on more intelligent sizing logic (right now, tags overlap if they're too long)
	# - Clean up all of the drawing code.
	
	# Draw in response to an expose-event
	__gsignals__ = { "expose-event": "override" }
	
	def __init__ (self):
		gtk.DrawingArea.__init__(self)
		self.__init_week()
		self.__init_tags()
		
	def do_expose_event (self, event):
		# Create the cairo context
		ctx = self.window.cairo_create()
		
		# Restrict Cairo to the exposed area; avoid extra work
		ctx.rectangle(event.area.x, event.area.y,
			event.area.width, event.area.height)
		ctx.clip()
		
		self.__draw(ctx, *self.window.get_size())
	
	def __init_week (self):
		"""
		Initializes the self.week list which contains the name 
		(e.g. "Sunday"), start timestamp, and end timestamp for every
		day in the past week. (The list starts with the current day and
		goes backwards in time.)
		"""
		# Get an object representing the current day
		day = datetime.date.today()
		
		# Get the start and end timestamps for each day in the past week
		self.week = []
		for i in xrange(7):
			if len(self.week) == 0:
				name = "Today"
			elif len(self.week) == 1:
				name = "Yesterday"
			else:
				name = day.strftime("%A")
			start = time.mktime(day.timetuple())
			end = start + 86400 # number of seconds in 1 day
			self.week.append((name, start, end))
			
			day -= datetime.timedelta(days=1)
	
	def __init_tags (self):
		"""
		Initializes the self.tags list which contains the tags for the
		for the past week. (The list starts with a list of tags for the
		current day and goes backwards in time.)
		"""
		self.tags = []
		
		# Loop over every day in the past week and get it's most popular tags
		for (name, start, end) in self.week:
			tags = engine.get_most_used_tags(4, start, end)
			self.tags.append(tags)
		
	def __draw (self, ctx, width, height):
		# Create a pango layout
		layout = ctx.create_layout()
		
		# Fill the background with gray
		ctx.set_source_rgb(0.5, 0.5, 0.5)
		ctx.rectangle(0, 0, width, height)
		ctx.fill()		
		
		# Draw a line down the middle
		border = 20
		ctx.set_source_rgb(1.0, 1.0, 1.0)
		ctx.move_to(border, height - 30 - 6)
		ctx.line_to(width - border, height - 30 - 6)
		ctx.arc(width - border, height - 30, 12, -math.pi/2, math.pi/2)
		ctx.line_to(width - border, height - 30 + 6)
		ctx.line_to(border, height - 30 + 6)
		ctx.arc(border, height - 30, 12, math.pi/2, -math.pi/2)
		ctx.line_to(border, height - 30 - 6)
		ctx.fill()
		
		# Loop over each day in the past week, and draw tags for that day
		interval = (width - 2 * (border + 10)) / 7.0
		x = width - border - 7 - interval
		for i in xrange(7):
			# If this day has tags:
			if len(self.tags[i]) > 0:
				# Draw a line connecting the timeline to the tags
				ctx.set_source_rgb(0.2, 0.2, 0.2)
				ctx.move_to(x + (interval)/2.0, height - 30 - 6)
				ctx.line_to(x + (interval - 40)/2.0, height - 30 - 30)
				ctx.stroke()
				
				# Draw all of the tags for this day
				y = height - 30
				for tag in self.tags[i]:
					y -= 40
					ctx.set_source_rgb(0.2, 0.2, 0.2)
					ctx.rectangle(x, y, interval - 10, 20)
					ctx.fill()
					
					# Draw tag text
					ctx.set_source_rgb(1.0, 1.0, 1.0)
					font = pango.FontDescription()
					font.set_weight(20)
					layout.set_font_description(font)
					layout.set_text(tag)
					ctx.move_to(x + 3, y + 2)
					ctx.show_layout(layout)
				
				# Draw a line connecting the tags to one another
				ctx.set_source_rgb(0.2, 0.2, 0.2)	
				ctx.move_to(x + 1, height - 30 - 20)
				ctx.line_to(x + 1, y)
				ctx.stroke()
				
			# Draw this day's name on the timeline
			name = self.week[i][0]
			ctx.set_source_rgb(0.0, 0.0, 0.0)
			font = pango.FontDescription()
			font.set_weight(30)
			font.set_size(9 * pango.SCALE)
			layout.set_font_description(font)
			layout.set_text(name)
			ctx.move_to(x, height - 30 - 7)
			ctx.show_layout(layout)
				
			x -= interval


