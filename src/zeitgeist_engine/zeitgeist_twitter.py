from zeitgeist_base import Data, DataProvider
import twitter

class TwitterData(Data):
	def __init__(self,tweet):
		self.uri = "http://explore.twitter.com/" + tweet.user.screen_name + "/status/" + str(tweet.id)
		self.name = tweet.user.name + ":\n" + tweet.text 
		self.timestamp = tweet.created_at_in_seconds
		self.icon = None
		Data.__init__(self, name=self.name, uri=self.uri,timestamp=self.timestamp, count=0, use="tweet", type="Twitter")
		
class TwitterSource(DataProvider):
	
	def __init__(self):
		DataProvider.__init__(self, uri="gzg/twitter", name="Twitter")
		self.username = ''
		self.password = ''
		self.comment = " tweets to Twitter"
		
	def get_icon_static(self,icon_size):
				loc = glob.glob(os.path.expanduser("~/.Zeitgeist/twitter.png"))
				self.icon = gtk.gdk.pixbuf_new_from_file_at_size(loc[0], -1, int(24))
		
	def get_items_uncached(self):
		try:
			self.api = twitter.Api(username=self.username, password=self.password)
			for status in self.api.GetUserTimeline(count = 500):
				yield TwitterData(status)
		except:
			pass
			
