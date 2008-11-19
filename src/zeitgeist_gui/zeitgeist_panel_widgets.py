from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_engine.zeitgeist_util import launcher
import pango
import gc
import time
import gtk
import gobject
import datetime
 
class TimelineWidget(gtk.HBox):
    
    def __init__(self):
        gtk.HBox.__init__(self,False,True)
        
        self.set_size_request(600,400)
        
        '''
         Viewer to view Items
         '''
            
        self.viewBox = gtk.HBox(False,True)
        self.viewscroll = gtk.HBox()
        
        self.scrolled_window2 = gtk.ScrolledWindow()
        self.scrolled_window2.set_border_width(4)

        self.scrolled_window2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled_window2.add_with_viewport(self.viewBox)
        self.pack_start(self.scrolled_window2,True,True)   
       
        self.results = []
        #self.vbox1.connect("focus-in-event",self.get_focus)
        self.date_dict={}
        self.backup_dict={}
        self.today=None
        
        calendar.connect("month-changed",self.reorganizemonth)
        calendar.connect("day-selected-double-click",self.reorganizeday)
        calendar.connect("day-selected",self.reorganizemonth)
        self.calendardate=None
        self.date_dict = None
        datasink.connect("reload",self.reorganize)
        self.reorganize()
                   
    def reorganize(self,x=None):
        time1= time.time()
           
        date_dict={}
        day = None
        list = []
        
        date=calendar.get_date()
        min = [date[0] ,date[1]+1,1,0,0,0,0,0,0]
        max =  [date[0] ,date[1]+2,0,0,0,0,0,0,0]
        min = time.mktime(min)
        max= time.mktime(max)
        
        self.calendardate = min
        for w in self.viewBox.get_children():
                self.viewBox.remove(w)
                del w
        
        calendar.clear_marks()
        for i in datasink.get_items_by_time(min,max):
             if not day or  day != i.ctimestamp or not date_dict.__contains__(i.ctimestamp):
                list = []
                day = i.ctimestamp
                daybox =  DayBox(i.datestring,list,i.ctimestamp)
                daybox.list.append(i)
                date_dict[i.ctimestamp]= daybox
             else:
                daybox.list.append(i)
       
        for key in sorted(date_dict.keys()):
            self.viewBox.pack_start(date_dict.get(key),True,True)
            date_dict.get(key).view_items()
        
        self.backup_dict = date_dict
        time2= time.time()
        print("Time to reorganize: "+ str(time2 -time1))
        gc.collect()
    
            
    def reorganizeday(self,x=None):
        
        time1= time.time()
           
        date_dict={}
        day = None
        list = []
        
        
        date=calendar.get_date()
        min = [date[0] ,date[1]+1,date[2],0,0,0,0,0,0]
        max =  [date[0] ,date[1]+1,date[2]+1,0,0,0,0,0,0]
        min = time.mktime(min)
        max= time.mktime(max)

        
        if not self.calendardate or not self.calendardate == min:
            self.calendardate = min
            for w in self.viewBox.get_children():
                    self.viewBox.remove(w)
                    del w
            
            
            calendar.clear_marks()
            for i in datasink.get_items_by_time(min,max):
                 if not day or  day != i.ctimestamp or not date_dict.__contains__(i.ctimestamp):
                    list = []
                    day = i.ctimestamp
                    daybox =  DayBox(i.datestring,list,i.ctimestamp)
                    daybox.list.append(i)
                    date_dict[i.ctimestamp]= daybox
                 else:
                    daybox.list.append(i)
           
            for key in sorted(date_dict.keys()):
                self.viewBox.pack_start(date_dict.get(key),True,True)
                date_dict.get(key).view_items()
            
            self.backup_dict = date_dict
            time2= time.time()
            print("Time to reorganize: "+ str(time2 -time1))
            gc.collect()
    
    def reorganizemonth(self,x=None):
        time1= time.time()
           
        date_dict={}
        day = None
        list = []
        
        date=calendar.get_date()
        min = [date[0] ,date[1]+1,1,0,0,0,0,0,0]
        max =  [date[0] ,date[1]+2,0,0,0,0,0,0,0]
        min = time.mktime(min)
        max= time.mktime(max)
        
        if not self.calendardate or not self.calendardate == min:
            self.calendardate = min
            for w in self.viewBox.get_children():
                    self.viewBox.remove(w)
                    del w
            
            calendar.clear_marks()
            for i in datasink.get_items_by_time(min,max):
                 if not day or  day != i.ctimestamp or not date_dict.__contains__(i.ctimestamp):
                    list = []
                    day = i.ctimestamp
                    daybox =  DayBox(i.datestring,list,i.ctimestamp)
                    daybox.list.append(i)
                    date_dict[i.ctimestamp]= daybox
                 else:
                    daybox.list.append(i)
           
            for key in sorted(date_dict.keys()):
                self.viewBox.pack_start(date_dict.get(key),True,True)
                date_dict.get(key).view_items()
            
            self.backup_dict = date_dict
            time2= time.time()
            print("Time to reorganize: "+ str(time2 -time1))
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
        gtk.HBox.__init__(self)
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
        self.pack_start(self.frame2,True,True,5)
        
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
        self.label = gtk.Label("Frequently Used")
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
        min = [date[0] ,date[1]+1,0,0,0,0,0,0,0]
        max =  [date[0] ,date[1]+2,1,0,0,0,0,0,0]
        min = time.mktime(min)
        max= time.mktime(max)
        
        month =  datetime.datetime.fromtimestamp(max).strftime("%b")
        self.label.set_text("Frequently Used "+month)
        
        x = datasink.get_freq_items(min,max)
        self.iconview.load_items(x)
        
class BookmarksWidget(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.iconview = ItemIconView()
        self.label = gtk.Label("Bookmarks")
        self.label.set_padding(5, 5)     
        self.pack_start(self.label,False,False)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.iconview)
        self.pack_start(scroll,True,True)

class CheckBox(gtk.CheckButton):
    def __init__(self,source):
        gtk.CheckButton.__init__(self)
        self.source = source
        self.set_border_width(5)
        self.label = gtk.Label(source.name)
        self.img = gtk.Image()
        self.set_label(source.name)
        #img.set_from_pixbuf(source.get_icon(16))
        self.set_image(self.img)
        self.set_focus_on_click(False)
        self.connect("toggled",self.toggle_source)

    def toggle_source(self,widget):
        if self.get_active():
            self.source.set_active(True)
        else:
            self.source.set_active(False)
        
class DayBox(gtk.VBox):
    def __init__(self,label,list,date):
        gtk.VBox.__init__(self,False)
        self.date = date
        self.label = gtk.Label(label)   
        self.label.set_padding(5, 5)    
        
        list.sort(self.compare)
        list = sorted(list, self.compare_columns)
        self.list= list
        self.iconview = ItemIconView()    
        self.iconview.show_all()
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        scroll.set_shadow_type(gtk.SHADOW_OUT)
        scroll.show_all()
        
        scroll.add(self.iconview)
        
        self.pack_end(scroll,True,True)
        self.pack_end(self.label,False,False)
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
        
class ItemIconView(gtk.IconView):
    '''
    Icon view which displays Items in the style of the Nautilus horizontal mode,
    where icons are right aligned and each column is of a uniform width.  Also
    handles opening an item and displaying the item context menu.
    '''

    
    def __init__(self):
        gtk.IconView.__init__(self)
        
        self.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.store = gtk.ListStore(str, gtk.gdk.Pixbuf, gobject.TYPE_PYOBJECT)
        self.use_cells = isinstance(self, gtk.CellLayout)
        
        self.icon_cell = gtk.CellRendererPixbuf()
        self.icon_cell.set_property("yalign", 0.0)
        self.icon_cell.set_property("xalign", 0.0)
        self.pack_start(self.icon_cell, expand=False)
        self.add_attribute(self.icon_cell, "pixbuf", 1)

        self.text_cell = gtk.CellRendererText()
        self.text_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        self.text_cell.set_property("yalign", 0.0)
        self.text_cell.set_property("xalign", 0.0)
        self.pack_start(self.text_cell, expand=False)
        self.add_attribute(self.text_cell, "markup", 0)
        self.text_cell.set_property("wrap-width", 150)
     
        self.connect("item-activated", self._open_item)
        self.connect("button-press-event", self._show_item_popup)
        self.connect("drag-data-get", self._item_drag_data_get)
        self.enable_model_drag_source(0, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
  
        
    def _open_item(self, view, path):
        model = view.get_model()
        model.get_value(model.get_iter(path), 2).open()
        del model,view,path
        gc.collect()

    def _show_item_popup(self, view, ev):
        if ev.button == 3:
            path = view.get_path_at_pos(int(ev.x), int(ev.y))
            if path:
                model = view.get_model()
                item = model.get_value(model.get_iter(path), 2)
                if item:
                    old_selected = view.get_selected_items()

                    view.unselect_all()
                    view.select_path(path)

                    menu = gtk.Menu()
                    menu.attach_to_widget(view, None)

                    pass #print " *** Showing item popup"
                    item.populate_popup(menu)
                    menu.popup(None, None, None, ev.button, ev.time)
                    return True
        del ev,view

    def _item_drag_data_get(self, view, drag_context, selection_data, info, timestamp):
        # FIXME: Prefer ACTION_LINK if available
        if info == 100: # text/uri-list
            selected = view.get_selected_items()
            if not selected:
                return

            model = view.get_model()
            uris = []
            for path in selected:
                item = model.get_value(model.get_iter(path), 2)
                if not item:
                    continue
                uris.append(item.get_uri())

            pass #print " *** Dropping URIs:", uris
            selection_data.set_uris(uris)
            
    def load_items(self, items, ondone_cb = None):
        # Create a store for our iconview and fill it with stock icons
        self.store.clear()
        for item in items:
            self._set_item(item)
            del item
        self.set_model(self.store)
        del items
        gc.collect()
        
    def _set_item(self, item):
        
        name =item.get_name()
        comment = "<span size='small' color='red'>%s</span>" % item.get_comment() + "  <span size='small' color='blue'> %s </span>" % str(item.count)
        text = name + "\n"  + comment 
        
        try:
            icon = item.get_icon(24)
        except (AssertionError, AttributeError):
            print("exception")
            icon = None
            
        self.store.append([text,icon,item])
        
        del icon,name,comment,text


calendar = CalendarWidget()
timeline = TimelineWidget()