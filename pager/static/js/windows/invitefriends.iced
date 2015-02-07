$ = require 'jquery'
_ = require 'underscore'
{observable, observableArray, computed} = require 'knockout'

{socket} = require 'socket'
{Window} = require './window'
{log} = require 'logger'
{fql, profile_image_src} = require 'sns/facebook'
{user} = require 'models'


class Invitefriends extends Window
  _template_name: 'invitefriends'

  constructor: ->
    super
    @keyword = observable ''
    @friends = observable null
    @filtered_friends = computed =>
      keyword = _.str.trim @keyword().toLowerCase()
      friends = @friends()
      if not friends? or keyword.length < 1
        return null
      [type, friends] = @friends()
      switch type
        when 'facebook'
          _.filter friends, (f) ->
            f.nickname.toLowerCase().indexOf(keyword) > -1
    me = {
      type: user.type(), user_id: user.id(), nickname: user.nickname()
      uid: user.facebook().userID, profile_image: user.profile_image()
      is_online: true
    }
    @selected = observableArray [me]

    @filtered_friends.extend throttle: 300

  show: (callback) ->
    await super defer()
    await @show_facebook_friends defer err
    callback? err

  show_touched_friends: ->
    socket.emit 'touched friends', (friends) =>
      @friends ['touched friends', friends]

  show_facebook_friends: (cb) ->
    # TODO Facebook User가 아닐 경우 비활성화
    await fql.friends user.facebook().accessToken, defer err, friends
    cb err if err?
    friends_uids = _.map friends, (f) -> String f.uid
    await socket.emit(
      'check facebook user registerd', friends_uids, defer registerd_friend_ids
    )
    # convert [{id, uid}] to set[uid]=id
    registerd_friends = {}
    online_friends = {}
    for [id, uid, is_online] in registerd_friend_ids
      registerd_friends[uid] = id
      online_friends[uid] = is_online
    @friends [
      'facebook',
      for f in friends
        {
          type: 'facebook', uid: f.uid, nickname: f.name
          user_id: registerd_friends[f.uid] ? null
          is_online: online_friends[f.uid] ? false
          profile_image: profile_image_src f.uid, 'square'
        }
    ]
    cb null

  select: (friend, event) =>
    if @selected.indexOf(friend) < 0
      if @selected().length < 5
        @selected.push friend
      else
        alert '최대 5명까지만 초대하실 수 있습니다.'
    else
      if friend.user_id is user.id()
        $(event.currentTarget).shake()
        return
      @selected.remove friend

  create_room: (o, event) =>
    selected = @selected()
    if selected.length < 2
      $('div', event.currentTarget).shake()
      return
    attendees = _.map selected, (u) -> {
      type: u.type, id: u.user_id, uid: u.uid,
      nickname: u.nickname, email: u.email
    }
    await socket.emit 'create room', attendees, defer err, room
    if err
      alert err
    else
      @room = room
      
    @back()

  back: ->
    location.hash = '#/rooms/'

module.exports = {Invitefriends}