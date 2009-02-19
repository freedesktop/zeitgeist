#!/usr/bin/env python

import clutter
import time
import datetime
import math
import sys
import os

from zeitgeist_engine.zeitgeist_datasink import datasink
from gtk_clutter import *
 
class Item():
    
    def __init__(self,data,index):
        self.data = data
        self.index = index
        pixbuf = data.get_icon(32)
        #self.texture = clutter.Texture(pixbuf)
        self.texture = Button(data.name)
        self.texture.set_opacity(255)
        #self.texture.set_text(data.get_name())
        self.behaviour = None
    
    
class UI():
    
    ELLIPSE_Y = 200 # The y position of the ellipse of images.
    ELLIPSE_HEIGHT = 600 # The distance from front to back when it's rotated 90 degrees.
    IMAGE_HEIGHT = 100
    angle_step = 30.0
    
    def __init__(self):
        self.day =  datetime.datetime.fromtimestamp(time.time()).strftime("%d %b %Y")
        self.day =  time.mktime(time.strptime(self.day, "%d %b %Y"))
        
        '''
        Variables
        '''
        
        self.items = []
        self.pitem = None
        self.front_item = None
        
        
        self.stage = clutter.stage_get_default() 
        self.timeline_rot = clutter.Timeline(120,60)
        
        self.timeline_moveup = None
        self.behaviour_scale = None
        self.behaviour_path = None
        self.behaviour_opacity = None
        
        self.set_up()
      
        self.stage.connect("key-press-event", clutter.main_quit)
        self.stage.show()
        
        
       # self.main()
        clutter.main()
        
    def set_up(self):
        
        self.stage.set_size(800,600)
        self.stage.set_color(clutter.color_parse("#00000000"))
        
      
        '''
        Show the stage:
        '''
        self.stage.show()

        self.timeline_rot.connect("completed",self.on_timeline_rotation_completed)
        '''
        Add an actor for each image:
        '''
        self.load_data();
        self.add_image_actors();
        #if 0 //TODO: What's this?
        #self.timeline_rot.set_loop(True);
        #endif
        '''
        Move them a bit to start with:
        '''
        
        
        if self.items:
            self.rotate_item_to_front(self.items[0]);
      
    def load_data(self):
        '''
        Clear any existing images
        '''
        self.items = []
        tmin = self.day 
        for d in datasink.get_items(self.day):
            item = Item(d,len(self.items))
            self.items.append(item)
        self.front_item = 0
        self.angle_step = 360.0/(len(self.items)+10)
          
    def add_image_actors(self):
        x = 0
        y = 0
        angle = 0.0
        
        counter = 0
        for p in self.items:
            print p
            actor = p.texture
            '''
            Add the actor to the stage:
            '''
            self.stage.add(actor)
    
            '''
            Set an initial position:
            '''
            
            actor.set_position(x, y)
            y += 10
        
            '''
            Allow the actor to emit events.  By default only the stage does this.
            '''
            actor.set_reactive(True)
        
            actor.connect("button-press-event",self.on_texture_button_press,p)
        
            alpha = clutter.Alpha(self.timeline_rot, clutter.sine_inc_func)
            
            tangle = 360.0 / len(self.items)
            
            p.behaviour = clutter.BehaviourEllipse(alpha, 390, self.ELLIPSE_Y,
                                                                            self.ELLIPSE_HEIGHT, self.ELLIPSE_HEIGHT,
                                                                            angle, angle + tangle)
        
            p.behaviour.set_angle_tilt(clutter.X_AXIS, -75.0)
            p.behaviour.apply(actor)
            actor.show()
            
            angle += self.angle_step
            counter += 1

    def on_texture_button_press(self,event,temp,item):
        if self.timeline_rot and self.timeline_rot.is_playing():
            print "on_texture_button_press(): ignoring."
            return False;

        print "on_texture_button_press(): handling."
        self.rotate_item_to_front(item);
        return True;
    
    def on_timeline_rotation_completed(self,ev):
        '''
         All the items have now been rotated so that the clicked item is at the
         front.  Now we transform just this one item gradually some more, and
         show the filename.
        '''
        pass
    
    def rotate_item_to_front(self,item):
        print "#################"
        pos = item.index
        if pos==len(self.items):
            return
        '''
        Stop the other timeline in case that is active at the same time:
        '''
        
        self.timeline_rot.stop()
        #Get the item's position in the list:
        
        
        pos_front = self.front_item
        # Calculate the end angle of the first item:
        angle_front = 180.0
        angle_start = (angle_front - self.angle_step * pos_front)% 360.0
        angle_end   = (angle_front) - (self.angle_step * pos);
        angle_diff = 0
        print "--------------"
        print self.front_item
        print angle_start
        print angle_end
        print "--------------"
        #Set the end angles:            
        if self.front_item != pos:
            
            for p in self.items:
              
                #Reset its size:
            
                angle_start = angle_start%360.0
                angle_end   = angle_end%360.0       
                
                p.behaviour.set_angle_start(angle_start);
                p.behaviour.set_angle_end(angle_end);  
                angle_diff = abs(angle_end - angle_start)%180
                angle_end   += self.angle_step
                angle_start += self.angle_step 
              
        
        self.timeline_rot.set_n_frames(int(angle_diff));

        # Remember what item will be at the front when this timeline finishes:
        self.front_item= pos;

        self.timeline_rot.start();
