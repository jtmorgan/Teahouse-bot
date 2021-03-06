#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  userinfo.py
#  
#  Copyright 2017 Tigraan <User:Tigraan>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
from utilities import api_call
import logging

def list_to_API_format(listin):
	'''Transforms a list of strings to the API input format.'''


def get_user_info(userlist,infotoget=['groups','editcount'],endpoint='https://en.wikipedia.org/w/api.php'):
	'''Query the API for user info.
	
	userlist is a list of strings, each string being a username.'''
	
	API_user_string = '|'.join(userlist)
	API_info_string = '|'.join(infotoget)
	
	params = {'action' : 'query',
			'list' : 'users',
			'ususers' : API_user_string,
			'usprop' : API_info_string,
			'format' : 'json',
			'formatversion' : 2,
			}
			
	rawoutput = api_call(endpoint,params)
	#Example :
	#{'batchcomplete': True,
	#'query': {'users': [{'invalid': True, 'name': '12.54.29.3'},
						 #{'editcount': 3529,
						  #'groups': ['extendedconfirmed',
									 #'*',
									 #'user',
									 #'autoconfirmed'],
						  #'name': 'Tigraan',
						  #'userid': 18899359},
						 #{'editcount': 13105,
						  #'groups': ['checkuser',
									 #'founder',
									 #'oversight',
									 #'sysop',
									 #'*',
									 #'user',
									 #'autoconfirmed'],
						  #'name': 'Jimbo Wales',
						  #'userid': 24},
						 #{'blockedby': 'Dougweller',
						  #'blockedbyid': 1304678,
						  #'blockedtimestamp': '2009-07-02T08:37:58Z',
						  #'blockexpiry': 'infinity',
						  #'blockid': 1505586,
						  #'blockreason': '[[WP:Spam|Spamming]] links to external '
										 #'sites: disguising links as news links, '
										 #'using multiple identities',
						  #'editcount': 2,
						  #'groups': ['*', 'user'],
						  #'name': 'Dananadan',
						  #'userid': 9977555},
						 #{'missing': True,
						  #'name': 'This username does not exist'}]}}
	
	# traverse the first two levels
	resultlist = rawoutput['query']['users']
	
	# we transform the result into a dictionary whose keys are the
	# usernames (it has to be done later anyways)
	
	resultdict = dict()
	for entry in resultlist:
		resultdict[entry['name']] = entry
	return resultdict
	
def get_block_info(userlist,endpoint='https://en.wikipedia.org/w/api.php'):
	'''Query the API for block info.
	
	userlist is a list of strings, each string being a username.
	This returns a dictionary such that dict[user] is True if the user
	currently (1) exists and (2) is blocked, False otherwise.'''
	user_string = '|'.join(userlist)
	
	params = {'action' : 'query',
			'list' : 'blocks',
			'bkusers' : user_string,
			'bkprop' : 'user',
			'format' : 'json',
			'formatversion' : 2,
			}
			
	rawoutput = api_call(endpoint,params)
	#Example: (https://en.wikipedia.org/w/api.php?action=query&list=blocks&bkusers=85.17.92.13|91.200.12.136|1.2.3.4&bkprop=user)
		#{
			#"batchcomplete": "",
			#"query": {
				#"blocks": [
					#{
						#"user": "91.200.12.136"
					#},
					#{
						#"user": "85.17.92.13"
					#}
				#]
			#}
		#}
	
	# traverse the first two levels
	resultlist = rawoutput['query']['blocks']
	
	# we transform the result into a dict of bool
	
	resultdict = dict()
	for user in userlist:
		resultdict[user] = ({'user':user} in resultlist)
	return resultdict

#TODO: make bot exclusion compliant
#Should be handled in the "posting notifications" part?
def isnotifiable(users):
	'''Check if specified users can be notified.
	
	The input is the list of usernames.
	The output is a dict of booleans (True = can be notified).
	
	This takes care of the policy aspect (who gets notified, in general)
	but NOT of the exclusion compliance, which must be handled elsewhere.
	For instance pywikibot's scripts should take care of it, per
	https://en.wikipedia.org/wiki/Template:Bots#Implementation'''
	
	# Get relevant info from API
	# Note: should get as little as needed...
	
	# Blocking info
	# Note: get_user_info cannot be used to check for blocks, because
	# https://www.mediawiki.org/wiki/API:Users fails to give any output
	# for IP editors. See also https://www.mediawiki.org/w/index.php?title=Topic:Tspl9p7oiyzzm19w
	
	isblocked = get_block_info(users)
	
	# Other general user information
	# WARNING! For IP editors, all we get is the 'invalid' key.
	# Do not rely on this to get (e.g.) the edit count of an IP editor!
	
	userinfo = get_user_info(users,infotoget=['groups'])
	
	
	is_notifiable = dict()
	for u in users:
		info = userinfo[u]
		
	###	 NOTIFICATION POLICY APPLIES HERE		###
	
		# By default, we should notify
		# Each exception will be logged
		is_notifiable[u] = True
		
		# If username does not exist (rename?) do not notify
		if 'missing' in info:
			is_notifiable[u] = False
			logging.warning('Username "{un}" does not seem to exist. No notification will be sent.'.format(un=u))
			
	
		# Do not notify currently-blocked users
		if isblocked[u]:
			is_notifiable[u] = False
			logging.warning('User "{un}" is blocked and will not be notified.'.format(un=u))
			
		#~ # Do not notify users with more than x edits
		#~ maxedits = 1000
		#~ if info['editcount']>maxedits:
			#~ is_notifiable[u] = False
			#~ logging.warning('User "{un}" performed more than {nedits} edits and will not be notified.'.format(un=u,nedits=maxedits))
			
		#~ # Do not notify users with the ECP flag
		#~ if 'extendedconfirmed' in info['groups']:
			#~ is_notifiable[u] = False
			#~ logging.warning('User "{un}" is extended confirmed and will not be notified.'.format(un=u))
			
		
		
	return is_notifiable
	


if __name__ == '__main__':
	from pprint import pprint
	# Jimbo Wales: an account with all user rights
	# Sandbox for user warnings: a user with expired blocks
	# Danadan / 12.54.29.3: two indeffed users
	# This username does not exist: a nonexistent user
	userlist = ['Jimbo Wales','Sandbox for user warnings','Dananadan','12.54.29.3','This username does not exist']
	#~ pprint(get_user_info(userlist))
	#~ pprint(get_block_info(userlist))
	pprint(isnotifiable(userlist))
	
