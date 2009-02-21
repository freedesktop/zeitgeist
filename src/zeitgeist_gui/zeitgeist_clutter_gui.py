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
        self.hasFocus=False
        self.data = data
        self.index = index
        pb = data.get_icon(64)
        self.actor=None
        tex = clutter.Texture()
        if pb.props.has_alpha:
            bpp = 4
        else:
            bpp = 3 
        tex.set_from_rgb_data(
            pb.get_pixels(),
            pb.props.has_alpha,
            pb.props.width,
            pb.props.height,
            pb.props.rowstride,
            bpp, 0) 
        
        name=""
        for c in data.name:
            if len(name) < 15: 
                name = name +c
            else:
                break
            
        name = name + "..."
            
        
        self.btn = Button(name+"\n"+data.time)
        
        box = Box(Box.HORIZONTAL)
        box.pack_start(Box(Box.VERTICAL))
        box.pack_start(tex)
        box.pack_start(Box(Box.VERTICAL))
        
        self.texture = Box(Box.VERTICAL)#Button(data.name)
        self.texture.set_opacity(255)
        self.texture.pack_start(box)
        self.texture.pack_start(self.btn)
        
        self.behaviour = None
    
    def set_actor(self,actor):
        self.actor = actor
        
    def get_actor(self):
        return self.actor
    
    def set_opacity(self,o):
        self.texture.set_opacity(o)
        
    
class UI():
    
    ELLIPSE_Y = 200 # The y position of the ellipse of images.
    ELLIPSE_HEIGHT = 400 # The distance from front to back when it's rotated 90 degrees.
    IMAGE_HEIGHT =250
    angle_step = 0.0
    
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
        
        self.stage.set_size(800,500)
        self.stage.set_color(clutter.color_parse("#0f0f0f0f"))
        
      
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
        
        dayLabel = Label()
        txt = datetime.datetime.fromtimestamp(time.time()).strftime("%d %b %Y")
        dayLabel.set_text(txt)
        dayLabel.set_size(30)
        dayLabel.set_color (clutter.color_parse ('#747474'))
        
        
        
        
        group = clutter.Group()
        
        #self.set_color
        
        BORDER_COLOR = clutter.color_parse ('#a9a9a970')
        NORMAL_COLOR = clutter.color_parse ('#FFFFFFFF')
        rectangle_actor = clutter.Rectangle ()
        rectangle_actor.set_color (NORMAL_COLOR)
        rectangle_actor.set_border_width (2)
        rectangle_actor.set_border_color (BORDER_COLOR)
        
        #self.set_color (self.NORMAL_COLOR)
        
        dayLabel.set_opacity(255)
        rectangle_actor.set_opacity(255)
        group.set_opacity(255)
        
        rectangle_actor.set_size (800, 50)
        rectangle_actor.set_position(0,250)

        group.add (rectangle_actor)
        group.add (dayLabel)
        
        self.stage.add(group)
        dayLabel.set_position(50,250)
        
        
        BORDER_COLOR = clutter.color_parse ('#A9A9A979')
        NORMAL_COLOR = clutter.color_parse ('#0F0F0F0F')
        rectangle_actor2 = clutter.Rectangle ()
        rectangle_actor2.set_color (NORMAL_COLOR)
        rectangle_actor2.set_border_width (2)
        rectangle_actor2.set_border_color (BORDER_COLOR)        
        self.stage.add(rectangle_actor2)
        
        rectangle_actor2.set_size (500, 600)
        rectangle_actor2.set_position(600,0)
        
        if self.items:
            self.rotate_item_to_front(self.items[len(self.items)-1]);
      
    def load_data(self):
        '''
        Clear any existing images
        '''
        self.items = []
        tmin = self.day 
        tempitems = []
        
        for d in datasink.get_items(self.day):
            tempitems.append(d)
        
        #tempitems.reverse()
        
        for d in tempitems:
            item = Item(d,len(self.items))
            self.items.append(item)
          
        self.front_item = 0
        self.angle_step = 360.0/(len(self.items)*2)
        
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
            
            p.behaviour = clutter.BehaviourEllipse(alpha, 200, self.ELLIPSE_Y,
                                                                            600, self.ELLIPSE_HEIGHT,
                                                                            angle, angle + tangle)
        
            p.behaviour.set_angle_tilt(clutter.Y_AXIS, 45.0)
            p.behaviour.set_angle_tilt(clutter.X_AXIS, 180.0)
            p.behaviour.apply(actor)
            actor.show()
            p.set_actor(actor)
            
            angle += self.angle_step
            counter += 1

    def on_texture_button_press(self,event,temp,item):
        print event
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
        for item in self.items:
            if not item.index == self.front_item:
                item.btn.NORMAL_COLOR=clutter.color_parse ('#FFFFFFFF')
                item.btn.rectangle_actor.set_color (item.btn.NORMAL_COLOR)
                if item.hasFocus:
                    actor = item.get_actor()
                    x,y = actor.get_position()
                    #actor.set_scale(1/2,1/2)
                item.set_opacity(122)
                item.hasFocus=False
            else:
                item.btn.NORMAL_COLOR=clutter.color_parse ('#FFFF00')
                item.btn.rectangle_actor.set_color (item.btn.NORMAL_COLOR)
                actor = item.get_actor()
                x,y = actor.get_position()
                item.hasFocus=True
                actor.set_position(x+150, y)
                #actor.set_scale(2,2)
                item.set_opacity(255)
    
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
        angle_front = 90.0
        angle_start = (angle_front - self.angle_step * pos_front)% 360.0
        angle_end   = (angle_front) - (self.angle_step * pos);
        angle_diff = 0
        print "--------------"
        print pos
        print angle_start
        print angle_end
        #Set the end angles:            
        if self.front_item != pos:
            
            for p in self.items:
            
                if pos < self.front_item:
                    #Reset its size:
                
                    angle_start = angle_start%360.0
                    angle_end   = angle_end%360.0       
                    
                    p.behaviour.set_angle_start(angle_start);
                    p.behaviour.set_angle_end(angle_end);  
                    angle_diff = abs(angle_end - angle_start)%180
                    angle_end   += self.angle_step
                    angle_start += self.angle_step 
                  
                else:
                    angle_start = angle_start%360.0
                    angle_end   = angle_end%360.0       
                    
                    p.behaviour.set_angle_start(angle_end);
                    p.behaviour.set_angle_end(angle_start);  
                    angle_diff = abs(angle_end - angle_start)%180
                    angle_end   += self.angle_step
                    angle_start += self.angle_step 
                  
            
            if pos < self.front_item:
                self.timeline_rot.set_direction(clutter.TIMELINE_FORWARD)
                
            else:                  
                self.timeline_rot.set_direction(clutter.TIMELINE_BACKWARD)
                
            print(angle_diff)
            self.timeline_rot.set_n_frames(int(angle_diff));
            print angle_diff
            # Remember what item will be at the front when this timeline finishes:
            self.front_item= pos;
    
            self.timeline_rot.start();
