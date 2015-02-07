_ = require 'underscore'
{computed, observable, observablePresist, observableArray} = require 'knockout'

config = require 'config'
{log} = require 'logger'
{profile_image_src} = require 'sns/facebook'

class User
  constructor: ->
    @id = observablePresist null, key: 'user.id'
    @nickname = observablePresist null, key: 'user.nickname'
    @email = observablePresist null, key: 'user.email'
    @type = observablePresist null, key: 'user.type'
    @facebook_account = observablePresist null, key: 'user.facebook_account'
    @facebook = observablePresist null, key: 'user.facebook'
    @connected = observablePresist no, key: 'user.connected'
    @profile_image = observablePresist null, key: 'user.profile_image'
    @last_note_color = observablePresist(
      config.default_message_color, key: 'user.last_note_color'
    )
    @previous_location = observablePresist(
      '#/rooms/', key: 'user.previous_location'
    )

  connect: (type, id, nickname, email, facebook_account) ->
    @type type
    @id id
    @nickname nickname
    @email email
    if type is 'facebook'
      @facebook_account facebook_account
      @profile_image profile_image_src facebook_account.uid
    else
      @facebook_account null
    @connected yes

  disconnect: =>
    @id null
    @nickname null
    @type null
    @facebook null
    @facebook_account null
    @connected no

  connect_facebook: (response) =>
    type = @type()
    connected = @connected()
    if not connected or type is 'facebook'
      if response?.status isnt 'connected'
        @disconnect()
      else
        @facebook response.authResponse 

user = new User

class Notification
  constructor: ->

class NoteNotification
  constructor: (note) ->
    _.extend @, note

  open: (o, event) ->
    location.href = "#/rooms/#{@chat_room_id}"
    @close event.currentTarget

notifications = observableArray []
_.extend notifications, {
  add_note: (note) ->
    noti = new NoteNotification note
    noti.close = (element) ->
      noti.on_close = yes
      $(element)
        .one('webkitAnimationEnd', (e) ->
          notifications.remove noti
        ).css('-webkit-animation-name', 'notification-bar-close')
    setTimeout ->
      if not noti.on_close
        notifications.remove noti
    , 5000
    @push noti
}

module.exports = {user, notifications}
