
from mayanna_engine.mayanna_util import *
from mayanna_engine.mayanna_fav import FavoritesSource
from mayanna_engine.mayanna_datasink import datasink
from gettext import gettext as _
import pango
import gc
import time
import datetime

 

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
        self.pack_start(self.icon_cell, expand=True)
        self.add_attribute(self.icon_cell, "pixbuf", 1)

        self.text_cell = gtk.CellRendererText()
        self.text_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
        self.text_cell.set_property("yalign", 0.0)
        self.text_cell.set_property("xalign", 0.0)
        self.pack_start(self.text_cell, expand=True)
        self.add_attribute(self.text_cell, "markup", 0)
        
        self.text_cell.set_property("wrap-width", 100)
        
        self.items=[]
        self.connect("button-press-event", self._show_item_popup)
        self.connect("drag-data-get", self._item_drag_data_get)
        self.enable_model_drag_source(0, [("text/uri-list", 0, 100)],gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
    
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
                    #menu.connect("deactivate", self._deactivate_item_popup, view, old_selected)

                    pass #print " *** Showing item popup"
                    item.populate_popup(menu)
                    menu.popup(None, None, None, ev.button, ev.time)
                    return True
    
    def load_items(self, items, ondone_cb = None):
        # Create a store for our iconview and fill it with stock icons
        #del self.items
        self.store.clear()
        for item in items:
            self._set_item(item)
            del item
        self.set_model(self.store)
        
    def _set_item(self, item):
        

        name = item.get_name()
        comment = "<span size='small'>%s</span>" % item.get_comment()

       # Size based on number of visible items
        item_cnt = len(self.store)
        text = name + "\n"  + comment
        icon_size = 24

        try:
            icon = item.get_icon(icon_size)
            # Bound returned width to height * 2
            icon_width = min(icon.get_width(), icon.get_height() * 2)
        except (AssertionError, AttributeError):
            icon = None
            icon_width = 0

        # Update text, icon, and visibility
        iter =[text,icon,item]
        self.store.append(iter)
        
        # Return the icon width used for sizing other records
        del icon,name,comment,text

    def _open_item(self, view, path):
        model = self.get_model()
        model.get_value(model.get_iter(path), 2).open()
        del model
  
class MayannaWidget(gtk.HBox):
    
    def __init__(self):
        gtk.HBox.__init__(self,False,True)
        
        self.set_size_request(600,400)
        self.fav = FavoritesSource()
        self.favIconView = ItemIconView()
        self.favIconView.load_items(self.fav.get_items())
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
        
        self.label1 = gtk.Label("Favorites")
        self.sidebarBtnBox = gtk.VBox()
        
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_border_width(4)

        self.scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scrolled_window.add_with_viewport(self.favIconView)
        self.scrolled_window.show()
        
        self.sidebarBox.hide()#
        
        #self.vbox1.pack_start(self.favIconView,False,False)
        self.vbox1.pack_start(self.topicTable,True,True)
        self.topicTable.pack_start(self.topicBox,False,False,5)
        self.topicBox.pack_start(self.sidebarBox,True,True)
        self.sidebarBox.pack_start(self.frame1,True,True,5)

        
        #self.frame1.set_shadow_type(gtk.SHADOW_OUT)
        #self.sidebarBox.pack_start(gtk.Button("xxxxx"),True,True,5)
        self.frame1.set_label_align(0.5, 0.5)
        self.frame1.add(self.alignment1)
        self.frame1.set_label_widget(self.label1)
        self.alignment1.add(self.scrolled_window)
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
        
        self.docfilter = gtk.CheckMenuItem("    Documents")
        self.vidfilter = gtk.CheckMenuItem("    Videos")
        self.audfilter = gtk.CheckMenuItem("    Audio")
        self.picfilter = gtk.CheckMenuItem("    Pictures")
        self.voptionbox = gtk.VBox(False)
        self.voptionbox.pack_start( self.docfilter,False,False)
        self.voptionbox.pack_start( self.vidfilter,False,False)
        self.voptionbox.pack_start( self.audfilter,False,False)
        self.voptionbox.pack_start( self.picfilter,False,False)
        self.viewBox.show_all()
        self.frame2.add(self.voptionbox)
        
        
        self.date_dict = None
        datasink.connect("reload",self.reorganize)
        self.reorganize()
            
        
    def reorganize(self,x=None):
        self.viewBox.hide_all()
        print("reorganizing")
        
        self.today = datetime.date.today().strftime("%x")       
        date_dict={}
        day = None
        list = []
        
        items = datasink.get_items()
        items.sort(self.compare)
        items = sorted(items, self.compare_columns)
        
        for i in items:
             print(i.datestring)
             if not day or  day != i.ctimestamp or not date_dict.__contains__(i.ctimestamp):
                list = []
                day = i.ctimestamp
                daybox =  DayBox(i.datestring,list,i.date)
                daybox.list.append(i)
                date_dict[i.ctimestamp]= daybox
             else:
                daybox.list.append(i)
        
        for key in sorted(date_dict.keys()):
            if not self.backup_dict or self.backup_dict.__contains__(key):
                if not self.backup_dict or not self.compare_sameday(self.backup_dict.get(key),date_dict.get(key)):
                    self.create_dayView(date_dict,key)
        
        self.backup_dict = date_dict
        gc.collect() 
        
        self.viewBox.show_all()
     
    def compare_sameday(self,x,y):
        if x.label == y.label:
            if not x.time == self.today:
                x = len(x.list)
                y= len(y.list)
                if x == y:
                    return True
        return False
            
    def create_dayView(self,date_dict,key):
        d = date_dict.get(key) 
        
        #self.hbox.pack_start(vbox,True,True)
        
        for w in self.viewBox.get_children():
            try:
                x = w.get_children()
                date1 = x[0].get_text()
                date2 = d.date
                if date1 == date2:
                    self.viewBox.remove(w)
            except StandardError, e:
                print("EXCEPTION ",e)
          
        self.viewBox.pack_start(d,True,True)
        d.view_items()

    def compare(self,a, b):
        return cmp(a.timestamp, b.timestamp) # compare as integers

    def compare_columns(self,a, b):
        # sort on ascending index 0, descending index 2
        return cmp(a.timestamp, b.timestamp)

    def _make_new_note(self,x):
        launcher.launch_command("tomboy --new-note")
  
    def _show_new_from_template_dialog(self, x):        
        dlg = NewFromTemplateDialog(".","")
        dlg.show()

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
