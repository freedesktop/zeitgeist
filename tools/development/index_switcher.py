#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2011 Collabora Ltd.
#                  By Trever Fischer <trever.fischer@collabora.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from optparse import OptionParser
import sqlite3
import sys
import os
import json

parser = OptionParser()
parser.add_option("-d", dest="drop", help="Drop current indexes", default=False, action="store_true")
parser.add_option("-l", dest="load", help="Load indexes from file", metavar="FILE", default=None)
parser.add_option("-s", dest="save", help="Save current indexes to a file", metavar="FILE", default=None)

(options, args) = parser.parse_args()

if not (options.drop or options.load or options.save):
    print "You must specify one or more of -d, -l, or -s"
    sys.exit(1)

db = sqlite3.connect(os.path.expanduser("~/.local/share/zeitgeist/activity.sqlite"))
if options.save:
  indexes = db.cursor().execute("SELECT name,sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
  saveData = {}
  for idx in indexes:
    print "Saving %s"%(idx[0])
    tokens = idx[1].split()
    idxData = {}
    idxData['unique'] = False
    tokens.pop(0) # "CREATE"
    if tokens[0].upper() == "UNIQUE":
      idxData['unique'] = True
      tokens.pop(0) # "UNIQUE"
    tokens.pop(0) # "INDEX"
    if " ".join(tokens[0:2]).upper() == "IF NOT EXISTS":
      tokens.pop(0)
      tokens.pop(0)
      tokens.pop(0)
    idxName = tokens.pop(0)
    tokens.pop(0) # "ON"
    idxDescription = "".join(tokens)[0:-1].split("(") # Takes table(column,column,column), strips last parens, and splits into table,column,column,column
    idxData['table'] = idxDescription[0]
    idxData['columns'] = {}
    for c in "".join(idxDescription[1:]).split(","):
      columnData = {'sort':None,'collation':None}
      tokens = c.split()
      columnName = tokens.pop(0)
      if len(tokens) > 0:
        sort = tokens.pop(0) # COLLATE or ASC/DESC
        if sort.upper() == "COLLATE":
            columnData['collation'] = tokens.pop(0)
            if len(tokens) > 0:
              columnData['sort'] = tokens.pop(0)
        else:
            columnData['sort'] = sort
      idxData['columns'][columnName] = columnData
    saveData[idxName] = idxData
  if options.save == "-":
    f = sys.stdout
  else:
    f = open(options.save, "w")
  print json.dump(saveData, f, indent=2)
if options.drop:
  indexes = db.cursor().execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
  with db as c:
    for idx in indexes:
        print "Dropping index %s"%(idx[0])
        c.execute("DROP INDEX %s"%(idx[0]))

if options.load:
  data = json.load(open(options.load))
  loadSql = {}
  for idxName,idxData in data.iteritems():
    sql = ["CREATE"]
    if idxData['unique']:
      sql.append("UNIQUE")
    sql.append("INDEX")
    sql.append("'%s'"%idxName)
    sql.append("ON")
    idxSql = []
    for columnName, columnProps in idxData['columns'].iteritems():
      columnSql = [columnName]
      if columnProps['collation']:
        columnSql.append("COLLATE")
        columnSql.append(columnProps['collation'])
      if columnProps['sort']:
        columnSql.append(columnProps['sort'])
      idxSql.append(" ".join(columnSql))
    sql.append("%s(%s)"%(idxData['table'], ",".join(idxSql)))
    loadSql[idxName] = " ".join(sql)
  with db as c:
    for name,query in loadSql.iteritems():
      print "Creating index %s"%name
      c.execute(query)
