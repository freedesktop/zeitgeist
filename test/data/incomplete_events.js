[
	{
		"timestamp" : 400,
		"interpretation" : "#AccessEvent",
		"manifestation" : "#UserActivity",
		"actor" : "Mistery",
		"subjects" : [
			{
				"uri" : "foo://bar",
				"interpretation" : "",
				"manifestation" : "Hi"
			},{
				"uri" : "http://meh",
				"mimetype" : "bs",
				"interpretation" : "",
				"manifestation" : "Something"
			}
		]
	},{
		"timestamp" : 500,
		"interpretation" : "#AccessEvent",
		"manifestation" : "#UserActivity",
		"actor" : "Void",
		"subjects" : [
			{
				"uri" : "file://baz0",
				"mimetype" : "text/x-python",
				"interpretation" : "",
				"manifestation" : ""
			},{
				"uri" : "file://baz1",
				"mimetype" : "text/x-python",
				"interpretation" : "a",
				"manifestation" : ""
			},{
				"uri" : "file://baz2",
				"mimetype" : "text/x-python",
				"interpretation" : "",
				"manifestation" : "b"
			}
		]
	},{
		"timestamp" : 600,
		"interpretation" : "#SendEvent",
		"manifestation" : "#UserActivity",
		"actor" : "Empty",
		"subjects" : [
			{
				"uri" : "sftp://quiz",
				"mimetype" : "text/x-sql",
				"interpretation" : "#Audio",
				"manifestation" : "something else"
			}
		]
	}
]
