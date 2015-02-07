$ = require 'jquery'
_ = require 'underscore'

fql = (query, access_token, callback) ->
  if _.isArray query
    queries = {}
    for q, i in query
      queries["query#{i}"] = q
    query = JSON.stringify queries
  args = q: query, access_token: access_token
  $.getJSON 'https://graph.facebook.com/fql', args, (data) ->
    callback null, data.data

fql.friends = (access_token, callback) ->
  fql('SELECT uid, name, email FROM user WHERE uid in (SELECT uid1 FROM friend WHERE uid2 = me())'
    access_token, callback
  )

PROFILE_IMAGE_TYPES = ['small', 'normal', 'large', 'square']
profile_image_src = (uid, type='small') ->
  "http://graph.facebook.com/#{uid}/picture?type=#{type}"

module.exports = {fql, profile_image_src}