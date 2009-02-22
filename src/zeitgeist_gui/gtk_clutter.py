import math
import gobject
import pango
import clutter

class Stage (clutter.Stage):
    def __init__ (self):
        self.__gobject_init__ ()
        self.set_color (clutter.color_parse ('#000000ff'))

    def get_child (self):
        return self.get_children()[0]

    def add (self, actor):
        if self.get_children ():
            raise RuntimeError ("A Stage can only hold one child")
        clutter.Stage.add (self, actor)
        #actor.set_size (self.get_width () - 2, self.get_height () - 2)

class Box (clutter.Group):
    HORIZONTAL = 0
    VERTICAL = 1

    def __init__ (self, orientation, spacing=0):
        self.__gobject_init__ ()
        self.order = []
        self.orientation = orientation
        self.spacing = spacing

    def pack_end (self, actor):
        clutter.Group.add (self, actor)
        self.order.insert (0, actor)
        self._reallocate ()

    def pack_start (self, actor):
        clutter.Group.add (self, actor)
        self.order.append (actor)
        self._reallocate ()

    def _reallocate (self):
        n = len (self.order)
        x = 0
        y = 0
        eat = int (math.ceil (self.spacing * (n - 1) / float (n)))
        if self.orientation == self.HORIZONTAL:
            width = self.get_width () / n - eat
            height = self.get_height ()
            for child in self.order:
                child.set_position (x, y)
                #child.set_size (width, height)
                x += child.get_width () + self.spacing
        else:
            width = self.get_width ()
            height = self.get_height () / n - eat
            for child in self.order:
                child.set_position (x, y)
                #child.set_size (width, height)
                y += child.get_height () + self.spacing
            
    def set_size_static(self,width,height):
        n = len (self.order)
        x = 0
        y = 0
        eat = int (math.ceil (self.spacing * (n - 1) / float (n)))
        if self.orientation == self.HORIZONTAL:
            for child in self.order:
                child.set_position (x, y)
                child.set_size (width, height)
                x += child.get_width () + self.spacing
        else:
            for child in self.order:
                child.set_position (x, y)
                child.set_size (width, height)
                y += child.get_height () + self.spacing
    
class Label (clutter.Label):
    COLOR = clutter.color_parse ('#FFFFFFFF')

    def __init__ (self):
        self.__gobject_init__ ()
        self.set_color (self.COLOR)
        attr_list = pango.AttrList ()
        attr = pango.AttrWeight (pango.WEIGHT_BOLD)
        attr.end_index = -1
        attr_list.insert (attr)
        attr = pango.AttrSize (6*pango.SCALE)
        attr.end_index = -1
        attr_list.insert (attr)
        self.set_attributes (attr_list)

    def set_size(self,size):
        self.set_color (self.COLOR)
        attr_list = pango.AttrList ()
        attr = pango.AttrWeight (pango.WEIGHT_BOLD)
        attr.end_index = -1
        attr_list.insert (attr)
        attr = pango.AttrSize (size*pango.SCALE)
        attr.end_index = -1
        attr_list.insert (attr)
        self.set_attributes (attr_list)

class Button (clutter.Group):
    BORDER_WIDTH = 2
    BORDER_COLOR = clutter.color_parse ('#00000000')
    NORMAL_COLOR = clutter.color_parse ('#00000000')
    HOVER_COLOR = clutter.color_parse ('#00000000')
    CLICKED_COLOR = clutter.color_parse ('#FF0000')
   
    __gproperties__ = {
        'label': (gobject.TYPE_STRING, 'Label', "The button's label",
                  '', gobject.PARAM_READWRITE),
        'padding': (gobject.TYPE_INT, 'Padding', 'The padding of the button',
                    0, 100, 6, gobject.PARAM_READWRITE),
        'width': (gobject.TYPE_INT, 'Width', 'The width of the button',
                  0, 100000, 0, gobject.PARAM_READWRITE),
        'height': (gobject.TYPE_INT, 'Height', 'The height of the button',
                   0, 100000, 0, gobject.PARAM_READWRITE),
        }

    __gsignals__ = {
        'button-press-event': 'override',
        'button-release-event': 'override',
        'enter-event': 'override',
        'leave-event': 'override',
        'clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                    ()),
        }

    def __init__ (self, label=''):
        self.__gobject_init__ ()

        self.set_reactive (True)
        self.padding = 2
        self.label = label

        self.label_actor = Label ()
        self.label_actor.set_text (self.label)
        
        #self.set_color
        
        self.rectangle_actor = clutter.Rectangle ()
        self.rectangle_actor.set_color (self.NORMAL_COLOR)
        self.rectangle_actor.set_border_width (self.BORDER_WIDTH)
        self.rectangle_actor.set_border_color (self.BORDER_COLOR)
        
        #self.set_color (self.NORMAL_COLOR)
        
        self.label_actor.set_opacity(255)
        self.rectangle_actor.set_opacity(255)
        self.set_opacity(255)
        
        self.set_size (48, 48)

        self.add (self.rectangle_actor)
        self.add (self.label_actor)

    def get_min_width (self):
        return self.label_actor.get_width () + self.padding * 2

    def get_min_height (self):
        return self.label_actor.get_height () + self.padding * 2

    def _set_width (self, width):
        min_width = self.get_min_width ()
        if width > min_width:
            self.width = width
        else:
            self.width = min_width

    def _set_height (self, height):
        min_height = self.get_min_height ()
        if height > min_height:
            self.height = height
        else:
            self.height = min_height

    def set_size (self, width, height):
        self._set_width (width)
        self._set_height (height)
        self._repaint ()

    def set_width (self, width):
        self._set_width (width)
        self._repaint ()

    def set_height (self, height):
        self._set_height (height)
        self._repaint ()

    def _repaint (self):
        # Recalculate geometry
        self._set_width (self.width)
        self._set_height (self.height)
        l_width = self.label_actor.get_width ()
        l_height = self.label_actor.get_height ()
        self.label_actor.set_position (self.width/2-l_width/2, self.height/2-l_height/2)
        self.rectangle_actor.set_size (self.width, self.height)
        
        self.label_actor.set_opacity(255)
        self.rectangle_actor.set_opacity(255)

    def do_set_property(self, pspec, value):
        setattr (self, pspec.name, value)
        if pspec.name == 'label':
            self.label_actor.set_text (value)
            self._repaint ()
        elif pspec.name in ('padding', 'width', 'height'):
            self._repaint ()
        else:
            raise AttributeError, 'unknown property %s' % pspec.name

    def do_get_property(self, pspec):
        if pspec.name in ('label', 'padding', 'width', 'height'):
            return getattr (self, pspec.name)
        else:
            raise AttributeError, 'unknown property %s' % pspec.name

    def do_button_press_event (self, event):
        self.rectangle_actor.set_color (self.CLICKED_COLOR)

    def do_button_release_event (self, event):
        self.rectangle_actor.set_color (self.HOVER_COLOR)
        self.emit ('clicked')

    def do_enter_event (self, event):
        self.rectangle_actor.set_color (self.HOVER_COLOR)

    def do_leave_event (self, event):
        self.rectangle_actor.set_color (self.NORMAL_COLOR)


