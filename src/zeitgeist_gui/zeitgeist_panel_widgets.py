import datetime
import gc
import os
import time

import gtk
import gobject
import pango
from gettext import ngettext, gettext as _
 
from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_engine.zeitgeist_util import launcher

class TimelineWidget(gtk.HBox):
    
    # Constants
    DAY = 1
    WEEK = 2
    MONTH = 4

    def __init__(self):
        gtk.HBox.__init__(self, False, True)
        self.set_size_request(600, 400)
        
        # Create child scrolled window
        self.scrolledWindow = gtk.ScrolledWindow()
        self.scrolledWindow.set_border_width(4)
        self.scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(self.scrolledWindow, True, True)
        
        self.viewBox = gtk.HBox(False, True)
        self.scrolledWindow.add_with_viewport(self.viewBox)
        
        calendar.connect("month-changed", self.reorganize, self.MONTH)
        calendar.connect("day-selected-double-click", self.reorganize, self.DAY)
        calendar.connect("day-selected", self.reorganize, self.MONTH)
        
        datasink.connect("reload", self.reorganize)
        self.reorganize(self.DAY)
                   
    def reorganize(self, widget, range=None):
        time1 = time.time()
           
        dateDict = {}
        day = None
        list = []
        
        date = calendar.get_date()
        
        if range == self.DAY:
            min = [date[0], date[1]+1,date[2]+1,0,0,0,0,0,0]
            max = [date[0], date[1]+1,date[2]+2,0,0,0,0,0,0]
        else:
            min = [date[0], date[1]+1,1,0,0,0,0,0,0]
            max = [date[0], date[1]+2,0,0,0,0,0,0,0]
        min = time.mktime(min)
        max = time.mktime(max)
        
        for w in self.viewBox.get_children():
            self.viewBox.remove(w)
            del w
        
        calendar.clear_marks()
        
        for i in datasink.get_items_by_time(min, max):
             if not day or day != i.ctimestamp or not dateDict.__contains__(i.ctimestamp):
                list = []
                day = i.ctimestamp
                daybox =  DayBox(i.datestring, list,i.ctimestamp)
                daybox.list.append(i)
                dateDict[i.ctimestamp]= daybox
             else:
                daybox.list.append(i)
       
        for key in sorted(dateDict.keys()):
            self.viewBox.pack_start(dateDict.get(key), True, True)
            dateDict.get(key).view_items()
            
        time2 = time.time()
        print("Time to reorganize: " + str(time2 -time1))
        gc.collect()
            
    def create_dayView(self,d):
        for d2 in self.viewBox.get_children():
            try:
                x = d2.get_children()
                
                date1 = x[0].get_text()
                date2 = d.label.get_text()
                
                if date1 == date2:
                    if d.list != d2.list:
                        self.viewBox.remove(d2) 
                        del d2
                        if len(d.list):        
                            self.viewBox.pack_start(d,True,True)
                            d.view_items()
            except StandardError, e:
                print("EXCEPTION ",e)
  
class StarredWidget(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self,True)
        self.freqused = FrequentlyUsedWidget()
        self.bookmakrs = BookmarksWidget()
        
        self.pack_start(self.freqused,True,True,5)
        self.pack_start(self.bookmakrs,True,True,5)

class FilterAndOptionBox(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.option_box = gtk.VBox(False)
        self.create_doc_btn = gtk.Button("Create New Document")
        self.create_doc_btn.connect("clicked",self._show_new_from_template_dialog)
        self.create_note_btn = gtk.Button("Create New Note")
        self.create_note_btn.connect("clicked",self._make_new_note)
        self.option_box.pack_start(self.create_doc_btn,False,False,5)
        self.option_box.pack_start(self.create_note_btn,False,False)
        self.pack_start(self.option_box)
        
        self.filters=[]
        '''
        Filter Box
        '''
        self.frame2 = gtk.Frame()
        #self.alignment2 = gtk.Alignment(0.5,0.5,1.0,1.0)
        self.label2 = gtk.Label("Filter")
        self.frame2.set_label_align(0.5, 0.5)
        #self.frame2.add(self.alignment2)
        self.frame2.set_label_widget(self.label2)
        
        self.option_box.pack_start(self.frame2,False, False, 5)
        self.voptionbox = gtk.VBox(False)
        
        for source in datasink.sources:
            filter = CheckBox(source)
            filter.set_active(True)
            self.voptionbox.pack_start( filter,False,False,0)
            self.filters.append(filter)
            filter.connect("toggled",self.filterout)
        
        self.frame2.add(self.voptionbox)
        self.date_dict = None
        
    def _make_new_note(self,x):
        launcher.launch_command("tomboy --new-note")
  
    def _show_new_from_template_dialog(self, x):        
        dlg = NewFromTemplateDialog(".","")
        dlg.show()
        
    def filterout(self,widget):
        datasink.emit("reload")

class CalendarWidget(gtk.Calendar):
    def __init__(self):
        gtk.Calendar.__init__(self)
            
class FrequentlyUsedWidget(gtk.VBox):
    
    def __init__(self):
        gtk.VBox.__init__(self)
        self.iconview = ItemIconView()
        self.label = gtk.Label("Popular")
        self.label.set_padding(5, 5)    
        
        self.pack_start(self.label,False,False)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.iconview)
        self.pack_start(scroll,True,True)
        calendar.connect("month-changed",self.reload_view)
        datasink.connect("reload",self.reload_view)
        self.reload_view()
    def reload_view(self,x=None):
        
        date=calendar.get_date()
        min = [date[0] ,date[1]+1,1,0,0,0,0,0,0]
        max =  [date[0] ,date[1]+2,0,0,0,0,0,0,0]
        min = time.mktime(min)
        max= time.mktime(max)
        
        month =  datetime.datetime.fromtimestamp(max).strftime("%B")
        self.label.set_text("Popular in "+month)
        
        x = datasink.get_freq_items(min,max)
        self.iconview.load_items(x)
        
class BookmarksWidget(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.iconview = ItemIconView()
        self.label = gtk.Label("Bookmarks and Desktop")
        self.label.set_padding(5, 5)     
        self.pack_start(self.label,False,False)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.iconview)
        self.pack_start(scroll,True,True)
        items = datasink.get_desktop_items()
        self.iconview.load_items(items)

class CheckBox(gtk.CheckButton):
    def __init__(self,source):
        gtk.CheckButton.__init__(self)
        self.source = source
        self.set_border_width(5)
        self.label = gtk.Label(source.name)
        self.img = gtk.Image()
        
        #icon = source.icon

        #self.img.set_from_pixbuf(icon)
        
        self.set_label(source.name)
        #img.set_from_pixbuf(source.get_icon(16))
        self.img.set_from_icon_name(source.icon,4)
        self.set_image(self.img)
        self.set_focus_on_click(False)
        self.connect("toggled",self.toggle_source)

    def toggle_source(self,widget):
        if self.get_active():
            self.source.set_active(True)
        else:
            self.source.set_active(False)
        
class DayBox(gtk.VBox):
    
    def __init__(self, label, list, date):
        # Call constructor
        gtk.VBox.__init__(self, False)
        
        # Sort list
        list.sort(self.compare)
        list = sorted(list, self.compare_columns)
        
        # Set attributes
        self.list = list
        self.date = date
        
        # Create GUI
        self.label = gtk.Label(label)   
        self.label.set_padding(5, 5)  
        self.pack_start(self.label,False,False)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_OUT)
        self.pack_start(scroll,True,True)
        
        self.iconview = ItemIconView()
        scroll.add(self.iconview)
        
        #self.imageBox = gtk.HBox(True)
        #self.pack_start(self.imageBox)
        
        self.show_all()
    
    def view_items(self):
        self.iconview.load_items(self.list)

    def compare(self,a, b):
        return cmp(a.timestamp, b.timestamp) # compare as integers

    def compare_columns(self,a, b):
        # sort on ascending index 0, descending index 2
        return cmp(a.timestamp, b.timestamp)
      
class NewFromTemplateDialog(gtk.FileChooserDialog):
    '''
    Dialog to create a new document from a template
    '''
    __gsignals__ = {
        "response" : "override"
        }

    def __init__(self, name, source_uri):
        # Extract the template's file extension
        try:
            self.file_extension = name[name.rindex('.'):]
            name = name[:name.rindex('.')]
        except ValueError:
            self.file_extension = None
        self.source_uri = source_uri
        parent = gtk.Window()
        gtk.FileChooserDialog.__init__(self,
                                       _("New Document"),
                                       parent,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        self.set_current_name(name)
        self.set_current_folder(os.path.expanduser("~/Desktop"))
        self.set_do_overwrite_confirmation(True)
        self.set_default_response(gtk.RESPONSE_ACCEPT)

    def do_response(self, response):
        if response == gtk.RESPONSE_ACCEPT:
            file_uri = self.get_filename()

            # Create a new document from the template and display it
            try:
                if not self.source_uri:
                    # Create an empty file
                    f = open(file_uri, 'w')
                    f.close()
                else:
                    shutil.copyfile(self.source_uri, file_uri)
                launcher.launch_uri(file_uri)
            except IOError:
                pass

        self.destroy()
        
class ItemIconView(gtk.TreeView):
    '''
    Icon view which displays Items in the style of the Nautilus horizontal mode,
    where icons are right aligned and each column is of a uniform width.  Also
    handles opening an item and displaying the item context menu.
    '''

    
    def __init__(self):
        gtk.TreeView.__init__(self)
        
        #self.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.store = gtk.ListStore(str, gtk.gdk.Pixbuf,str,str, gobject.TYPE_PYOBJECT)
        #self.use_cells = isinstance(self, gtk.CellLayout)
        
        time_cell = gtk.CellRendererText()
        time_column = gtk.TreeViewColumn("Time",time_cell,markup=0)
        
        icon_cell = gtk.CellRendererPixbuf()
        icon_column = gtk.TreeViewColumn("Icon",icon_cell,pixbuf=1)
        
        name_cell = gtk.CellRendererText()
        name_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        name_cell.set_property("yalign", 0.0)
        name_cell.set_property("xalign", 0.0)
        name_cell.set_property("wrap-width", 200)
        name_column = gtk.TreeViewColumn("Name",name_cell,markup=2)
        
        count_cell = gtk.CellRendererText()
        count_column = gtk.TreeViewColumn("Count",count_cell,markup=3)
        
        self.append_column(time_column)
        self.append_column(icon_column)
        self.append_column(name_column)
        self.append_column(count_column)
     
        self.set_model(self.store)
        self.set_headers_visible(False)
        
        self.connect("row-activated", self._open_item)
        self.connect("button-press-event", self._show_item_popup)
        self.connect("drag-data-get", self._item_drag_data_get)
        self.connect("focus-out-event",self.unselect_all)
        self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
        self.last_item=None
        
    def unselect_all(self,x=None,y=None):
        try:
            treeselection = self.get_selection()
            model, iter = treeselection.get_selected()
            self.last_item = model.get_value(iter, 4)
            treeselection.unselect_all()
        except:
            pass
        
    def _open_item(self, view, path, x=None):        
        treeselection = self.get_selection()
        model, iter = treeselection.get_selected()
        item = model.get_value(iter, 4)
        item.open()
        del model,view,path
        gc.collect()

    def _show_item_popup(self, view, ev):
        if ev.button == 3:
               treeselection = self.get_selection()
               model, iter = treeselection.get_selected()
               item = model.get_value(iter, 4)
               if item:
                    menu = gtk.Menu()
                    menu.attach_to_widget(view, None)
                    item.populate_popup(menu)
                    menu.popup(None, None, None, ev.button, ev.time)
                    return True
                
        del ev,view

    def _item_drag_data_get(self, view, drag_context, selection_data, info, timestamp):
        # FIXME: Prefer ACTION_LINK if available
        if info == 100: # text/uri-list
            
            if self.last_item:
                uris = []
                uris.append(self.last_item.get_uri())
                selection_data.set_uris(uris)

            
    def load_items(self, items, ondone_cb = None):
        # Create a store for our iconview and fill it with stock icons
        self.store.clear()
        for item in items:
            self._set_item(item)
        self.set_model(self.store)
        gc.collect()
        
    def _set_item(self, item):
        name = item.get_name()
        comment = "<span size='small' color='red'>%s</span>" % item.get_comment() #+ "  <span size='small' color='blue'> %s </span>" % str(item.count)
        count = "<span size='small' color='blue'>%s</span>" %  item.count
        text = name +"\n" + comment
        try:
            icon = item.get_icon(24)
        except (AssertionError, AttributeError):
            print("exception")
            icon = None
        
        self.store.append([None, icon, text, None, item])
        
        del icon,name,comment
        


calendar = CalendarWidget()
timeline = TimelineWidget()
