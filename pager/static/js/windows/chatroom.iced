{observable, observableArray, computed} = require 'knockout'

config = require 'config'
require 'one-color-ext' # install one-color extention for knockout
{profile_image_src} = require 'sns/facebook'
{log} = require 'logger'
{tic} = require 'commons'
{socket} = require 'socket'
{notifications} = require 'models'
{Window} = require './window'
{Invitefriends} = require './invitefriends' 
{Room} = require './room'

class RoomVM
  constructor: ({@id, @created, @updated, @creator, users, message}, @socket) ->
    @users = observable(
      for user in users
        user.profile_image = profile_image_src user.facebook_account.uid, 'square'
        user
    )
    @message = observable null
    @change_message message
    
  change_message: (message) =>
    message ?= {
      message: config.default_message, created: @created
      color: 0xffffff, user: @creator
    }
    message.color = config.message_colors.darken[message.color] ? message.color
    message.created_from_now = computed =>
      # inject timer
      tic(60*1000)()
      moment(message.created).fromNow()
    @message message

  open_room_panel: (room, event) ->
    $e = $(event.currentTarget)
    if event.displacement > 0
      $e.addClass 'open-pannel'
    else
      $e.removeClass 'open-pannel'


class Chatroom extends Window
  _template_name: 'chatroom'

  constructor: ->
    super
    @connected = observable no
    @rooms = observableArray null
    @rooms.scrollTo = observable 0
    @loading_rooms = observable no
    @_event_handler_ids = []

  show: (callback) ->
    super()
    @_on_connect = computed =>
      accessible = socket.accessible()
      if accessible
        @loading_rooms yes
        await socket.emit 'list chat rooms', defer err, rooms
        @loading_rooms no
        throw err if err
        @rooms (new RoomVM room for room in rooms)
        callback null
    @_event_handler_ids.push socket.on 'new note', @_on_new_note

  close: (next) ->
    # release soketio
    @_on_connect.dispose()
    for id in @_event_handler_ids
      socket.removeListener id
    super

  _on_new_note: (note) =>
      if @room_window and note.chat_room_id is @room_window.room.id
        @room_window.add_note note
        socket.emit 'read notes', [note.id]
      else
        notifications.add_note note
        socket.emit 'notified notes', [note.id]
      @change_room_header_message note


  change_room_header_message: (note) =>
    for room in @rooms()
      if room.id is note.chat_room_id
        room.change_message note
        break

  enter: (room, event) =>
    location.hash = "#/rooms/" + room.id
    return

  show_room: (room_id, callback) ->
    room = _.find @rooms(), (r) -> r.id is room_id
    if not room
      return callback 404
    if @room_window
      if @room_window.id is room_id
        return callback null
      else
        await @room_window.close defer err
        return callback err if err?
    room_window = @room_window = new Room room
    room_window.on_new_note = @change_room_header_message
    room_window.on_close = (callback) =>
      if @room_window is room_window
        delete @room_window
      callback null
    await @room_window.show defer err
    callback err

  leave: (room, event) =>
    @rooms.remove room
    socket.emit 'leave chat room', room.id

  invite_friends: ->
    invitefriends = new Invitefriends
    invitefriends.on_close = (next) =>
      if room = invitefriends.room
        @rooms.push new RoomVM room
        await _.defer_ defer()
        if room
          last_index = @rooms().length - 1
          @rooms.scrollTo Math.max 0, last_index
      next()
    invitefriends.show()

  scroll_to_top: ->
    @rooms.scrollTo 0
    @rooms.scrollTo.valueHasMutated()

module.exports = {Chatroom}