
from mayanna_engine.mayanna_datasink import datasink
import pango
import gc
import time
import gtk
import gobject
 
class MayannaWidget(gtk.HBox):
    
    def __init__(self):
        gtk.HBox.__init__(self,False,True)
        
        self.set_size_request(600,400)
        #self.fav.connect("reload",self.reload_fav)
        
        self.option_box = gtk.VBox(False)
        self.create_doc_btn = gtk.Button("Create New Document")
        self.create_doc_btn.connect("clicked",self._show_new_from_template_dialog)
        self.create_note_btn = gtk.Button("Create New Note")
        self.create_note_btn.connect("clicked",self._make_new_note)
        self.option_box.pack_start(self.create_doc_btn,False,False,5)
        self.option_box.pack_start(self.create_note_btn,False,False)
        
        
        '''
        Topics Buttons Box
        '''        
        self.vbox1 =  gtk.VBox(False)
        self.topicTable = gtk.HBox(False)
        self.topicBox =  gtk.VBox(False)
        self.pack_start(self.vbox1,False,False)
        
               
        '''
        Set up Topic buttons
        '''
        
        self.topicButtonBox = gtk.VBox(False)
        self.sidebarBox = gtk.VBox(False)
        
        self.frame1 = gtk.Frame(False)
        self.alignment1 = gtk.Alignment(0.5,0.5,1.0,1.0)
        
        self.sidebarBtnBox = gtk.VBox()
        
        
        self.sidebarBox.hide()#
        
        #self.vbox1.pack_start(self.favIconView,False,False)
        self.vbox1.pack_start(self.topicTable,True,True)
        self.topicTable.pack_start(self.topicBox,False,False,5)
        self.topicBox.pack_start(self.sidebarBox,True,True)
        '''
         Viewer to view Items
         '''
            
        self.viewBox = gtk.HBox(False,True)
        self.viewscroll = gtk.HBox()
        
        self.scrolled_window2 = gtk.ScrolledWindow()
        self.scrolled_window2.set_border_width(4)

        self.scrolled_window2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        self.scrolled_window2.add_with_viewport(self.viewBox)
        self.pack_start(self.scrolled_window2,True,True)        
        self.pack_start(self.option_box,False,False)
       
        self.results = []
        #self.vbox1.connect("focus-in-event",self.get_focus)
        self.date_dict={}
        self.backup_dict={}
        self.today=None
        self.filters=[]
        
        '''
        Filter Box
        '''
        
        self.frame2 = gtk.Frame(True)
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
        
        self.viewBox.show_all()
        self.frame2.add(self.voptionbox)
        
        
        self.date_dict = None
        self.filtered_items = datasink.get_items()
        datasink.connect("reload",self.reorganize)
        self.reorganize()
                   
    def filterout(self,widget):
        
        for w in self.viewBox.get_children():
            self.viewBox.remove(w)
            del w
        self.reorganize()
    
    def reorganize(self,x=None):
        
        time1= time.time()
           
        date_dict={}
        day = None
        list = []
        
        for i in datasink.get_items():
             if not day or  day != i.ctimestamp or not date_dict.__contains__(i.ctimestamp):
                list = []
                day = i.ctimestamp
                daybox =  DayBox(i.datestring,list,i.ctimestamp)
                daybox.list.append(i)
                date_dict[i.ctimestamp]= daybox
             else:
                daybox.list.append(i)
       
        for key in sorted(self.backup_dict.keys()):
           if not date_dict.__contains__(key):
               for w in self.viewBox.get_children():
                   if w.date==key:
                        self.viewBox.remove(w)
                        del w
                   #self.viewBox.remove()
        
        if not self.viewBox.get_children():
            for key in sorted(date_dict.keys()):
                print(key)
                self.viewBox.pack_start(date_dict.get(key),True,True)
                date_dict.get(key).view_items()
        else: 
            for key in sorted(date_dict.keys()):
                if not self.backup_dict or self.backup_dict.__contains__(key):
                        self.create_dayView(date_dict.get(key))
        
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
  
    def _make_new_note(self,x):
        launcher.launch_command("tomboy --new-note")
  
    def _show_new_from_template_dialog(self, x):        
        dlg = NewFromTemplateDialog(".","")
        dlg.show()

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
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
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
        self.use_cells = isinstance(self, gtk.CellLayout)
        
        self.icon_cell = gtk.CellRendererPixbuf()
        self.pack_start(self.icon_cell, expand=True)
        self.add_attribute(self.icon_cell, "pixbuf", 1)

        self.text_cell = gtk.CellRendererText()
        self.text_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        self.pack_start(self.text_cell, expand=True)
        self.add_attribute(self.text_cell, "markup", 0)

        self.connect("item-activated", self._open_item)
        self.connect("button-press-event", self._show_item_popup)
        self.connect("drag-data-get", self._item_drag_data_get)
        self.enable_model_drag_source(0, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
        self.store = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_PYOBJECT)   # 3: Visible
    
  
    
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
        
        name = item.get_name()
        comment = "<span size='small'>%s</span>" % item.get_comment()
        text = name + "\n"  + comment
        
        try:
            icon = item.get_icon(24)
        except (AssertionError, AttributeError):
            print("exception")
            icon = None
            
        self.store.append([text,icon,item])
        
        del icon,name,comment,text

