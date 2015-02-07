_ = require 'underscore-ext'
{observable, observableArray, computed} = require 'knockout'

config = require 'config'
{tic} = require 'commons'
{log} = require 'logger'
{socket} = require 'socket'
{profile_image_src} = require 'sns/facebook'
{user} = require 'models'
{Window} = require './window'
{Invitefriends} = require './invitefriends'


class NewNote
  constructor: (@on_submit) ->
    @_submiting = observable no
    @color = observable Number 0
    @background_color =  computed =>
      color = @color()
      color and '#' + color.toString(16) or 'none'
    @message = observable null
    @_set_default()

  submit: (note, event) =>
    submiting = @_submiting()
    if submiting
      return
    @_submiting yes

    message = @message()
    color = @color()
    if message.length < 1 or message.length > 280
      if message.length > 280
        _.defer_ -> alert '최대 280자 까지 입력하실 수 있습니다.'
      $(event.currentTarget).shake()
      @_submiting no
      return

    # TODO block submit until response recived
    await @on_submit message, color, defer err, callback
    throw err if err
    callback()
    @_set_default()
    @_submiting no

  _set_default: ->
    @message ''
    @color _.choice(config.message_colors)[1]


class Note
  constructor: ({@id, @color, @message, @user, @created}, force_transition=no) ->
    @me = user.id() is @user.id
    @force_transition = force_transition
    @created_from_now = computed =>
      # inject depenecy to timer
      tic(60*1000)()
      moment(@created).fromNow()
    @user.profile_image ?= profile_image_src @user.facebook_account.uid, 'square'

class Room extends Window
  _template_name: 'room'
  # APIS ['on_new_note', 'on_close']

  constructor: (@room)  ->
    super
    @new_note = new NewNote @_on_submit
    @notes = observableArray []
    @scroll = observable null
    @_users = observable null
    @users = computed =>
      users = @_users() ? []
      # TODO invite more friends
      #users = users.concat (null for i in [0...5-users.length])
      users

  add_note: (note) ->
    @notes.unshift new Note note, yes
    # move to top after html updated
    await _.defer_ defer()

  show_new_note_form: =>
    @new_note new NewNote config.message_colors, @_on_submit

  hide_new_note_form: =>
    @new_note null

  invite: (user, event) =>
    if user
      $(event.currentTarget).shake()
    else
      invitefriends = new Invitefriends
      invitefriends.show @users(), ->

  scrollTop: =>
    @scroll {index: 0, duration: 300}


  show: (callback) ->
    await super defer()
    @_users @room.users()
    await socket.emit 'list notes', @room.id, defer err, notes
    ids = 
      for note in notes
        @notes.push new Note note
        note.id
    socket.emit 'read notes', ids
    callback null

  back: ->
    location.href = '#/rooms/'

  _on_submit: (message, color, callback) =>
    await socket.emit(
      'new note', {id: @room.id, message: message, color: color},
      defer err, note
    )
    if err
      return callback err
    await callback null, defer()
    @add_note note
    @on_new_note note


module.exports = {Room}