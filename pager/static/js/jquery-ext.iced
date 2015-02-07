$ = require 'jquery'

$.is_jquery = (obj) ->
  obj instanceof $

$.unwrap = (obj) ->
  if $.is_jquery obj
    obj = obj[0]
  obj

$.fn.scrollFix = ->
  @each ->
    @addEventListener 'touchstart', (event) ->
      startY = event.touches[0].pageY
      startTopScroll = @scrollTop
      if startTopScroll <= 0
        @scrollTop = 1
      if startTopScroll + @offsetHeight >= @scrollHeight
        @scrollTop = @scrollHeight - @offsetHeight - 1
    , false

$.fn.shake = ->
  @each ->
    if $(@).hasClass 'shake'
      return
      
    $(@).one 'webkitAnimationEnd', (event) =>
      if event.currentTarget is @
        $(@).removeClass 'shake'
    $(@).addClass 'shake'

$.fn.hasFocus = ->
  document.activeElement is @[0]

$.isTouchDevice = $.isTouchDeveice = window.Touch?
