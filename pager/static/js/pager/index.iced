# migrations should be called very first time
require('migrations') ->
  _ = require 'underscore'
  require 'jquery.facebook'
  {
    observable, observableArray, applyBindings, bindingHandlers, computed
  } = require 'knockout'
  async = require 'async'
  Path = require 'path'
  Raven = require 'raven'

  require 'vevent'
  require 'knockout-ext'
  {throw_error, reversed} = require 'commons'
  config = require 'config'
  {socket} = require 'socket'
  {log, error} = require 'logger' 
  {
    Intro, Login, Signup, Lounge, Invitefriends, Chatroom, Room, Notification,
    Setting, Window
  } = require 'windows'
  {user, notifications} = require 'models'

  # install raven error collector
  Raven.config(config.raven).install()
  error_counter = observable 0
  error_counter.inc = ->
    error_counter error_counter() + 1
  window.onerror = (message, location, line_no) ->
    Raven.captureException new Error "#{message}, #{location}, line #{line_no}"
    error_counter.inc()

  socket.on 'error', (reason) ->
    Raven.captureException(reason)
    error_counter.inc()

  bindingHandlers.transitionEnd = 
    init: (element, valueAccessor) ->
      value = valueAccessor()
      $(element).on 'webkitTransitionEnd', (e) ->
        if e.currentTarget is element
          value.transitionEnd?()


  route = (path, controller) ->
    Path.map(path).enter([
      ->
        if location.hash isnt '#/login'
          user.previous_location location.hash
          if not user.connected()
            location.hash = '#/login'
            false
    ]).to controller


  class Pager extends Window
    constructor: ->
      super
      @windows.push new Intro
      @initialized = observable no
      @error = error_counter
      @show_add_to_home_screen = \
        observable (config.installable and not config.installed) and config.platform or null
      @notifications = notifications

    show_rooms: (callback=->) ->
      windows = @windows()
      w = _.find windows, (w) -> w instanceof Chatroom
      if not w
        w = new Chatroom()
        await w.show defer err
        if err
          return callback err
      if not w.is_show()
        await @_pop_to w, defer err
        if err
          return callback err
      callback null, w

    show_room: (room_id) ->
      await @show_rooms defer err, chat_room
      if err
        throw err
      await chat_room.show_room room_id, defer err
      if err
        switch
          when 404 
            alert "채팅방을 찾을 수 없습니다."
        location.hash = '#/rooms/'

    show_invite_friends: ->
      windows = @windows()
      w = _.find windows, (w) -> w instanceof Invitefriends
      if not w
        await @show_rooms defer err, chat_room
        throw err if err
        chat_room.invite_friends()
      else if not w.is_show()
        await @_pop_to w, defer err
        throw err if err

    show_login: ->
      w = _.find @windows(), (w) -> w instanceof Login
      if not w
        w = new Login
        w.show()
      if not w.is_show()
        await @_pop_to w, defer err

    _user_connection: (connected) =>
      if connected
        location.hash = user.previous_location()
      else
        location.hash = '#/login'

    _pop_to: (window_, callback) ->
      windows = @windows()
      for w in reversed windows
        if w is window_
          return callback()
        await w.close defer err
        if err
          return callback err

    _pop_to_intro: (callback) ->
      async.whilst(
        =>
          @windows().length > 1

        (next) =>
          @windows.remove next

        callback
      )

    logout: ->
      if user.type() is 'facebook'
        FB.logout()
      else
        user.disconnect()

    initialize: =>
      @socket ?= socket
      _window = $.deparam.querystring()._window
      if _window?
        class_ =
          switch _window
            when 'login' then Login
            when 'signup' then Signup
            when 'invitefriends' then Invitefriends
            when 'chatroom' then Chatroom
            when 'room' then Room
            when 'notification' then Notification
            when 'setting' then Setting
            else
              throw "wrong _window name - #{_window}"
        new class_().show null, throw_error
        return

      $.facebook config.facebook_id, {
        locale: 'ko_KR', events: {
          'auth.login': user.connect_facebook
          'auth.logout': user.disconnect
        }
      }, (response) =>
        @_user_connection user.connected()
        user.connected.subscribe @_user_connection
        user.connect_facebook response
        
      @initialized yes
      Path.root user.previous_location()
      Path.listen()

  pager = new Pager

  route '#/rooms/', ->
    pager.show_rooms()

  route '#/rooms/:note_id', ->
    note_id = parseInt @params.note_id
    if _.isNaN note_id
      return location.hash '#/rooms/'
    pager.show_room note_id

  route '#/invite_friends', ->
    pager.show_invite_friends()

  route '#/login', ->
    pager.show_login()

  init = _.once ({facebook_id})->
    if config.prevent_user_selection
      $('body').addClass 'prevent-user-select'

    config.facebook_id = facebook_id
    $ -> _.defer_ =>
      applyBindings pager
      window.scrollTo 0,0
      _.defer_ ->
        if socket.accessible()
          pager.initialize()
        else
          after_socket_connected = socket.connected.subscribe (connected) ->
            if connected
              after_socket_connected.dispose()
              pager.initialize()

  module.exports = {init}
