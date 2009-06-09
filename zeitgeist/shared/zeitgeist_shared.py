# -.- encoding: utf-8 -.-

sig_plain_data = "(isssssssbsss)"

def plainify_dict(item_list):
	return (
		item_list["timestamp"],
		item_list["uri"],
		item_list["text"],
		item_list["source"],
		item_list["content"],
		item_list["mimetype"], 
		item_list["tags"],
		item_list["use"],
		item_list["bookmark"] if "bookmark" in item_list else False,
		item_list["icon"],
		item_list["app"],
		item_list["origin"],
		)

def dictify_data(item_list):
    return {
		"timestamp": item_list[0],
		"uri": item_list[1],
		"text": item_list[2],
		"source": item_list[3],
		"content": item_list[4],
		"mimetype": item_list[5],
		"tags": item_list[6],
		"use": item_list[7],
		"bookmark": item_list[8],
		"icon": item_list[9],
		"app": item_list[10],
		"origin": item_list[11]
		}

def resolve_dot_desktop(path):
	attr = ["Name=",
		    "Comment=",
		    "GenericName=",
		    "Exec=",
		    "Type=",
		    "Icon=",
		    "MimeType="
		    "Categories="]
	f = open(path)
	data  = {}
	
	i = 0
	for line in f.readlines():
		if line.startswith(attr[i]):
			data[attr[i][0:len(attr[i])-1].lower()] = line[len(attr[i]):len(line)-1]
			i += 1
			
	return data