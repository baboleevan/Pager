$ = require 'jquery'
_ = require 'underscore'
async = require 'async'
{observable, observableArray, computed} = require 'knockout'

{throw_error} = require 'commons'

windows = observableArray []
windows.width = observable $(window).width()
$(window).on 'resize', =>
  windows.width $(window).width()
windows.active_index = observable 0
windows.transition = observable yes
previous_window_width = windows.width()
windows.translate = computed ->
  active_index = windows.active_index()
  width = windows.width()
  if width != previous_window_width
    previous_window_width = width
    windows.transition no
    _.defer_ ->
      windows.transition yes
  if active_index >= 1
    active_index * width * -1
  else
    0

windows.add = (window_, callback) ->
  windows.transitionEnd = _.once ->
    delete windows.transitionEnd
    callback()
  windows.push window_
  _.defer_ =>
    # move window position to last inserted
    ws = windows()
    windows.active_index ws.length - 1

windows.remove = (callback) ->
  windows.transitionEnd = _.once ->
    delete windows.transitionEnd
    window_ = windows.pop()
    callback()
  # move window to before last
  windows.active_index windows().length - 2

###
Widnow.show opts, callback
  Window._show opts
    ... now window has main view and do something with it
    Window.close err, callback2
      callback2 err / callback err
###
class Window
  template_prefix: 'template-'
  # total windows single tone
  windows: windows

  constructor: ->
    @template_name = "#{@template_prefix}#{@_template_name}"

  show: (callback) ->
    await @windows.add @, defer()
    callback?()

  close: (callback) ->
    @windows.remove =>
      if @on_close?
        await @on_close defer()
      callback?()

  is_show: ->
    _.last(windows()) is @

module.exports = {Window}